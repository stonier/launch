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

"""Module for the LaunchService class."""

import asyncio
import logging
import threading
from typing import Optional

import osrf_pycommon.process_utils

from .event_handler import EventHandler
from .event_handlers import event_named
from .events import IncludeLaunchDescription
from .events import Shutdown
from .launch_context import LaunchContext
from .launch_description import LaunchDescription

_logger = logging.getLogger(name='launch')


class LaunchService:
    """Service that manages the event loop and runtime for launched system."""

    def __init__(self, *, debug=False):
        """Constructor."""
        self.__debug = debug
        if self.__debug:
            logging.basicConfig(level=logging.DEBUG)
        self.__launch_descriptions = []
        self.__context = LaunchContext()
        self.__context.register_event_handler(EventHandler(
            matcher=event_named('launch.events.IncludeLaunchDescription'),
            handler=self.__on_include_launch_description_event,
        ))
        self.__context.register_event_handler(EventHandler(
            matcher=event_named('launch.events.Shutdown'),
            handler=self.__on_shutdown_event,
        ))
        # Used to prevent run() being called from multiple threads.
        self.__running_lock = threading.Lock()
        self.__running = False
        # Used to allow asynchronous use of self.__loop_from_run_thread without
        # it being set to None by run() as it exits.
        self.__loop_from_run_thread_lock = threading.Lock()
        self.__loop_from_run_thread = None

    def include_launch_description(self, launch_description: LaunchDescription) -> None:
        """Evaluate a given LaunchDescription and visits all of its entities."""
        self.__context.emit_event_sync(IncludeLaunchDescription(launch_description))

    def __on_include_launch_description_event(
        self,
        event: IncludeLaunchDescription,
        context: LaunchContext
    ) -> Optional[LaunchDescription]:
        event.launch_description.visit(context)

    def __on_shutdown_event(
        self,
        event: Shutdown,
        context: LaunchContext
    ) -> Optional[LaunchDescription]:
        _logger.info('Shutting down...')
        with self.__running_lock:
            self.__running = False
        # TODO(wjwwood): should actually shutdown running actions some how

    def shutdown(self) -> None:
        """
        Shutdown all running actions and then stop the asyncio run loop.

        Does nothing if LaunchService.run() is not running in another thread.
        """
        with self.__loop_from_run_thread_lock:
            if self.__loop_from_run_thread is not None:
                self.__loop_from_run_thread.stop()

    async def __run_loop(self) -> None:
        _logger.debug('in __run_loop')
        running = False
        with self.__running_lock:
            running = self.__running
        while running:
            await self.__context._process_one_event()
            with self.__running_lock:
                running = self.__running

    def __create_future(self):
        if hasattr(self.__loop_from_run_thread_lock, 'create_future'):
            # This was added in Python 3.5.2 and has some benefit if available.
            return self.__loop_from_run_thread_lock.create_future()
        else:
            return asyncio.Future()

    def run(self) -> None:
        """
        Start the event loop and visit all entities of all included LaunchDescriptions.

        This should only ever be run from a single thread.
        """
        with self.__running_lock:
            if self.__running:
                raise RuntimeError('LaunchService.run() called from multiple threads concurrently.')
            self.__running = True
        with self.__loop_from_run_thread_lock:
            self.__loop_from_run_thread = osrf_pycommon.process_utils.get_loop()
            if self.__debug:
                self.__loop_from_run_thread.set_debug(True)
            self.__context._set_asyncio_loop(self.__loop_from_run_thread)

        # canceled_future = self.__create_future()
        run_loop_task = self.__loop_from_run_thread.create_task(self.__run_loop())
        while not run_loop_task.done():
            try:
                self.__loop_from_run_thread.run_until_complete(run_loop_task)
            except KeyboardInterrupt:
                # run_loop_task.cancel()
                raise

        with self.__loop_from_run_thread_lock:
            self.__loop_from_run_thread = None
            self.__context._set_asyncio_loop(None)
        with self.__running_lock:
            self.__running = False
