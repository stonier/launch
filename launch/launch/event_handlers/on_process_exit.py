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

"""Module for OnProcessExit class."""

from typing import Callable
from typing import List
from typing import Optional
from typing import Text
from typing import Tuple
from typing import overload

from ..actions import ExecuteProcess
from ..event_handler import EventHandler
from ..events.process import ProcessExited
from ..launch_description_entity import LaunchDescriptionEntity
from ..some_actions_type import SomeActionsType


class OnProcessExit(EventHandler):
    """Convenience class for handling a process exited event."""

    @overload
    def __init__(self, *, target_action: ExecuteProcess, on_exit: SomeActionsType):
        """Overload which takes just actions."""
        ...

    @overload  # noqa: F811
    def __init__(
        self,
        *,
        target_action: ExecuteProcess,
        on_exit: Callable[[int], Optional[SomeActionsType]]
    ):
        """Overload which takes a callable to handle the exit."""
        ...

    def __init__(self, *, target_action, on_exit):  # noqa: F811
        """Constructor."""
        if not isinstance(target_action, ExecuteProcess):
            raise RuntimeError("OnProcessExit requires an 'ExecuteProcess' action as the target")
        super().__init__(
            matcher=(
                lambda event: isinstance(event, ProcessExited) and event.action == target_action
            ),
            handler=None,  # noop
        )
        self.__target_action = target_action
        # TODO(wjwwood) check that it is not only callable, but also a callable that matches
        # the correct signature for a handler in this case
        self.__on_exit = on_exit
        self.__actions_on_exit = []
        if isinstance(on_exit, LaunchDescriptionEntity):
            self.__on_exit = lambda event, context: on_exit
            if isinstance(on_exit, (list, tuple)):
                self.__actions_on_exit = on_exit
            else:
                self.__actions_on_exit = [on_exit]

    def __call__(self, event: ProcessExited, context: 'LaunchContext') -> Optional[SomeActionsType]:
        """Handle the given event."""
        return self.__on_exit(event, context)

    def describe(self) -> Tuple[Text, List[LaunchDescriptionEntity]]:
        """Return the description list with 0 being a string, and then LaunchDescriptionEntity's."""
        return [
            "OnProcessExit(matcher='{}', handler=<actions>)".format(self.matcher_description),
            self.__actions_on_exit,
        ]

    @property
    def matcher_description(self):
        """Return the string description of the matcher."""
        return 'event == ProcessExited and event.action == ExecuteProcess({})'.format(
            hex(id(self.__target_action))
        )
