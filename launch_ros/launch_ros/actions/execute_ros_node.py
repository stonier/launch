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

"""Module for the ExecuteROSNode action."""

import logging
from typing import Iterable
from typing import List
from typing import Optional

from launch.action import Action
from launch.actions import ExecuteProcess
from launch.launch_context import LaunchContext
from launch.some_substitutions_type import SomeSubstitutionsType

from launch_ros.substitutions import ExecutableInPackage

_logger = logging.getLogger(name='launch_ros')


class ExecuteROSNode(ExecuteProcess):
    """Action that begins executing a process and sets up event handlers for the process."""

    def __init__(
        self, *,
        package: SomeSubstitutionsType,
        node_executable: SomeSubstitutionsType,
        arguments: Optional[Iterable[SomeSubstitutionsType]] = None,
        **kwargs,
    ) -> None:
        """
        Construct an ExecuteROSNode action.

        Many arguments are passed eventually to
        :class:`launch.actions.ExecuteProcess`, so see the documentation of
        that class for additional details.
        However, the `cmd` is not meant to be used, instead use the
        `node_executable` and `arguments` keyword arguments to this function.

        This action, once executed, delegates most work to the
        :class:`launch.actions.ExecuteProcess`, but it also converts some ROS
        specific arguments into generic command line arguments.

        The launch_ros.substitutions.ExecutableInPackage substitution is used
        to find the executable at runtime, so this Action also raise the
        exceptions that substituion can raise when the package or executable
        are not found.

        :param: package the package in which the node executable can be found
        :param: node_executable the name of the executable to find
        :param: arguments list of extra arguments for the node
        """
        cmd = [ExecutableInPackage(package=package, executable=node_executable)]
        cmd += [] if arguments is None else arguments
        super().__init__(cmd=cmd, **kwargs)
        self.__package = package
        self.__node_executable = node_executable
        self.__arguments = arguments

    def execute(self, context: LaunchContext) -> Optional[List[Action]]:
        """
        Execute the action.

        Delegated to :meth:`launch.actions.ExecuteProcess.execute`.
        """
        return super().execute(context)
