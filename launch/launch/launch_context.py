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

"""Module for LaunchContext class."""

import asyncio
import collections
import logging
from typing import Text

from .event import Event
from .event_handler import EventHandler
from .launch_description_entity import LaunchDescriptionEntity
from .substitution import Substitution

_logger = logging.getLogger(name='launch')


class LaunchContext:
    """Runtime context used by various launch entities when being visited or executed."""

    def __init__(self):
        """Constructor."""
        self.__event_queue = asyncio.Queue()
        self.__event_handlers = collections.deque()
        self.__async_event_handlers = collections.deque()
        self.__asyncio_loop = None

    def _set_asyncio_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.__asyncio_loop = loop

    @property
    def asyncio_loop(self):
        """Getter for asyncio_loop."""
        return self.__asyncio_loop

    async def _process_one_event(self) -> None:
        _logger.debug('in _process_one_event()')
        next_event = await self.__event_queue.get()
        _logger.debug("in _process_one_event() -> got event '{}'".format(next_event))
        await self.__process_event(next_event)

    async def __process_event(self, event: Event) -> None:
        _logger.debug("processing event: '{}'".format(event.name))
        for event_handler in tuple(self.__event_handlers):
            if event_handler.matches(event):
                _logger.debug(
                    "processing event: '{}' ✓ '{}'".format(event.name, event_handler))
                launch_description = event_handler(event, self)
                if launch_description is not None:
                    from .utilities import is_a_subclass
                    if not is_a_subclass(launch_description, LaunchDescriptionEntity):
                        raise RuntimeError(
                            "expected a LaunchDescriptionEntity from event_handler, got '{}'"
                            .format(launch_description)
                        )
                    launch_description.visit(self)
            else:
                _logger.debug(
                    "processing event: '{}' x '{}'".format(event.name, event_handler))

    def register_event_handler(self, event_handler: EventHandler) -> None:
        """Register a synchronous event handler."""
        self.__event_handlers.appendleft(event_handler)

    def register_async_event_handler(self, event_handler: EventHandler) -> None:
        """Register a synchronous event handler."""
        self.__async_event_handlers.appendleft(event_handler)

    def emit_event_sync(self, event: Event) -> None:
        """Emit an event synchronously."""
        _logger.debug("emitting event synchronously: '{}'".format(event.name))
        self.__event_queue.put_nowait(event)

    async def emit_event(self, event: Event) -> None:
        """Emit an event."""
        _logger.debug("emitting event: '{}'".format(event.name))
        await self.__event_queue.put(event)

    def perform_substitution(self, substitution: Substitution) -> Text:
        """Perform substitution on given Substitution."""
        return substitution.perform(self)
