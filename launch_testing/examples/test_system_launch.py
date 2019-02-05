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
Some example tests for ROS-agnostic launch descriptions.
"""


import sys
import unittest

from datetime import timedelta

from apex_rostest import post_shutdown_test

from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.actions import ExecuteProcess
from launch.event_handlers import OnProcessExit


def generate_test_description(ready_fn) -> LaunchDescription:
    """
    Tests that a post-condition holds for an executable's
    outcome, a compression command in this case.
    """
    ld = LaunchDescription()

    prelist_bags_action = ExecuteProcess(
        cmd='ls *.bag', cwd='/var/log/bags',
        shell=True, output='screen', name='prelist'
    )
    ld.add_action(prelist_bags_action)

    compression_action = ExecuteProcess(
        cmd='bzip2 /var/log/bags/*.bag', shell=True,
        output='screen', prefix='time', name='compressor'
    )
    ld.add_action(RegisterEventHandler(OnProcessExit(
        target_action=prelist_bags_action,
        on_exit=[compression_action]
    )))

    postlist_bags_action = ExecuteProcess(
        cmd='ls *.bag.bz2', cwd='/var/log/bags',
        shell=True, output='screen', name='postlist'
    )

    ld.add_action(RegisterEventHandler(OnProcessExit(
        target_action=compression_action,
        on_exit=[postlist_bags_action]
    )))

    ready_fn()  # ???
    return ld


@post_shutdown_test()
class CompressionTest(unittest.TestCase):

    def test_compression_timing(self):
        def parse_timedelta(string_value):
            match = re.match(
                '(?P<minutes>\d+)m(?P<seconds>\d\.\d{3}s)', string_value
            )
            return timedelta(**{
                name: float(value) if value else 0
                for name, value in match.groupdict()
            })

        compressor_output = self.proc_output['compressor'].text

        real_time = re.search(
            '^real (\d+m\d\.\d{3}s)$', compressor_output, re.M
        )
        self.assertIsNotNone(real_time)
        self.assertLess(
            parse_timedelta(real_time.group(0)),
            timedelta(minutes=1, seconds=30)
        )

        sys_time = re.search(
            '^sys (\d+m\d\.\d{3}s)$', compressor_output, re.M
        )
        self.assertIsNotNone(sys_time)
        self.assertLess(
            parse_timedelta(sys_time.group(0)),
            timedelta(seconds=30)
        )

    def test_compression_completeness(self):
        self.assertEquals(
            len(self.proc_output['prelist'].text.splitlines()),
            len(self.proc_output['postlist'].text.splitlines())
        )
