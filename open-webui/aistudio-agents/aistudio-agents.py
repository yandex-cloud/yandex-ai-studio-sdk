"""
title: Yandex Cloud AI Assistant Integration for OpenWebUI
version: 0.1.0
description: Integration with Yandex Cloud AI Agents using Conversations API with real-time status and streaming
author: https://github.com/vhaldemar
license: MIT
"""

from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import TypeGuard, TypeVar

from open_webui.env import VERSION as OPEN_WEBUI_VERSION
from open_webui.routers.openai import convert_to_responses_payload
from openai import AsyncOpenAI
from openai.types.realtime.response_text_delta_event import ResponseTextDeltaEvent
from pydantic import BaseModel, Field

EventEmitterType = Callable[[dict], Awaitable[None]]
T = TypeVar("T")

THIS_PIPE_VERSION = "0.1.0"
PIPE_ORIGIN = (
    "https://github.com/yandex-cloud/yandex-ai-studio-sdk/tree/master/open-webui"
)
TICKETS_URL = "https://github.com/yandex-cloud/yandex-ai-studio-sdk/issues"
LAST_TESTED_WEBUI_VERSION = "0.8.12"

STATUS_NAMES = {
    # Web Search
    "response.web_search_call.in_progress": "Searching the web..",
    "response.web_search_call.searching": "Searching the web...",
    "response.web_search_call.completed": "Search complete, analyzing results...",
    # MCP
    "response.mcp_list_tools.in_progress": "Connecting tools...",
    "response.mcp_list_tools.completed": "Tools connected",
    "response.mcp_call.in_progress": "Calling tool...",
    "response.mcp_call.completed": "Tool executed, generating response...",
    # File Search
    "response.file_search_call.in_progress": "Searching documents...",
    "response.file_search_call.searching": "Searching documents...",
    "response.file_search_call.completed": "Documents found, analyzing...",
    # Code Interpreter
    "response.code_interpreter_call.in_progress": "Executing code...",
    "response.code_interpreter_call.interpreting": "Executing code...",
    "response.code_interpreter_call.completed": "Code executed",
    # Response Lifecycle
    "response.created": "Creating response...",
    "response.in_progress": "Generating response...",
    "response.completed": "Response complete",
    "response.failed": "Response failed",
    "response.cancelled": "Response cancelled",
    "response.incomplete": "Response incomplete",
    # Output Item
    "response.output_item.added": "Processing output...",
    "response.output_item.done": "Output ready",
    # Text
    "response.output_text.delta": "Streaming text...",
    "response.output_text.done": "Text complete",
    "response.output_text.annotation.added": "Adding annotation...",
    # Reasoning
    "response.reasoning.delta": "Thinking...",
    "response.reasoning.done": "Reasoning complete",
    "response.reasoning_summary.delta": "Summarizing reasoning...",
    "response.reasoning_summary.done": "Reasoning summary complete",
    # Content Part
    "response.content_part.added": "Adding content...",
    "response.content_part.done": "Content part complete",
    # Function Call
    "response.function_call_arguments.delta": "Preparing tool call...",
    "response.function_call_arguments.done": "Tool call ready",
    # Image Generation
    "response.image_generation_call.in_progress": "Generating image...",
    "response.image_generation_call.generating": "Generating image...",
    "response.image_generation_call.partial_image": "Image rendering...",
    "response.image_generation_call.completed": "Image generated",
    # Rate Limits / Usage
    "rate_limit_updated": "Rate limit updated",
    "response.refusal.delta": "Generating refusal...",
    "response.refusal.done": "Refusal complete",
    # Errors
    "error": "Error occurred",
}


class Pipe:
    class Valves(BaseModel):
        YANDEX_CLOUD_API_KEY: str = Field(
            default="",
            description=(
                "Yandex Cloud API key, "
                "more on the topic at https://aistudio.yandex.ru/docs/ai-studio/operations/get-api-key.html"
            ),
            json_schema_extra={"input": {"type": "password"}},
        )

        YANDEX_CLOUD_FOLDER_ID: str = Field(
            default="",
            description="Yandex Cloud folder ID (e.g. b1grc91ju8et9rl2b8jg)",
        )

        AGENT_IDS: list[str] = Field(
            default_factory=list,
            description=(
                "Agents IDs from Yandex AI Studio, "
                'for example: "fvt210rlb66c, fvtp4kvcgiu36u"'
            ),
        )

        AGENT_NAMES: list[str] = Field(
            default_factory=list,
            description=(
                "Agent names to show in OpenWebUI instead of IDs; "
                "number and order of names must match IDs number and order"
            ),
        )

        AI_STUDIO_BASE_URL: str = Field(
            default="https://ai.api.cloud.yandex.net/v1",
            description="Yandex AI Studio API base URL",
        )

        MODEL_PREFIX: str = Field(
            default="",
            description="Optional prefix for model names in Open WebUI (e.g. 'Yandex: ')",
        )

        REQUEST_TIMEOUT: int = Field(
            default=90,
            description="Timeout for API requests in seconds",
            gt=0,
        )

    def __init__(self):
        self.valves = self.Valves()

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self.valves.YANDEX_CLOUD_API_KEY,
            base_url=self.valves.AI_STUDIO_BASE_URL,
            project=self.valves.YANDEX_CLOUD_FOLDER_ID,
            timeout=self.valves.REQUEST_TIMEOUT,
        )

    def get_agent_name(self, agent_id: str) -> str:
        prefix = self.valves.MODEL_PREFIX
        name = self.agent_names.get(agent_id, f"Agent {agent_id}")
        return f"{prefix}{name}"

    @property
    def agent_names(self) -> dict[str, str]:
        ids = self.valves.AGENT_IDS
        names = self.valves.AGENT_NAMES
        return dict(zip(ids, names))

    def pipes(self) -> list[dict]:
        # TODO: Validate existence of agent ids or
        # add auto listing from backend
        try:
            self._validate_configuration()
        except ValueError as e:
            return [
                {
                    "id": "configuration_error",
                    "name": f"Configuration error: {e}",
                }
            ]

        models = []

        for agent_id in self.valves.AGENT_IDS:
            model_id = f"gpt://{self.valves.YANDEX_CLOUD_FOLDER_ID}/{agent_id}"
            name = self.get_agent_name(agent_id)
            models.append({"id": model_id, "name": name})

        return models

    def _assert_not_none(self, value: T | None, message: str) -> TypeGuard[T]:
        if value is not None:
            return True

        raise RuntimeError(
            f"assertion error {message!r}, {LAST_TESTED_WEBUI_VERSION=}, "
            f"{OPEN_WEBUI_VERSION=}, {THIS_PIPE_VERSION=}, "
            f"please, try to update plugin from {PIPE_ORIGIN} "
            f"or create a ticket at {TICKETS_URL}"
        )

    async def _emit_status(
        self, emitter: EventEmitterType, description: str, done: bool = False
    ):
        await emitter(
            {
                "type": "status",
                "data": {"description": description, "done": done},
            }
        )

    async def _emit_event_stub(self, data: dict) -> None:
        pass

    async def pipe(
        self,
        body: dict,
        __event_emitter__: EventEmitterType | None = None,
    ) -> AsyncGenerator[str]:
        event_emitter = __event_emitter__ or self._emit_event_stub

        # open-webui doing smth with body after calling a pipe,
        # but convert_to_responses_payload modifies it
        body = copy.deepcopy(body)
        responses_kwargs = convert_to_responses_payload(body)
        responses_kwargs.pop("stream", None)

        raw_model_id = body.get("model")
        if not self._assert_not_none(raw_model_id, "model_id not None"):
            return
        model_id = raw_model_id.split(".", 1)[-1]
        assistant_id = model_id.rsplit("/", 1)[-1]

        responses_kwargs["model"] = model_id

        last_event_type: str | None = None

        client = self._get_client()

        async with client:
            async with client.responses.stream(
                prompt={"id": assistant_id}, **responses_kwargs
            ) as stream:
                async for event in stream:
                    if event.type == "response.output_text.delta":
                        assert isinstance(event, ResponseTextDeltaEvent)
                        yield event.delta

                    if event.type != last_event_type:
                        last_event_type = event.type
                        status_name = STATUS_NAMES.get(event.type, event.type)
                        await self._emit_status(
                            event_emitter,
                            status_name,
                            event.type == "response.completed",
                        )

        return

    def _validate_configuration(self) -> None:
        if not self.valves.YANDEX_CLOUD_API_KEY.strip():
            raise ValueError("Yandex Cloud API Key is required")

        if not self.valves.YANDEX_CLOUD_FOLDER_ID.strip():
            raise ValueError("Yandex Cloud Folder ID is required")

        ids = self.valves.AGENT_IDS
        if not ids:
            raise ValueError("Add at least one agent ID into Agent Ids Valve")

        names = self.valves.AGENT_NAMES
        if names and len(names) != len(ids):
            raise ValueError("Number of Agent names must match number of Agent Ids")
