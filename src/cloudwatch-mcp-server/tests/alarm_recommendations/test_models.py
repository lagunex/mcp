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
