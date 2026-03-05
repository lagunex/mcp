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

"""SigV4-signed HTTP client for the Alarm Recommendations API."""

import json
from boto3 import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from os import getenv
from urllib.request import Request, urlopen


BASE_URL = getenv('ALARM_RECOMMENDATIONS_BASE_URL')
if not BASE_URL:
    raise ValueError('ALARM_RECOMMENDATIONS_BASE_URL environment variable must be set')
SIGNING_SERVICE = 'awsalarmkorerecommendations'
SIGNING_REGION = getenv('ALARM_RECOMMENDATIONS_SIGNING_REGION', 'us-east-1')


class AlarmRecommendationsClient:
    """HTTP client that signs requests with SigV4 for the Alarm Recommendations API."""

    def __init__(self, profile_name: str | None = None):
        """Initialize the client with AWS credentials.

        Args:
            profile_name: AWS CLI profile name. Falls back to AWS_PROFILE env var.
        """
        if profile_name is None:
            profile_name = getenv('AWS_PROFILE', None)

        if profile_name:
            self._session = Session(profile_name=profile_name)
        else:
            self._session = Session()

    def call(self, operation: str, body: dict) -> dict:
        """Send a signed POST request to the recommendations API.

        Args:
            operation: API operation name (e.g., 'GetAlarmRecommendations').
            body: JSON request body.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            Exception: On HTTP errors with status code and response body.
        """
        url = f'{BASE_URL}/{operation}'
        data = json.dumps(body).encode()

        creds = self._session.get_credentials().get_frozen_credentials()
        aws_request = AWSRequest(
            method='POST',
            url=url,
            data=data,
            headers={
                'Content-Type': 'application/json',
            },
        )
        SigV4Auth(creds, SIGNING_SERVICE, SIGNING_REGION).add_auth(aws_request)

        request = Request(url, data=data, method='POST')
        for key, val in dict(aws_request.headers).items():
            request.add_header(key, val)

        try:
            with urlopen(request) as response:
                return json.loads(response.read())
        except Exception as e:
            raise Exception(f'Alarm Recommendations API error ({operation}): {e}') from e
