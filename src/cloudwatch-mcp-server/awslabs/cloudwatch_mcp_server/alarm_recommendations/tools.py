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
    GetAlarmRecommendationsResponse,
)
from loguru import logger
from mcp.server.fastmcp import Context
from pydantic import Field
from typing import Annotated


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
