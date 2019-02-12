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

from collections import OrderedDict

from launch.actions import EmitEvent
from launch.actions import ExecuteProcess
from launch.actions import RegisterEventHandler
from launch.actions import UnregisterEventHandler
from launch.event_handlers import OnExecutionComplete
from launch.event_handlers import OnProcessExit
from launch.event_handlers import OnProcessIO
from launch.events import Shutdown


class LaunchTestService():

    def __init__(self):
        self.__tests = OrderedDict()
        self.__processes_rc = OrderedDict()

    def _arm(
        self,
        test_name
    ):
        """Prepare for test execution."""
        assert test_name not in self.__tests
        self.__tests[test_name] = 'armed'

    def _fail(
        self,
        test_name,
        reason
    ):
        """Mark test as a failure and shutdown, dropping the tests that are still ongoing."""
        self.__tests[test_name] = 'failed'
        for test_name in self.__tests:
            if self.__tests[test_name] == 'armed':
                self.__tests[test_name] = 'dropped'
        return [EmitEvent(event=Shutdown(reason=reason))]

    def _succeed(
        self,
        test_name,
        side_effect=None
    ):
        """Mark test as a success and shutdown if all other tests have succeeded too."""
        self.__tests[test_name] = 'succeeded'
        if all(status == 'succeeded' for status in self.__tests.values()):
            return [EmitEvent(event=Shutdown(reason='all tests finished'))]
        if side_effect == 'shutdown':
            return [EmitEvent(event=Shutdown(reason='shutdown after test'))]
        return []

    def add_fixture_action(
        self,
        launch_description,
        action,
        exit_allowed=[0],
    ):
        """
        Add action used as testing fixture.

        If a process action and it exits, a shutdown event is emitted.
        """
        launch_description.add_action(action)
        if isinstance(action, ExecuteProcess):
            def on_fixture_process_exit(event, context):
                process_name = event.action.process_details['name']
                allowed_to_exit = exit_allowed
                if isinstance(exit_allowed, list):
                    allowed_to_exit = event.returncode in exit_allowed
                if not context.is_shutdown and not allowed_to_exit:
                    rc = event.returncode if event.returncode else 1
                    self.__processes_rc[process_name] = rc
                    return EmitEvent(event=Shutdown(
                        reason='{} fixture process died!'.format(process_name)
                    ))
            launch_description.add_action(
                RegisterEventHandler(OnProcessExit(
                    target_action=action, on_exit=on_fixture_process_exit
                ))
            )
        return action

    def add_test_action(
        self,
        launch_description,
        action
    ):
        """
        Add action used for testing.

        If either all test actions have completed or a process action has
        exited with a non-zero return code, a shutdown event is emitted.
        """
        test_name = 'test_{}'.format(id(action))
        if isinstance(action, ExecuteProcess):
            def on_test_process_exit(event, context):
                if event.returncode != 0:
                    process_name = event.action.process_details['name']
                    self._processes_rc[process_name] = event.returncode
                    return self._fail(
                        test_name, reason='{} test failed!'.format(
                            process_name
                        )
                    )
                return self._succeed(test_name)

            launch_description.add_action(
                RegisterEventHandler(OnProcessExit(
                    target_action=action, on_exit=on_test_process_exit
                ))
            )
        else:
            launch_description.add_action(
                RegisterEventHandler(OnExecutionComplete(
                    target_action=action, on_completion=(
                        lambda *args: self._succeed(test_name)
                    )
                ))
            )
        launch_description.add_action(action)
        self._arm(test_name)
        return action

    def add_output_test(
        self,
        launch_description,
        action,
        output_test,
        test_suffix='output',
        output_filter=None,
        side_effect=None,
    ):
        """
        Test an action process' output against a given test.

        :param launch_description: test launch description that owns the given action.
        :param action: launch action to test whose output is to be tested.
        :param output_test: test tuple as returned by launch_testing.output.create_* functions.
        :param test_suffix: an optional test suffix to disambiguate multiple test instances,
        defaults to 'output'.
        :param output_filter: an optional function to filter out i.e. ignore output lines for
        the test.
        :param side_effect: an optional side effect of a passing test, currently only 'shutdown'
        is supported.
        """
        assert isinstance(action, ExecuteProcess)
        test_name = 'test_{}_{}'.format(id(action), test_suffix)
        output, collate_output, match_output, match_patterns = output_test
        if not output_filter:
            output_filter = (lambda x: x)
        assert any(match_patterns)

        def on_process_exit(event, context):
            nonlocal match_patterns
            if any(match_patterns):
                process_name = event.action.process_details['name']
                reason = 'not all {} output matched!'.format(process_name)
                return [
                    UnregisterEventHandler(on_output),
                    UnregisterEventHandler(on_exit),
                    *self._fail(test_name, reason)
                ]

        on_exit = OnProcessExit(
            target_action=action, on_exit=on_process_exit
        )

        launch_description.add_action(
            RegisterEventHandler(on_exit)
        )

        def on_process_stdout(event):
            nonlocal output
            nonlocal match_patterns
            output = collate_output(output, output_filter(event.text))
            match_patterns = [
                pattern for pattern in match_patterns
                if not match_output(output, pattern)
            ]
            if not any(match_patterns):
                return [
                    UnregisterEventHandler(on_output),
                    UnregisterEventHandler(on_exit),
                    *self._succeed(test_name, side_effect)
                ]

        on_output = OnProcessIO(
            target_action=action, on_stdout=on_process_stdout
        )
        launch_description.add_action(
            RegisterEventHandler(on_output)
        )
        self._arm(test_name)

        return action

    def run(
        self,
        launch_service,
        *args,
        **kwargs
    ):
        """
        Invoke the `run` method of the launch service.

        :returns: If the return value of the parent method is zero but any of
          the test processes exited with a non-zero return code the return of
          the first failed test process is returned.
        """
        rc = launch_service.run(*args, **kwargs)
        if rc == 0:
            default_rc = 1 if 'failed' in self.__tests.values() else 0
            rc = next((rc for rc in self.__processes_rc.values() if rc != 0), default_rc)
        return rc
