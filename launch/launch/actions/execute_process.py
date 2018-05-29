# Copyright 2018 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module for the ExecuteProcess action."""

import logging
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Text

from osrf_pycommon.process_utils import AsyncSubprocessProtocol
from osrf_pycommon.process_utils import async_execute_process

from ..action import Action
from ..event_handler import EventHandler
from ..events.process import ProcessExited
from ..events.process import ProcessStarted
from ..events.process import ProcessStderr
from ..events.process import ProcessStdin
from ..events.process import ProcessStdout
from ..events.process import ShutdownProcess
from ..events.process import SignalProcess
from ..launch_context import LaunchContext
from ..launch_description import LaunchDescription
from ..some_substitutions_type import SomeSubstitutionsType
from ..utilities import normalize_to_list_of_substitutions

_logger = logging.getLogger(name='launch')


class ExecuteProcess(Action):
    """Action that begins executing a process and sets up event handlers for the process."""

    def __init__(
        self, *,
        cmd: Iterable[SomeSubstitutionsType],
        cwd: Optional[SomeSubstitutionsType] = None,
        env: Optional[Dict[SomeSubstitutionsType, SomeSubstitutionsType]] = None,
        shell: bool = False,
    ):
        """
        Construct an ExecuteProcess action.

        Many arguments are passed eventually to :class:`subprocess.Popen`, so
        see the documentation for the class for additional details.

        This action, once executed, registers several event handlers for
        various process related events and will also emit events asynchronously
        when certain events related to the process occur.

        Handled events include:

        - launch.events.process.ShutdownProcess:

          - begins standard shutdown procedure for a running executable

        - launch.events.process.SignalProcess:

          - passes the signal provided by the event to the running process

        - launch.events.process.ProcessStdin:

          - passes the text provided by the event to the stdin of the process

        Emitted events include:

        - launch.events.process.ProcessStarted:

            - emitted when the process starts

        - launch.events.process.ProcessExited:

            - emitted when the process exits
            - event contains return code

        - launch.events.process.ProcessStdout and launch.events.process.ProcessStderr:

            - emitted when the process produces data on either the stdout or stderr pipes
            - event contains the data from the pipe

        :param: cmd a list where the first item is the executable and the rest
            are arguments to the executable, each item maybe be a string or a
            list of strings and Substitutions to be resolved at runtime
        :param: cwd the directory in which to run the executable
        :param: env dictionary of environment variables to be used
        :param: shell if True, a shell is used to execute the cmd
        """
        super().__init__()
        self.__cmd = normalize_to_list_of_substitutions(cmd)
        self.__cwd = cwd if cwd is None else normalize_to_list_of_substitutions(cwd)
        self.__env = None
        if env is not None:
            self.__env = {}
            for key, value in env.items():
                self.__env[normalize_to_list_of_substitutions(key)] = \
                    normalize_to_list_of_substitutions(value)
        self.__shell = shell
        self.__asyncio_task = None
        self._final_cmd = None
        self._final_cwd = None
        self._final_env = None

    def __on_shutdown_process_event(
        self,
        event: ShutdownProcess,
        context: LaunchContext
    ) -> Optional[LaunchDescription]:
        _logger.debug("in ExecuteProcess('{}').__on_shutdown_process_event()".format(id(self)))

    def __on_signal_process_event(
        self,
        event: SignalProcess,
        context: LaunchContext
    ) -> Optional[LaunchDescription]:
        _logger.debug("in ExecuteProcess('{}').__on_signal_process_event()".format(id(self)))

    def __on_process_stdin_event(
        self,
        event: ProcessStdin,
        context: LaunchContext
    ) -> Optional[LaunchDescription]:
        _logger.debug("in ExecuteProcess('{}').__on_process_stdin_event()".format(id(self)))

    class __ProcessProtocol(AsyncSubprocessProtocol):
        def __init__(self, action: 'ExecuteProcess', context: LaunchContext, **kwargs):
            super().__init__(**kwargs)
            self.__context = context
            self.__action = action

        def on_stdout_received(self, data: Text) -> None:
            self.__context.emit_event_sync(ProcessStdout(
                action=self.__action,
                cmd=self.__action._final_cmd,
                cwd=self.__action._final_cwd,
                env=self.__action._final_env,
                text=data
            ))

        def on_stderr_received(self, data: Text) -> None:
            self.__context.emit_event_sync(ProcessStderr(
                action=self.__action,
                cmd=self.__action._final_cmd,
                cwd=self.__action._final_cwd,
                env=self.__action._final_env,
                text=data
            ))

    async def __execute_process(self, context: LaunchContext) -> None:
        _logger.debug("in ExecuteProcess('{}').__execute_process()".format(id(self)))

        def __create_protocol(**kwargs) -> AsyncSubprocessProtocol:
            return self.__ProcessProtocol(self, context, **kwargs)

        self._final_cmd = [context.perform_substitution(x) for x in self.__cmd]
        self._final_cwd = None
        if self.__cwd is not None:
            self._final_cwd = ''.join([context.perform_substitution(x) for x in self.__cwd])
        self._final_env = None
        if self.__env is not None:
            self._final_env = {}
            for key, value in self.__env.items():
                self._final_env[''.join([context.perform_substitution(x) for x in key])] = \
                    ''.join([context.perform_substitution(x) for x in value])

        _logger.debug(
            "in ExecuteProcess('{}').__execute_process(): '{}'".format(id(self), self._final_cmd)
        )
        transport, protocol = await async_execute_process(
            __create_protocol,
            cmd=self._final_cmd,
            cwd=self._final_cwd,
            env=self._final_env,
            shell=self.__shell,
            emulate_tty=False,
            stderr_to_stdout=False,
        )

        await context.emit_event(ProcessStarted(
            action=self, cmd=self._final_cmd, cwd=self._final_cwd, env=self._final_env,
        ))

        returncode = await protocol.complete
        await context.emit_event(ProcessExited(
            action=self,
            cmd=self._final_cmd, cwd=self._final_cwd, env=self._final_env,
            returncode=returncode
        ))

    def execute(self, context: LaunchContext) -> Optional[List['Action']]:
        """
        Execute the action.

        This does the following:
        - register an event handler for the shutdown process event
        - register an event handler for the signal process event
        - register an event handler for the stdin event
        - create a task for the coroutine that monitors the process
        """
        from ..event_handlers import event_named
        context.register_event_handler(EventHandler(
            matcher=event_named('launch.events.ShutdownProcess'),
            handler=self.__on_shutdown_process_event
        ))
        context.register_event_handler(EventHandler(
            matcher=event_named('launch.events.SignalProcess'),
            handler=self.__on_signal_process_event
        ))
        context.register_event_handler(EventHandler(
            matcher=event_named('launch.events.ProcessStdin'),
            handler=self.__on_process_stdin_event
        ))
        self.__asyncio_task = context.asyncio_loop.create_task(self.__execute_process(context))

    @property
    def cmd(self):
        """Getter for cmd."""
        return self.__cmd

    @property
    def cwd(self):
        """Getter for cwd."""
        return self.__cwd

    @property
    def env(self):
        """Getter for env."""
        return self.__env

    @property
    def shell(self):
        """Getter for shell."""
        return self.__shell
