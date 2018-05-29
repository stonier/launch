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

"""Module for ProcessExited event."""

from typing import Dict
from typing import List
from typing import Optional
from typing import Text

from .process_event import ProcessEvent


class ProcessExited(ProcessEvent):
    """Event emitted when a process exits."""

    name = 'launch.events.process.ProcessExited'

    def __init__(
        self,
        *,
        action: 'launch.actions.ExecuteProcess',
        cmd: List[Text],
        cwd: Optional[Text],
        env: Optional[Dict[Text, Text]],
        returncode: int,
    ):
        """
        Constructor.

        :param: action is the ExecuteProcess action associated with the event
        :param: cmd is the final command after substitution expansion
        :param: cwd is the final working directory after substitution expansion
        :param: env is the final environment variables after substitution expansion
        :param: returncode is the returncode of the process
        """
        super().__init__(action=action, cmd=cmd, cwd=cwd, env=env)
        self.__returncode = returncode

    @property
    def returncode(self) -> int:
        """Getter for returncode."""
        return self.__returncode
