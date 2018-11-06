# Copyright 2018 Datawire. All rights reserved.
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
# limitations under the License

from typing import Any, List, Dict

# from ...ir.irratelimit import IRRateLimit


class V1RateLimitAction(dict):
    def __init__(self, rate_limit: Dict[str, Any]) -> None:
        super().__init__({
            'actions': [
                { 'type': 'source_cluster' },
                { 'type': 'destination_cluster' },
                { 'type': 'remote_address' },
            ]
        })

        rate_limit_descriptor = rate_limit.get('descriptor', None)

        if rate_limit_descriptor:
            self['actions'].append({ 'type': 'generic_key',
                                     'descriptor_value': rate_limit_descriptor })

        rate_limit_headers = rate_limit.get('headers', [])

        for rate_limit_header in rate_limit_headers:
            self['actions'].append({ 'type': 'request_headers',
                                     'header_name': rate_limit_header,
                                     'descriptor_key': rate_limit_header})
