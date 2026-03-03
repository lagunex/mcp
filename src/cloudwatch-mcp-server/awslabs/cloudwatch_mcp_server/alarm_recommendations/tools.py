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

"""Alarm Recommendations tools for MCP server."""

from awslabs.cloudwatch_mcp_server.alarm_recommendations.client import (
    AlarmRecommendationsClient,
)
from awslabs.cloudwatch_mcp_server.alarm_recommendations.models import (
    AlarmRecommendation,
    GetAlarmRecommendationsResponse,
    NamespaceSummary,
    SummarizeAlarmRecommendationsResponse,
)
from collections import defaultdict
from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated


_CATEGORY_KEYWORDS = {
    'error_fault': [
        'error', 'fault', 'failed', 'throttle', 'rejected', 'dead letter', 'unsuccessful',
    ],
    'latency': ['latency', 'duration', 'time', 'elapsed', 'response time'],
    'requests': ['request', 'count', 'invocation', 'call', 'message', 'hit', 'miss'],
    'utilization': ['utilization', 'cpu', 'memory', 'capacity', 'usage', 'consumed'],
}


class AlarmRecommendationsTools:
    """Alarm Recommendations tools for MCP server."""

    def __init__(self):
        """Initialize the Alarm Recommendations tools."""
        pass

    def register(self, mcp):
        """Register all Alarm Recommendations tools with the MCP server."""
        mcp.tool(name='get_alarm_recommendations_for_account')(
            self.get_alarm_recommendations_for_account
        )
        mcp.tool(name='summarize_alarm_recommendations')(
            self.summarize_alarm_recommendations
        )

    @staticmethod
    def _classify_recommendation(rec: AlarmRecommendation) -> str:
        """Classify a recommendation into a metric category.

        Priority order: error_fault > latency > requests > utilization > other.
        Matching is case-insensitive against metric_name and intent.
        """
        text = f'{rec.metric_name} {rec.intent}'.lower()
        for category, keywords in _CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return 'other'

    async def get_alarm_recommendations_for_account(
        self,
        ctx: Context,
        region: Annotated[
            str | None,
            Field(
                description='AWS region to query. Defaults to AWS_REGION environment variable or us-east-1 if not set.'
            ),
        ] = None,
        profile_name: Annotated[
            str | None,
            Field(
                description='AWS CLI Profile Name to use for AWS access. Falls back to AWS_PROFILE environment variable if not specified, or uses default AWS credential chain.'
            ),
        ] = None,
    ) -> GetAlarmRecommendationsResponse:
        """Gets pre-computed alarm recommendations for the AWS account.

        Retrieves account-wide alarm recommendations from the Alarm Recommendations
        service. These are pre-computed recommendations based on the account's resources
        and best practices, unlike get_recommended_metric_alarms which computes
        recommendations locally for individual metrics.

        Usage: Use this tool to get account-level alarm recommendations. If generation
        status is IN_PROGRESS, wait and retry. If the account is not onboarded, use
        onboard_alarm_recommendations_for_account first.

        Args:
            ctx: The MCP context object for error handling and logging.
            region: AWS region. Defaults to AWS_REGION env var or us-east-1.
            profile_name: AWS CLI profile name. Falls back to AWS_PROFILE env var.

        Returns:
            GetAlarmRecommendationsResponse: Recommendations with generation status.
        """
        try:
            client = AlarmRecommendationsClient(profile_name=profile_name)
            data = client.call('GetAlarmRecommendations', {})
            return GetAlarmRecommendationsResponse.model_validate(data)
        except Exception as e:
            logger.error(f'Error in get_alarm_recommendations_for_account: {str(e)}')
            await ctx.error(f'Error getting alarm recommendations: {str(e)}')
            raise

    async def summarize_alarm_recommendations(
        self,
        ctx: Context,
        region: Annotated[
            str | None,
            Field(
                description='AWS region to query. Defaults to AWS_REGION environment variable or us-east-1 if not set.'
            ),
        ] = None,
        profile_name: Annotated[
            str | None,
            Field(
                description='AWS CLI Profile Name to use for AWS access. Falls back to AWS_PROFILE environment variable if not specified, or uses default AWS credential chain.'
            ),
        ] = None,
    ) -> SummarizeAlarmRecommendationsResponse:
        """Summarizes alarm recommendations grouped by namespace and metric category.

        Fetches account-wide alarm recommendations and classifies each into a metric
        category (error/fault, latency, requests, utilization, other), returning a
        summary grouped by namespace.

        Usage: Use this tool to get a quick overview of alarm recommendations. For the
        full list of raw recommendations, use get_alarm_recommendations_for_account.

        Args:
            ctx: The MCP context object for error handling and logging.
            region: AWS region. Defaults to AWS_REGION env var or us-east-1.
            profile_name: AWS CLI profile name. Falls back to AWS_PROFILE env var.

        Returns:
            SummarizeAlarmRecommendationsResponse: Summary grouped by namespace.
        """
        try:
            client = AlarmRecommendationsClient(profile_name=profile_name)
            data = client.call('GetAlarmRecommendations', {})
            response = GetAlarmRecommendationsResponse.model_validate(data)

            if response.generation_status != 'COMPLETED':
                return SummarizeAlarmRecommendationsResponse(
                    generation_status=response.generation_status,
                    total_recommendations=0,
                    total_namespaces=0,
                    message=response.message,
                )

            groups: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
            for rec in response.recommendations:
                category = self._classify_recommendation(rec)
                groups[rec.namespace][category] += 1

            namespaces = [
                NamespaceSummary(
                    namespace=ns,
                    total=sum(counts.values()),
                    **counts,
                )
                for ns, counts in sorted(groups.items())
            ]

            return SummarizeAlarmRecommendationsResponse(
                generation_status=response.generation_status,
                total_recommendations=sum(ns.total for ns in namespaces),
                total_namespaces=len(namespaces),
                namespaces=namespaces,
            )
        except Exception as e:
            logger.error(f'Error in summarize_alarm_recommendations: {str(e)}')
            await ctx.error(f'Error summarizing alarm recommendations: {str(e)}')
            raise
