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

"""Module for OnProcessIO class."""

from typing import Callable
from typing import List
from typing import Optional
from typing import Text
from typing import Tuple

from ..actions import ExecuteProcess
from ..event import Event
from ..event_handler import EventHandler
from ..events.process import ProcessIO
from ..launch_description_entity import LaunchDescriptionEntity
from ..some_actions_type import SomeActionsType


class OnProcessIO(EventHandler):
    """Convenience class for handling I/O from processes via events."""

    # TODO(wjwwood): make the __init__ more flexible like OnProcessExit, so
    # that it can take SomeActionsType directly or a callable that returns it.
    def __init__(
        self,
        *,
        target_action: ExecuteProcess,
        on_stdin: Callable[[Text], Optional[SomeActionsType]] = None,
        on_stdout: Callable[[Text], Optional[SomeActionsType]] = None,
        on_stderr: Callable[[Text], Optional[SomeActionsType]] = None,
    ):
        """Constructor."""
        if not isinstance(target_action, ExecuteProcess):
            raise RuntimeError("OnProcessIO requires an 'ExecuteProcess' action as the target")
        super().__init__(
            matcher=self._matcher,
            handler=None,  # noop
        )
        self.__target_action = target_action
        self.__on_stdin = on_stdin
        self.__on_stdout = on_stdout
        self.__on_stderr = on_stderr

    def _matcher(self, event: Event) -> bool:
        if not hasattr(event, '__class__'):
            raise RuntimeError("event '{}' unexpectedly not a class".format(event))
        return issubclass(event.__class__, ProcessIO) and event.action == self.__target_action

    def __call__(self, event: ProcessIO, context: 'LaunchContext') -> Optional[SomeActionsType]:
        """Handle the given event."""
        if event.from_stdout and self.__on_stdout is not None:
            return self.__on_stdout(event.text)
        elif event.from_stderr and self.__on_stderr is not None:
            return self.__on_stderr(event.text)
        elif event.from_stdin and self.__on_stdin is not None:
            return self.__on_stdin(event.text)
        else:
            raise RuntimeError("Unexpected ProcessIO event where all 'from_*' are False.")

    def describe(self) -> Tuple[Text, List[LaunchDescriptionEntity]]:
        """Return the description list with 0 being a string, and then LaunchDescriptionEntity's."""
        handlers = '{'
        if self.__on_stdin is not None:
            handlers += "on_stdin: '{}'".format(self.__on_stdin)
        if self.__on_stdout is not None:
            handlers += "on_stdout: '{}'".format(self.__on_stdout)
        if self.__on_stderr is not None:
            handlers += "on_stderr: '{}'".format(self.__on_stderr)
        handlers += '}'
        return [
            "OnProcessIO(matcher='{}', handlers={})".format(self.matcher_description, handlers),
            [],
        ]

    @property
    def matcher_description(self):
        """Return the string description of the matcher."""
        return 'event issubclass of ProcessIO and event.action == ExecuteProcess({})'.format(
            hex(id(self.__target_action))
        )
