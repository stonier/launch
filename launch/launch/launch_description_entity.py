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

"""Module for LaunchDescriptionEntity class."""

from typing import List
from typing import Optional


class LaunchDescriptionEntity:
    """Single item in a launch description."""

    # Note: Types that reference themselves in typing annotations have to be
    # expressed as strings until Python 4.0 (?) where annotations will be
    # postponed, see: https://www.python.org/dev/peps/pep-0563/
    # In Python 3.7, there will be `from __future__ import annotations` to
    # use the new behavior earlier.
    def visit(self, context: 'LaunchContext') -> Optional[List['LaunchDescriptionEntity']]:
        """
        Visit the entity.

        This is called for each entity in a launch description when being
        evaluated at runtime.

        Should be overridden by derived class, but by default does nothing.
        """
        pass
