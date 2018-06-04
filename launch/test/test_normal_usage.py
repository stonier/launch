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
        on_stdout=lambda event: launch.actions.LogInfo(
            msg="whoami says you are '{}'.".format(event.text.decode().strip())
        ),
    )))

    # ld.add_action(launch.actions.SetLaunchConfiguration('launch-prefix', 'time'))

    counter_action = launch.actions.ExecuteProcess(cmd=['python3', '-u', './legacy/counter.py'])
    ld.add_action(counter_action)

    def counter_output_handler(event):
        target_str = 'Counter: 4'
        if target_str in event.text.decode():
            return launch.actions.EmitEvent(event=launch.events.Shutdown(
                reason="saw '{}' from '{}'".format(target_str, event.process_name)
            ))

    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnProcessIO(
        target_action=counter_action,
        on_stdout=counter_output_handler,
        on_stderr=counter_output_handler,
    )))

    def on_output(event):
        for line in event.text.decode().splitlines():
            print('({}) {}'.format(event.process_name, line))
        # return launch.actions.LogInfo(msg='[{}] {}'.format(event.process_name, event.text))

    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnProcessIO(
        on_stdout=on_output,
        on_stderr=on_output,
    )))
    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnProcessExit(
        on_exit=lambda event, context: LaunchDescription([
            launch.actions.LogInfo(
                msg="'{}' exited with '{}'".format(event.process_name, event.returncode)
            ),
        ]),
    )))
    ld.add_action(launch.actions.RegisterEventHandler(launch.event_handlers.OnShutdown(
        on_shutdown=lambda event, context: launch.actions.LogInfo(
            msg='Launch was asked to shutdown: {}'.format(event.reason)
        ),
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
    # - Make use of describe_sub_entities in ExecuteProcess, other actions; also extend to EH's


if __name__ == '__main__':
    test_normal_case()
