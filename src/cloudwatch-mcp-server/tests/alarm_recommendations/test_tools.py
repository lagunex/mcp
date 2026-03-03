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
    AlarmRecommendation,
    GetAlarmRecommendationsResponse,
    SummarizeAlarmRecommendationsResponse,
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


def _make_recommendation(metric_name='TestMetric', intent='Test intent', namespace='AWS/EC2'):
    """Helper to create an AlarmRecommendation with minimal required fields."""
    return AlarmRecommendation(
        recommendation_id='rec-1',
        namespace=namespace,
        metric_name=metric_name,
        dimensions=[],
        statistic='Average',
        threshold=90.0,
        comparison_operator='GreaterThanThreshold',
        period=300,
        evaluation_periods=3,
        intent=intent,
        description='Test alarm',
    )


class TestClassifyRecommendation:
    """Test cases for _classify_recommendation."""

    def test_error_fault_by_metric(self):
        """Test error/fault classification by metric name."""
        tools = AlarmRecommendationsTools()
        rec = _make_recommendation(metric_name='5XXError')
        assert tools._classify_recommendation(rec) == 'error_fault'

    def test_error_fault_by_intent(self):
        """Test error/fault classification by intent."""
        tools = AlarmRecommendationsTools()
        rec = _make_recommendation(intent='Monitor error rate')
        assert tools._classify_recommendation(rec) == 'error_fault'

    def test_latency_by_metric(self):
        """Test latency classification."""
        tools = AlarmRecommendationsTools()
        for metric in ['Duration', 'TargetResponseTime']:
            rec = _make_recommendation(metric_name=metric)
            assert tools._classify_recommendation(rec) == 'latency'

    def test_requests_by_metric(self):
        """Test requests classification."""
        tools = AlarmRecommendationsTools()
        for metric in ['Invocations', 'RequestCount']:
            rec = _make_recommendation(metric_name=metric)
            assert tools._classify_recommendation(rec) == 'requests'

    def test_utilization_by_metric(self):
        """Test utilization classification."""
        tools = AlarmRecommendationsTools()
        rec = _make_recommendation(metric_name='CPUUtilization')
        assert tools._classify_recommendation(rec) == 'utilization'

    def test_other(self):
        """Test other classification for unknown metrics."""
        tools = AlarmRecommendationsTools()
        rec = _make_recommendation(metric_name='SomeUnknownMetric', intent='custom')
        assert tools._classify_recommendation(rec) == 'other'

    def test_case_insensitive(self):
        """Test classification is case-insensitive."""
        tools = AlarmRecommendationsTools()
        rec = _make_recommendation(metric_name='cpuutilization')
        assert tools._classify_recommendation(rec) == 'utilization'

    def test_priority_error_over_latency(self):
        """Test error_fault takes priority over latency."""
        tools = AlarmRecommendationsTools()
        rec = _make_recommendation(metric_name='ErrorDuration')
        assert tools._classify_recommendation(rec) == 'error_fault'


class TestSummarizeAlarmRecommendations:
    """Test cases for summarize_alarm_recommendations tool."""

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_multiple_namespaces(self, mock_client_cls, mock_context):
        """Test summary with multiple namespaces and categories."""
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
                {
                    'recommendationId': 'rec-2',
                    'namespace': 'AWS/Lambda',
                    'metricName': 'Errors',
                    'dimensions': [],
                    'statistic': 'Sum',
                    'threshold': 1.0,
                    'comparisonOperator': 'GreaterThanThreshold',
                    'period': 300,
                    'evaluationPeriods': 1,
                    'intent': 'Monitor errors',
                    'description': 'Lambda errors',
                },
                {
                    'recommendationId': 'rec-3',
                    'namespace': 'AWS/Lambda',
                    'metricName': 'Duration',
                    'dimensions': [],
                    'statistic': 'Average',
                    'threshold': 5000.0,
                    'comparisonOperator': 'GreaterThanThreshold',
                    'period': 300,
                    'evaluationPeriods': 3,
                    'intent': 'Monitor latency',
                    'description': 'Lambda duration',
                },
            ],
        }
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        result = await tools.summarize_alarm_recommendations(mock_context)

        assert isinstance(result, SummarizeAlarmRecommendationsResponse)
        assert result.generation_status == 'COMPLETED'
        assert result.total_recommendations == 3
        assert result.total_namespaces == 2

        ns_map = {ns.namespace: ns for ns in result.namespaces}
        assert ns_map['AWS/EC2'].total == 1
        assert ns_map['AWS/EC2'].utilization == 1
        assert ns_map['AWS/Lambda'].total == 2
        assert ns_map['AWS/Lambda'].error_fault == 1
        assert ns_map['AWS/Lambda'].latency == 1

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_in_progress_status(self, mock_client_cls, mock_context):
        """Test IN_PROGRESS status returns early."""
        mock_client = Mock()
        mock_client.call.return_value = {
            'generationStatus': 'IN_PROGRESS',
            'recommendations': [],
        }
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        result = await tools.summarize_alarm_recommendations(mock_context)

        assert result.generation_status == 'IN_PROGRESS'
        assert result.total_recommendations == 0
        assert result.namespaces == []

    @pytest.mark.asyncio
    @patch('awslabs.cloudwatch_mcp_server.alarm_recommendations.tools.AlarmRecommendationsClient')
    async def test_error_handling(self, mock_client_cls, mock_context):
        """Test that errors are logged and re-raised."""
        mock_client = Mock()
        mock_client.call.side_effect = Exception('API error')
        mock_client_cls.return_value = mock_client

        tools = AlarmRecommendationsTools()
        with pytest.raises(Exception, match='API error'):
            await tools.summarize_alarm_recommendations(mock_context)

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
        await tools.summarize_alarm_recommendations(
            mock_context, region='eu-west-1', profile_name='my-profile'
        )

        mock_client_cls.assert_called_once_with(profile_name='my-profile')


class TestToolRegistration:
    """Test that tools are properly registered."""

    def test_summarize_tool_registered(self):
        """Test summarize_alarm_recommendations is registered."""
        tools = AlarmRecommendationsTools()
        mock_mcp = Mock()
        mock_mcp.tool.return_value = lambda fn: fn
        tools.register(mock_mcp)

        tool_names = [call.kwargs['name'] for call in mock_mcp.tool.call_args_list]
        assert 'summarize_alarm_recommendations' in tool_names
