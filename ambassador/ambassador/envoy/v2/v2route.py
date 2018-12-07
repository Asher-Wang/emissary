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

from typing import List, TYPE_CHECKING

from ..common import EnvoyRoute
from ...ir import IRResource
from ...ir.irmapping import IRMappingGroup

from .v2ratelimitaction import V2RateLimitAction

if TYPE_CHECKING:
    from . import V2Config


class V2Route(dict):
    def __init__(self, config: 'V2Config', group: IRMappingGroup) -> None:
        super().__init__()

        envoy_route = EnvoyRoute(group).envoy_route

        match = {
            envoy_route: group.get('prefix'),
            'case_sensitive': group.get('case_sensitive', True),
        }

        headers = self.generate_headers(group)

        if len(headers) > 0:
            match['headers'] = headers

        clusters = []
        req_hdrs_to_add = group.get('request_headers_to_add', None)

        for mapping in group.mappings:
            cluster = {
                'name': mapping.cluster.name,
                'weight': mapping.weight
            }

            if req_hdrs_to_add:
                cluster['request_headers_to_add'] = req_hdrs_to_add

            clusters.append(cluster)

        route = {
            'priority': group.get('priority'),
            'timeout': "%0.3fs" % (group.get('timeout_ms', 3000) / 1000.0),
            'weighted_clusters': {
                'clusters': clusters
            }
        }

        if group.get('rewrite', None):
            route['prefix_rewrite'] = group['rewrite']

        if 'host_rewrite' in group:
            route['host_rewrite'] = group['host_rewrite']

        if 'auto_host_rewrite' in group:
            route['auto_host_rewrite'] = group['auto_host_rewrite']

        cors = None

        if "cors" in group:
            cors = group.cors.as_dict()
        elif "cors" in config.ir.ambassador_module:
            cors = config.ir.ambassador_module.cors.as_dict()

        if cors:
            for key in [ "_active", "_referenced_by", "_rkey", "kind", "location", "name" ]:
                cors.pop(key, None)

            route['cors'] = cors

        # Is RateLimit a thing?
        rlsvc = config.ir.ratelimit

        if rlsvc:
            # Yup. Build our labels into a set of RateLimitActions (remember that default
            # labels have already been handled, as has translating from v0 'rate_limits' to
            # v1 'labels').

            if "labels" in group:
                # The Envoy RateLimit filter only supports one domain, so grab the configured domain
                # from the RateLimitService and use that to look up the labels we should use.

                rate_limits = []

                for rl in group.labels.get(rlsvc.domain, []):
                    action = V2RateLimitAction(config, rl)

                    if action.valid:
                        rate_limits.append(action.to_dict())

                if rate_limits:
                    route["rate_limits"] = rate_limits

        self['match'] = match
        self['route'] = route

        request_headers_to_add = []

        for mapping in group.mappings:
            for k, v in mapping.get('add_request_headers', {}).items():
                request_headers_to_add.append({
                    'header': {'key': k, 'value': v},
                    'append': True, # ???
                    })

        if request_headers_to_add:
            self['request_headers_to_add'] = request_headers_to_add

        host_redirect = group.get('host_redirect', None)

        if host_redirect:
            self['redirect'] = {
                'host_redirect': host_redirect.service
            }

            path_redirect = host_redirect.get('path_redirect', None)

            if path_redirect:
                self['redirect']['path_redirect'] = path_redirect

    @classmethod
    def generate(cls, config: 'V2Config') -> None:
        config.routes = []

        for irgroup in config.ir.ordered_groups():
            route = config.save_element('route', irgroup, V2Route(config, irgroup))
            if irgroup.get('sni'):
                info = {
                    'hosts': irgroup['tls_context']['hosts'],
                    'secret_info': irgroup['tls_context']['secret_info']
                }
                config.sni_routes.append({'route': route, 'info': info})
            else:
                config.routes.append(route)

    @staticmethod
    def generate_headers(mapping_group: IRMappingGroup) -> List[dict]:
        headers = []

        group_headers = mapping_group.get('headers', [])

        for group_header in group_headers:
            header = { 'name': group_header.get('name') }

            if group_header.get('regex'):
                header['regex_match'] = group_header.get('value')
            else:
                header['exact_match'] = group_header.get('value')

            headers.append(header)

        return headers
