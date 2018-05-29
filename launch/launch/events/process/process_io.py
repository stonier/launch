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

"""Module for ProcessIO event."""

from typing import Dict
from typing import List
from typing import Optional
from typing import Text

from .process_event import ProcessEvent


class ProcessIO(ProcessEvent):
    """Event emitted when a process generates output on stdout or stderr, or if stdin is used."""

    name = 'launch.events.process.ProcessIO'

    def __init__(
        self,
        *,
        action: 'launch.actions.ExecuteProcess',
        cmd: List[Text],
        cwd: Optional[Text],
        env: Optional[Dict[Text, Text]],
        text: bytes,
        fd: int,
    ):
        """
        Constructor.

        :param: action is the ExecuteProcess action associated with the event
        :param: cmd is the final command after substitution expansion
        :param: cwd is the final working directory after substitution expansion
        :param: env is the final environment variables after substitution expansion
        :param: text is the unicode data associated with the event
        :param: fd is an integer that indicates which file descriptor the text is from
        """
        super().__init__(action=action, cmd=cmd, cwd=cwd, env=env)
        self.__text = text
        self.__from_stdin = fd == 0
        self.__from_stdout = fd == 1
        self.__from_stderr = fd == 2

    @property
    def text(self) -> bytes:
        """Getter for text."""
        return self.__text

    @property
    def from_stdin(self) -> bool:
        """Getter for from_stdin."""
        return self.__from_stdin

    @property
    def from_stdout(self) -> bool:
        """Getter for from_stdout."""
        return self.__from_stdout

    @property
    def from_stderr(self) -> bool:
        """Getter for from_stderr."""
        return self.__from_stderr
