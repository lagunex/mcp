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

"""Tests for Alarm Recommendations Pydantic models."""

from awslabs.cloudwatch_mcp_server.alarm_recommendations.models import (
    AlarmRecommendation,
    GetAlarmRecommendationsResponse,
    NamespaceSummary,
    SummarizeAlarmRecommendationsResponse,
)


class TestAlarmRecommendation:
    """Test cases for AlarmRecommendation model."""

    def test_from_camel_case_dict(self):
        """Test constructing from API camelCase response."""
        data = {
            'recommendationId': '9139f54f-a475-4184-8f60-277491bfca00',
            'namespace': 'AWS/DynamoDB',
            'metricName': 'AccountProvisionedReadCapacityUtilization',
            'dimensions': [],
            'statistic': 'Maximum',
            'threshold': 80.0,
            'comparisonOperator': 'GreaterThanThreshold',
            'period': 300,
            'evaluationPeriods': 2,
            'intent': 'Monitor capacity',
            'description': 'Alert on high read capacity',
        }
        rec = AlarmRecommendation.model_validate(data)
        assert rec.recommendation_id == '9139f54f-a475-4184-8f60-277491bfca00'
        assert rec.metric_name == 'AccountProvisionedReadCapacityUtilization'
        assert rec.comparison_operator == 'GreaterThanThreshold'
        assert rec.evaluation_periods == 2


class TestGetAlarmRecommendationsResponse:
    """Test cases for GetAlarmRecommendationsResponse model."""

    def test_completed_response(self):
        """Test parsing a COMPLETED response with recommendations."""
        data = {
            'generationStatus': 'COMPLETED',
            'lastGeneratedAt': 1772503246.0,
            'recommendations': [
                {
                    'recommendationId': 'rec-1',
                    'namespace': 'AWS/EC2',
                    'metricName': 'CPUUtilization',
                    'dimensions': [{'Name': 'InstanceId', 'Value': 'i-123'}],
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
        resp = GetAlarmRecommendationsResponse.model_validate(data)
        assert resp.generation_status == 'COMPLETED'
        assert resp.last_generated_at == 1772503246.0
        assert len(resp.recommendations) == 1
        assert resp.recommendations[0].namespace == 'AWS/EC2'

    def test_in_progress_response(self):
        """Test parsing an IN_PROGRESS response."""
        data = {
            'generationStatus': 'IN_PROGRESS',
            'recommendations': [],
        }
        resp = GetAlarmRecommendationsResponse.model_validate(data)
        assert resp.generation_status == 'IN_PROGRESS'
        assert resp.last_generated_at is None
        assert resp.recommendations == []

    def test_optional_fields_none(self):
        """Test that optional fields default to None."""
        data = {
            'generationStatus': 'COMPLETED',
            'recommendations': [],
        }
        resp = GetAlarmRecommendationsResponse.model_validate(data)
        assert resp.last_generated_at is None
        assert resp.message is None


class TestNamespaceSummary:
    """Test cases for NamespaceSummary model."""

    def test_all_fields(self):
        """Test construction with all fields provided."""
        summary = NamespaceSummary(
            namespace='AWS/EC2',
            total=10,
            error_fault=2,
            latency=3,
            requests=1,
            utilization=3,
            other=1,
        )
        assert summary.namespace == 'AWS/EC2'
        assert summary.total == 10
        assert summary.error_fault == 2
        assert summary.latency == 3
        assert summary.requests == 1
        assert summary.utilization == 3
        assert summary.other == 1

    def test_default_counts(self):
        """Test that category counts default to 0."""
        summary = NamespaceSummary(namespace='AWS/Lambda', total=5)
        assert summary.error_fault == 0
        assert summary.latency == 0
        assert summary.requests == 0
        assert summary.utilization == 0
        assert summary.other == 0

    def test_camel_case_alias(self):
        """Test construction from camelCase keys via model_validate."""
        data = {
            'namespace': 'AWS/DynamoDB',
            'total': 4,
            'errorFault': 1,
            'latency': 1,
            'requests': 1,
            'utilization': 0,
            'other': 1,
        }
        summary = NamespaceSummary.model_validate(data)
        assert summary.error_fault == 1
        assert summary.other == 1

    def test_serialization_camel_case(self):
        """Test that model_dump with by_alias produces camelCase keys."""
        summary = NamespaceSummary(namespace='AWS/S3', total=2, error_fault=1, other=1)
        dumped = summary.model_dump(by_alias=True)
        assert 'errorFault' in dumped
        assert 'namespace' in dumped
        assert dumped['errorFault'] == 1


class TestSummarizeAlarmRecommendationsResponse:
    """Test cases for SummarizeAlarmRecommendationsResponse model."""

    def test_full_construction(self):
        """Test construction with all fields."""
        ns = NamespaceSummary(namespace='AWS/EC2', total=3, utilization=2, other=1)
        resp = SummarizeAlarmRecommendationsResponse(
            generation_status='COMPLETED',
            total_recommendations=3,
            total_namespaces=1,
            namespaces=[ns],
            message='All done',
        )
        assert resp.generation_status == 'COMPLETED'
        assert resp.total_recommendations == 3
        assert resp.total_namespaces == 1
        assert len(resp.namespaces) == 1
        assert resp.namespaces[0].namespace == 'AWS/EC2'
        assert resp.message == 'All done'

    def test_empty_namespaces(self):
        """Test construction with empty namespaces list."""
        resp = SummarizeAlarmRecommendationsResponse(
            generation_status='IN_PROGRESS',
            total_recommendations=0,
            total_namespaces=0,
            namespaces=[],
        )
        assert resp.namespaces == []
        assert resp.message is None

    def test_camel_case_alias(self):
        """Test construction from camelCase keys via model_validate."""
        data = {
            'generationStatus': 'COMPLETED',
            'totalRecommendations': 5,
            'totalNamespaces': 2,
            'namespaces': [
                {'namespace': 'AWS/EC2', 'total': 3},
                {'namespace': 'AWS/Lambda', 'total': 2},
            ],
        }
        resp = SummarizeAlarmRecommendationsResponse.model_validate(data)
        assert resp.total_recommendations == 5
        assert resp.total_namespaces == 2
        assert len(resp.namespaces) == 2

    def test_message_defaults_to_none(self):
        """Test that message defaults to None when not provided."""
        resp = SummarizeAlarmRecommendationsResponse(
            generation_status='COMPLETED',
            total_recommendations=0,
            total_namespaces=0,
            namespaces=[],
        )
        assert resp.message is None
