# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

"""Tests for the Alarm Recommendations SigV4 HTTP client."""

import json
import pytest
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError


class TestAlarmRecommendationsClient:
    """Test cases for AlarmRecommendationsClient."""

    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.urlopen')
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.Session')
    def test_sigv4_signing_setup(self, mock_session_cls, mock_urlopen):
        """Test that SigV4Auth is called with correct service name and region."""
        from awslabs.cloudwatch_mcp_server.alarm_recommendations.client import (
            AlarmRecommendationsClient,
        )

        mock_session = Mock()
        mock_creds = Mock()
        mock_session.get_credentials.return_value.get_frozen_credentials.return_value = mock_creds
        mock_session_cls.return_value = mock_session

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"generationStatus": "COMPLETED"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch(
            'awslabs.cloudwatch_mcp_server.alarm_recommendations.client.SigV4Auth'
        ) as mock_auth_cls:
            mock_auth = Mock()
            mock_auth_cls.return_value = mock_auth

            client = AlarmRecommendationsClient()
            client.call('GetAlarmRecommendations', {})

            mock_auth_cls.assert_called_once_with(
                mock_creds, 'awsalarmkorerecommendations', 'us-east-1'
            )
            mock_auth.add_auth.assert_called_once()

    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.urlopen')
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.Session')
    def test_successful_request(self, mock_session_cls, mock_urlopen):
        """Test that a successful request returns parsed JSON."""
        from awslabs.cloudwatch_mcp_server.alarm_recommendations.client import (
            AlarmRecommendationsClient,
        )

        mock_session = Mock()
        mock_creds = Mock()
        mock_session.get_credentials.return_value.get_frozen_credentials.return_value = mock_creds
        mock_session_cls.return_value = mock_session

        expected = {'generationStatus': 'COMPLETED', 'recommendations': []}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.SigV4Auth'):
            client = AlarmRecommendationsClient()
            result = client.call('GetAlarmRecommendations', {})

        assert result == expected

    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.urlopen')
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.Session')
    def test_http_error(self, mock_session_cls, mock_urlopen):
        """Test that HTTP errors are raised with status code and body."""
        from awslabs.cloudwatch_mcp_server.alarm_recommendations.client import (
            AlarmRecommendationsClient,
        )

        mock_session = Mock()
        mock_creds = Mock()
        mock_session.get_credentials.return_value.get_frozen_credentials.return_value = mock_creds
        mock_session_cls.return_value = mock_session

        mock_urlopen.side_effect = HTTPError(
            url='https://example.com',
            code=403,
            msg='Forbidden',
            hdrs=None,
            fp=MagicMock(read=Mock(return_value=b'Access denied')),
        )

        with patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.SigV4Auth'):
            client = AlarmRecommendationsClient()
            with pytest.raises(Exception, match='403'):
                client.call('GetAlarmRecommendations', {})

    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.urlopen')
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.Session')
    def test_profile_passed_to_session(self, mock_session_cls, mock_urlopen):
        """Test that profile_name is passed to boto3 Session."""
        from awslabs.cloudwatch_mcp_server.alarm_recommendations.client import (
            AlarmRecommendationsClient,
        )

        mock_session = Mock()
        mock_creds = Mock()
        mock_session.get_credentials.return_value.get_frozen_credentials.return_value = mock_creds
        mock_session_cls.return_value = mock_session

        mock_response = MagicMock()
        mock_response.read.return_value = b'{}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.client.SigV4Auth'):
            client = AlarmRecommendationsClient(profile_name='my-profile')
            client.call('GetAlarmRecommendations', {})

        mock_session_cls.assert_called_once_with(profile_name='my-profile')
