# Copyright 2019 Open Source Robotics Foundation, Inc.
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

"""
Some example tests for ROS-aware launch descriptions.
"""

import sys
import unittest

from datetime import timedelta

from apex_rostest import post_shutdown_test

from launch.launch_description_sources import \
    get_launch_description_from_python_launch_file

from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
from launch_testing.actions import PyTest
from launch_testing.actions import GTest


def generate_test_description(ready_fn) -> LaunchDescription:
    """
    A test fixture providing the basic pub/sub launch description.
    """
    # TODO(hidmic): implement functionality to lookup launch files
    # on a per package basis
    launch_path = get_launch_path(
        package_name='launch_ros', launch_file_path='pub_sub_launch.py'
    )
    launch_description = get_launch_description_from_python_launch_file(launch_path)
    # Launches a pytest with a 30s timeout.
    launch_description.add_action(
        PyTest(path='pub_test.py', timeout=30)
    )
    # Launches a gtest with a 30s timeout.
    launch_description.add_action(
        GTest(path='sub_test', timeout=30)
    )
    ready_fn()  # ???
    return launch_description


@post_shutdown_test()
class OutcomeTest(unittest.TestCase):

    def test_return_codes(self):
        for info in self.proc_info:
            self.assertEquals(
                info.returncode,
                0,
                "Non-zero exit code for process {}".format(info.process_name)
            )


def generate_test_description(ready_fn) -> LaunchDescription:
    """
    Tests a basic pub/sub setup for proper output matching.
    """
    ready_fn()  # ???
    return LaunchDescription([
        launch_ros.actions.Node(
            package='demo_nodes_cpp',
            node_executable='talker',
            remappings=[('chatter', 'my_chatter')],
            output='screen'
        ),
        launch_ros.actions.Node(
            package='demo_nodes_py',
            node_executable='listener',
            remappings=[('chatter', 'my_chatter')],
            output='screen'
        )
    ])


@post_shutdown_test()
class PostShutdownPubSubTest(unittest.TestCase):

    def test_error_free_output(self):
        self.assertNotIn('ERROR', self.proc_output['talker'].text)

    def test_message_count(self):
        self.assertGreater(self.proc_output['listener'].text.count('I heard'), 0)
