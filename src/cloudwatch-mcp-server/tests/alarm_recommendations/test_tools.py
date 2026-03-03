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

"""Tests for Alarm Recommendations tools."""

import pytest
from awslabs.cloudwatch_mcp_server.alarm_recommendations.models import (
    GetAlarmRecommendationsResponse,
)
from awslabs.cloudwatch_mcp_server.alarm_recommendations.tools import (
    AlarmRecommendationsTools,
)
from unittest.mock import AsyncMock, Mock, patch


@pytest.fixture
def mock_context():
    """Create mock MCP context."""
    context = Mock()
    context.info = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    return context


class TestGetAlarmRecommendationsForAccount:
    """Test cases for get_alarm_recommendations_for_account tool."""

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_success(self, mock_client_cls, mock_context):
        """Test successful retrieval of alarm recommendations."""
        mock_client = Mock()
        mock_client.call.return_value = {
            'generationStatus': 'COMPLETED',
            'lastGeneratedAt': 1772503246.0,
            'recommendations': [
                {
                    'recommendationId': 'rec-1',
                    'namespace': 'AWS/EC2',
                    'metricName': 'CPUUtilization',
                    'dimensions': [],
                    'statistic': 'Average',
                    'threshold': 90.0,
                    'comparisonOperator': 'GreaterThanThreshold',
                    'period': 300,
                    'evaluationPeriods': 3,
                    'intent': 'Monitor CPU',
                    'description': 'High CPU alarm',
                },
            ],
        }
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        result = await tools.get_alarm_recommendations_for_account(mock_context)

        assert isinstance(result, GetAlarmRecommendationsResponse)
        assert result.generation_status == 'COMPLETED'
        assert len(result.recommendations) == 1
        assert result.recommendations[0].metric_name == 'CPUUtilization'

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_error_handling(self, mock_client_cls, mock_context):
        """Test that errors are logged and re-raised."""
        mock_client = Mock()
        mock_client.call.side_effect = Exception('API error')
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        with pytest.raises(Exception, match='API error'):
            await tools.get_alarm_recommendations_for_account(mock_context)

        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_with_profile_and_region(self, mock_client_cls, mock_context):
        """Test that profile and region are passed to the client."""
        mock_client = Mock()
        mock_client.call.return_value = {
            'generationStatus': 'COMPLETED',
            'recommendations': [],
        }
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        await tools.get_alarm_recommendations_for_account(
            mock_context, region='eu-west-1', profile_name='my-profile'
        )

        mock_client_cls.assert_called_once_with(profile_name='my-profile')

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_in_progress_status(self, mock_client_cls, mock_context):
        """Test handling of IN_PROGRESS generation status."""
        mock_client = Mock()
        mock_client.call.return_value = {
            'generationStatus': 'IN_PROGRESS',
            'recommendations': [],
        }
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        result = await tools.get_alarm_recommendations_for_account(mock_context)

        assert result.generation_status == 'IN_PROGRESS'
        assert result.recommendations == []
