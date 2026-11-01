"""LLM provider: a narrow chat-with-tools interface, implemented over the AWS Bedrock Converse API."""

import os
from typing import Any, Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_MODEL_ID = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEFAULT_REGION = "eu-west-1"


class ProviderError(Exception):
    """The LLM provider could not produce a response."""


class ChatProvider(Protocol):
    def converse(
        self, system: str, messages: list[dict[str, Any]], tool_specs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """One model turn. Returns the assistant message: text, toolUse blocks, or both."""
        ...


class BedrockProvider:
    """Model ID from BEDROCK_MODEL_ID, region from AWS_REGION; credentials from the standard AWS chain."""

    def __init__(self, client: Any = None) -> None:
        self.model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
        self.region = os.environ.get("AWS_REGION", DEFAULT_REGION)
        self._client = client

    def _bedrock(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                config=Config(read_timeout=30, connect_timeout=5, retries={"max_attempts": 2, "mode": "standard"}),
            )
        return self._client

    def converse(
        self, system: str, messages: list[dict[str, Any]], tool_specs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            response = self._bedrock().converse(
                modelId=self.model_id,
                system=[{"text": system}],
                messages=messages,
                toolConfig={"tools": [{"toolSpec": spec} for spec in tool_specs], "toolChoice": {"auto": {}}},
                inferenceConfig={"maxTokens": 4096, "temperature": 0},
            )
        except (ClientError, BotoCoreError) as error:
            raise ProviderError(f"Bedrock Converse failed ({self.model_id}, {self.region}): {error}") from error
        return response["output"]["message"]
