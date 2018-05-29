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

"""Tests for normal usage of `launch`."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # noqa

import launch.actions
import launch.events
import launch.substitutions
from launch import LaunchDescription
from launch import LaunchIntrospector
from launch import LaunchService


def test_normal_case():
    """Test the normal use case for a launch description."""
    ld = LaunchDescription([
        launch.actions.LogInfo(msg='Hello World!'),
        launch.actions.LogInfo(msg=(
            'Is that you, ', launch.substitutions.EnvironmentVariable(name='USER'), '?'
        )),
    ])
    whoami_action = launch.actions.ExecuteProcess(
        cmd=[launch.substitutions.FindExecutable(name='whoami')],
    )
    ld.add_action(whoami_action)
    # TODO(wjwwood): consider putting this as a convenience function of actions.ExecuteProcess
    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnProcessIO(
        target_action=whoami_action,
        on_stdout=lambda text: launch.actions.LogInfo(
            msg="whoami says you are '{}'.".format(text.decode().strip())
        ),
    )))
    # TODO(wjwwood): consider putting this as a convenience function of actions.ExecuteProcess
    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnProcessExit(
        target_action=whoami_action,
        on_exit=lambda event, context: LaunchDescription([
            launch.actions.EmitEvent(event=launch.events.Shutdown()),
            launch.actions.LogInfo(
                msg="'{}' exited with '{}'".format(event.cmd[0], event.returncode)
            ),
        ]),
    )))
    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnShutdown(
        on_shutdown=lambda event: print('Launch was asked to shutdown!'),
    )))

    print('Starting introspection of launch description...')
    print('')

    print(LaunchIntrospector().format_launch_description(ld))

    print('')
    print('Starting launch of launch description...')
    print('')

    # ls = LaunchService(debug=True)
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
    # next steps:
    # - make execute process action

    # questions:
    # - should sync version of emit event call all handlers before returning?


if __name__ == '__main__':
    test_normal_case()
