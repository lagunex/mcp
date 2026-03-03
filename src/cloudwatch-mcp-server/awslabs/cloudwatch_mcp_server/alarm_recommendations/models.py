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

"""Data models for Alarm Recommendations MCP tools."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Dict, List


class AlarmRecommendation(BaseModel):
    """A single alarm recommendation from the service."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    recommendation_id: str = Field(..., description='Unique ID of the recommendation')
    namespace: str = Field(..., description='AWS namespace (e.g., AWS/DynamoDB)')
    metric_name: str = Field(..., description='CloudWatch metric name')
    dimensions: List[Dict[str, str]] = Field(default_factory=list, description='Metric dimensions')
    statistic: str = Field(..., description='Statistic (e.g., Maximum, Average)')
    threshold: float = Field(..., description='Alarm threshold value')
    comparison_operator: str = Field(
        ..., description='Comparison operator (e.g., GreaterThanThreshold)'
    )
    period: int = Field(..., description='Evaluation period in seconds')
    evaluation_periods: int = Field(..., description='Number of evaluation periods')
    intent: str = Field(..., description='Intent of the recommendation')
    description: str = Field(..., description='Human-readable description')


class GetAlarmRecommendationsResponse(BaseModel):
    """Response from GetAlarmRecommendations."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    generation_status: str = Field(..., description='Status: COMPLETED or IN_PROGRESS')
    last_generated_at: float | None = Field(
        default=None, description='Epoch timestamp of last generation'
    )
    recommendations: List[AlarmRecommendation] = Field(
        default_factory=list, description='List of alarm recommendations'
    )
    message: str | None = Field(default=None, description='Optional informational message')
