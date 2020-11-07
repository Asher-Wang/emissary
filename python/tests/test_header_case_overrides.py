import json
import logging
import time
import sys

import pytest
import requests

from utils import run_and_assert, apply_kube_artifacts, delete_kube_artifacts, install_ambassador, \
        httpbin_manifests, create_httpbin_mapping

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s test %(levelname)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("ambassador")

from ambassador import Config, IR
from ambassador.ir.irerrorresponse import IRErrorResponse
from ambassador.envoy.v2.v2config import V2Config
from ambassador.envoy.v2.v2listener import V2Listener
from ambassador.envoy import EnvoyConfig
from ambassador.fetch import ResourceFetcher
from ambassador.utils import NullSecretHandler

def _ambassador_module_config():
    return '''
---
apiVersion: getambassador.io/v1
kind: Module
name: ambassador
config:
'''

def _ambassador_module_header_case_overrides(overrides, proper_case=False):
    mod = _ambassador_module_config()
    if len(overrides) == 0:
        mod = mod + '''
  header_case_overrides: []
'''
        return mod

    mod = mod + '''
  header_case_overrides:
'''
    for override in overrides:
        mod = mod + f'''
  - {override}
'''
    # proper case isn't valid if header_case_overrides are set, but we do
    # it here for tests that want to test that this is in fact invalid.
    if proper_case:
        mod = mod + f'''
    proper_case: true
'''
    return mod

def _test_headercaseoverrides(yaml, expectations, expect_norules=False):
    aconf = Config()

    fetcher = ResourceFetcher(logger, aconf)
    fetcher.parse_yaml(yaml)

    aconf.load_all(fetcher.sorted())

    secret_handler = NullSecretHandler(logger, None, None, "0")

    ir = IR(aconf, file_checker=lambda path: True, secret_handler=secret_handler)
    #print(f"ir = {ir.as_json()}")
    assert ir

    econf = EnvoyConfig.generate(ir, "V2")
    assert econf, "could not create an econf"
    #print(f"econf = {econf.as_json()}")

    found_rules = False
    conf = econf.as_dict()
    for listener in conf['static_resources']['listeners']:
        for filter_chain in listener['filter_chains']:
            for f in filter_chain['filters']:
                typed_config = f['typed_config']
                if 'http_protocol_options' not in typed_config:
                    continue

                http_protocol_options = typed_config['http_protocol_options']
                if expect_norules:
                    assert 'header_key_format' not in http_protocol_options, \
                        f"'header_key_format' found unexpectedly, ted typed_config {typed_config}"
                    continue

                assert 'header_key_format' in http_protocol_options, \
                        f"'header_key_format' not found, typed_config {typed_config}"

                header_key_format = http_protocol_options['header_key_format']
                assert 'custom' in header_key_format, \
                        f"'custom' not found, typed_config {typed_config}"

                rules = header_key_format['custom']['rules']
                assert len(rules) == len(expectations)
                for e in expectations:
                    hdr = e.lower()
                    assert hdr in rules
                    rule = rules[hdr]
                    assert rule == e, f"unexpected rule {rule} in {rules}"
                found_rules = True
    if expect_norules:
        assert not found_rules
    else:
        assert found_rules

def _test_headercaseoverrides_rules(rules, expected=None, expect_norules=False):
    if not expected:
        expected = rules
    _test_headercaseoverrides(
        _ambassador_module_header_case_overrides(rules),
        expected,
        expect_norules=expect_norules
    )

# Test that we throw assertions for obviously wrong cases
def test_testsanity():
    failed = False
    try:
        _test_headercaseoverrides_rules(['X-ABC'], expected=['X-Wrong'])
    except AssertionError as e:
        failed = True
    assert failed

    failed = False
    try:
        _test_headercaseoverrides_rules([], expected=['X-Wrong'])
    except AssertionError as e:
        failed = True
    assert failed

# Test that we can parse a variety of header case override arrays.
def test_headercaseoverrides():
    _test_headercaseoverrides_rules([], expect_norules=True)
    _test_headercaseoverrides_rules([{}], expect_norules=True)
    _test_headercaseoverrides_rules([5], expect_norules=True)
    _test_headercaseoverrides_rules(['X-ABC'])
    _test_headercaseoverrides_rules(['X-foo', 'X-ABC-Baz'])
    _test_headercaseoverrides_rules(['x-goOd', 'X-alSo-good', 'Authorization'])
    _test_headercaseoverrides_rules(['x-good', ['hello']], expected=['x-good'])
    _test_headercaseoverrides_rules(['X-ABC', 'x-foo', 5, {}], expected=['X-ABC', 'x-foo'])

# Test that we always omit header case overrides if proper case is set
def test_headercaseoverrides_propercasefail():
    _test_headercaseoverrides(
        _ambassador_module_header_case_overrides(['My-OPINIONATED-CASING'], proper_case=True),
        [],
        expect_norules=True
    )
    _test_headercaseoverrides(
        _ambassador_module_header_case_overrides([], proper_case=True),
        [],
        expect_norules=True
    )
    _test_headercaseoverrides(
        _ambassador_module_header_case_overrides([{"invalid": "true"}, "X-COOL"], proper_case=True),
        [],
        expect_norules=True
    )


class HeaderCaseOverridesTesting:
    def create_module(self, namespace):
        manifest = f"""
---
apiVersion: getambassador.io/v2
kind: Module
metadata:
  name: ambassador
spec:
  config:
    header_case_overrides:
    - X-HELLO
    - X-FOO-Bar
        """

        apply_kube_artifacts(namespace=namespace, artifacts=manifest)

    def test_header_case_overrides(self):
        # Is there any reason not to use the default namespace?
        namespace = 'header-case-overrides'

        # Install Ambassador
        install_ambassador(namespace=namespace, envs=[
            {
                'name': 'AMBASSADOR_SINGLE_NAMESPACE',
                'value': 'true'
            }
        ])

        # Install httpbin
        apply_kube_artifacts(namespace=namespace, artifacts=httpbin_manifests)

        # Install module
        self.create_module(namespace)

        # Install httpbin mapping
        create_httpbin_mapping(namespace=namespace)

        # Now let's wait for ambassador and httpbin pods to become ready
        run_and_assert(['kubectl', 'wait', '--timeout=90s', '--for=condition=Ready', 'pod', '-l', 'service=ambassador', '-n', namespace])
        run_and_assert(['kubectl', 'wait', '--timeout=90s', '--for=condition=Ready', 'pod', '-l', 'service=httpbin', '-n', namespace])

        # Let's port-forward ambassador service to talk to Ambassador.
        # IMPORTANT: We _must_ choose a unique port_forward_port so long as test_watt.py,
        # test_knative.py, and others like it, run in the same environment as this test.
        # Otherwise we get port collisions and it's madness.
        port_forward_port = 6123
        port_forward_command = ['kubectl', 'port-forward', '--namespace', namespace, 'service/ambassador', f'{port_forward_port}:80']
        run_and_assert(port_forward_command, communicate=False)

        print("Waiting 2 seconds, just because...")
        time.sleep(2)

        # Assert 200 OK at httpbin/status/200 endpoint
        ready = False
        httpbin_url = f'http://localhost:{port_forward_port}/httpbin/status/200'

        loop_limit = 2
        while not ready:
            assert loop_limit > 0, "httpbin is not ready yet, aborting..."
            try:
                print(f"trying {httpbin_url}...")
                resp = requests.get(httpbin_url, timeout=5)
                code = resp.status_code
                assert code == 200, f"Expected 200 OK, got {code}"
                resp.close()
                print(f"{httpbin_url} is ready")
                ready = True

            except Exception as e:
                print(f"Error: {e}")
                print(f"{httpbin_url} not ready yet, trying again...")
                time.sleep(1)
                loop_limit -= 1

        assert ready

        httpbin_url = f'http://localhost:{port_forward_port}/httpbin/response-headers?x-Hello=1&X-foo-Bar=1&x-Lowercase1=1&x-lowercase2=1'
        resp = requests.get(httpbin_url, timeout=5)
        code = resp.status_code
        assert code == 200, f"Expected 200 OK, got {code}"


        # Very important: this test relies on matching case sensitive header keys.
        # Fortunately it appears that we can convert resp.headers, a case insensitive
        # dictionary, into a list of case sensitive keys.
        keys = [ h for h in resp.headers.keys() ]
        for k in keys:
            print(f"header key: {k}")

        assert 'x-hello' not in keys
        assert 'X-HELLO' in keys
        assert 'x-foo-bar' not in keys
        assert 'X-FOO-Bar' in keys
        assert 'x-lowercase1' in keys
        assert 'x-Lowercase1' not in keys
        assert 'x-lowercase2' in keys
        resp.close()


def test_ambassador_headercaseoverrides():
    t = HeaderCaseOverridesTesting()
    t.test_header_case_overrides()

if __name__ == '__main__':
    pytest.main(sys.argv)
