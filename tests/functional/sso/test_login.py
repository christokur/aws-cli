# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import hashlib
import json
import os
import re

from tests.functional.sso import BaseSSOTest


class TestLoginCommand(BaseSSOTest):
    _TIMESTAMP_FORMAT_PATTERN = re.compile(
        r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ'
    )

    def add_oidc_workflow_responses(self, access_token,
                                    include_register_response=True):
        responses = [
            # StartDeviceAuthorization response
            {
                'interval': 1,
                'expiresIn': 600,
                'userCode': 'foo',
                'deviceCode': 'foo-device-code',
                'verificationUri': 'https://sso.fake/device',
                'verificationUriComplete': 'https://sso.verify',
            },
            # CreateToken responses
            {
                'Error': {
                    'Code': 'AuthorizationPendingException',
                    'Message': 'Authorization is still pending',
                }
            },
            {
                'expiresIn': self.expires_in,
                'tokenType': 'Bearer',
                'accessToken': access_token,
            }
        ]
        if include_register_response:
            responses.insert(
                0,
                {
                    'clientSecretExpiresAt': self.expiration_time,
                    'clientId': 'foo-client-id',
                    'clientSecret': 'foo-client-secret',
                }
            )
        self.parsed_responses = responses

    def assert_cache_contains_token(
        self,
        start_url,
        expected_token,
        session_name=None,
    ):
        cached_files = os.listdir(self.token_cache_dir)
        # The registration and cached access token
        self.assertEqual(len(cached_files), 2)
        cached_token_filename = self._get_cached_token_filename(
            start_url,
            session_name,
        )
        self.assertIn(cached_token_filename, cached_files)
        self.assertEqual(
            self._get_cached_response(cached_token_filename)['accessToken'],
            expected_token
        )

    def _get_cached_token_filename(self, start_url, session_name):
        to_hash = start_url
        if session_name:
            to_hash = session_name
        return hashlib.sha1(to_hash.encode('utf-8')).hexdigest() + '.json'

    def _get_cached_response(self, token_filename):
        token_path = os.path.join(self.token_cache_dir, token_filename)
        with open(token_path, 'r') as f:
            cached_response = json.loads(f.read())
            return cached_response

    def assert_cache_token_expiration_time_format_is_correct(self):
        token_filename = self._get_cached_token_filename(self.start_url, None)
        token_path = os.path.join(self.token_cache_dir, token_filename)
        with open(token_path, 'r') as f:
            cached_response = json.loads(f.read())
            self.assertIsNotNone(
                self._TIMESTAMP_FORMAT_PATTERN.match(
                    cached_response['expiresAt']
                )
            )

    def test_login(self):
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login')
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            expected_token=self.access_token
        )

    def test_login_no_browser(self):
        self.add_oidc_workflow_responses(self.access_token)
        stdout, _, _ = self.run_cmd('sso login --no-browser')
        self.assertIn('Browser will not be automatically opened.', stdout)
        self.open_browser_mock.assert_not_called()
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            expected_token=self.access_token
        )

    def test_login_forces_refresh(self):
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login')
        # The register response from the first login should have been
        # cached.
        self.add_oidc_workflow_responses(
            'new.token', include_register_response=False)
        self.run_cmd('sso login')
        self.assert_cache_contains_token(
            start_url=self.start_url,
            expected_token='new.token'
        )

    def test_login_no_sso_configuration(self):
        self.set_config_file_content(content='')
        _, stderr, _ = self.run_cmd('sso login', expected_rc=253)
        self.assertIn(
            'Missing the following required SSO configuration',
            stderr
        )

    def test_login_minimal_sso_configuration(self):
        content = (
            '[default]\n'
            'sso_start_url={start_url}\n'
            'sso_region={sso_region}\n'
        ).format(start_url=self.start_url, sso_region=self.sso_region)
        self.set_config_file_content(content=content)
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login')
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            expected_token=self.access_token
        )

    def test_login_partially_missing_sso_configuration(self):
        content = (
            '[default]\n'
            'sso_start_url=%s\n' % self.start_url
        )
        self.set_config_file_content(content=content)
        _, stderr, _ = self.run_cmd('sso login', expected_rc=253)
        self.assertIn(
            'Missing the following required SSO configuration',
            stderr
        )
        self.assertIn('sso_region', stderr)
        self.assertNotIn('sso_start_url', stderr)
        self.assertNotIn('sso_account_id', stderr)
        self.assertNotIn('sso_role_name', stderr)

    def test_token_cache_datetime_format(self):
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login')
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            expected_token=self.access_token
        )
        self.assert_cache_token_expiration_time_format_is_correct()

    def test_login_sso_session(self):
        content = self.get_sso_session_config('test-session')
        self.set_config_file_content(content=content)
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login')
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            session_name='test-session',
            expected_token=self.access_token,
        )

    def test_login_sso_with_explicit_sso_session_arg(self):
        content = self.get_sso_session_config(
            'test-session', include_profile=False)
        self.set_config_file_content(content=content)
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login --sso-session test-session')
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            session_name='test-session',
            expected_token=self.access_token,
        )

    def test_login_sso_session_with_scopes(self):
        self.registration_scopes = ['sso:foo', 'sso:bar']
        content = self.get_sso_session_config('test-session')
        self.set_config_file_content(content=content)
        self.add_oidc_workflow_responses(self.access_token)
        self.run_cmd('sso login')
        self.assert_used_expected_sso_region(expected_region=self.sso_region)
        self.assert_cache_contains_token(
            start_url=self.start_url,
            session_name='test-session',
            expected_token=self.access_token,
        )
        operation, params = self.operations_called[0]
        self.assertEqual(operation.name, 'RegisterClient')
        self.assertEqual(params.get('scopes'), self.registration_scopes)

    def test_login_sso_session_missing_config(self):
        content = (
            f'[default]\n'
            f'sso_session=test\n'
            f'[sso-session test]\n'
        )
        self.set_config_file_content(content=content)
        _, stderr, _ = self.run_cmd('sso login', expected_rc=253)
        self.assertIn(
            'SSO configuration values: sso_start_url, sso_region',
            stderr
        )

    def test_login_sso_session_missing(self):
        content = (
            f'[default]\n'
            f'sso_session=test\n'
        )
        self.set_config_file_content(content=content)
        _, stderr, _ = self.run_cmd('sso login', expected_rc=253)
        self.assertIn('sso-session does not exist: "test"', stderr)
