"""LangChain integration for Yandex AI Studio Chat API.

This module is optional: requires ``langchain_core`` to be installed.
Provides :class:`ChatYandexGPT` — a LangChain ``BaseChatModel`` adapter
that uses the Chat API backend.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from typing import Any

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel as LCBaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from yandex_ai_studio_sdk._tools.tool import FunctionTool
from yandex_ai_studio_sdk._types.langchain import BaseYandexLanguageModel
from yandex_ai_studio_sdk._types.misc import UNDEFINED
from yandex_ai_studio_sdk._utils.langchain import make_async_run_manager
from yandex_ai_studio_sdk._utils.sync import run_sync_generator_impl, run_sync_impl

from .model import BaseChatModel as ChatAPIModel
from .result import ChatChoice, ChatModelResult, DeltaChatChoice

# =========================================================================
# Message conversion: LangChain → Chat API
# =========================================================================


def _transform_messages(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    """Convert LangChain messages to Chat API dict format."""
    result: list[dict[str, Any]] = []

    for message in messages:
        if isinstance(message, ToolMessage):
            result.append({
                "role": "tool",
                "content": str(message.content),
                "tool_call_id": message.tool_call_id,
            })

        elif isinstance(message, AIMessage) and message.tool_calls:
            result.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(
                                tc["args"], ensure_ascii=False,
                            ),
                        },
                    }
                    for tc in message.tool_calls
                ],
            })

        elif isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, list):
                # Multimodal: list of content parts
                result.append({"role": "user", "content": content})
            else:
                result.append({"role": "user", "content": str(content)})

        elif isinstance(message, AIMessage):
            result.append({"role": "assistant", "content": str(message.content)})

        elif isinstance(message, SystemMessage):
            result.append({"role": "system", "content": str(message.content)})

    return result


# =========================================================================
# Tool conversion: LangChain → Yandex FunctionTool
# =========================================================================


def _lc_tool_to_function_tool(tool: Any) -> FunctionTool:
    """Convert a LangChain-compatible tool to a Yandex FunctionTool."""
    openai_tool = convert_to_openai_tool(tool)
    fn = openai_tool["function"]
    return FunctionTool(
        name=fn["name"],
        description=fn.get("description"),
        parameters=fn.get("parameters", {}),
        strict=fn.get("strict"),
    )


# =========================================================================
# Response parsing: Chat API → LangChain
# =========================================================================


def _parse_tool_calls(choice: ChatChoice) -> list[dict[str, Any]]:
    """Extract tool calls from ChatChoice into LangChain format."""
    if not choice.tool_calls:
        return []

    return [
        {
            "id": tc.id or "",
            "name": tc.function.name,
            "args": tc.function.arguments,
            "type": "tool_call",
        }
        for tc in choice.tool_calls
        if tc.function  # skip malformed tool calls
    ]


def _make_usage(result: ChatModelResult) -> UsageMetadata | None:
    """Build LangChain UsageMetadata from Chat API usage stats."""
    if not result.usage:
        return None
    return UsageMetadata(
        input_tokens=result.usage.input_text_tokens,
        output_tokens=result.usage.completion_tokens,
        total_tokens=result.usage.total_tokens,
    )


# =========================================================================
# ChatYandexGPT — LangChain adapter for Chat API
# =========================================================================


class ChatYandexGPT(BaseYandexLanguageModel[ChatAPIModel], LCBaseChatModel):
    """LangChain chat model for Yandex GPT via Chat API.

    Supports text, tool calls, tool results, multimodal content, and streaming.

    Example:
        >>> sdk = AIStudio()
        >>> model = sdk.chat.completions('yandexgpt').langchain()
        >>> result = model.invoke([HumanMessage("Hello!")])
    """

    class Config:
        arbitrary_types_allowed = True

    @property
    def _sdk(self):
        return self.ycmlsdk_model._sdk

    # -----------------------------------------------------------------
    # Sync → async delegation (same pattern as legacy ChatYandexGPT)
    # -----------------------------------------------------------------

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        async_rm = make_async_run_manager(run_manager) if run_manager else None
        return run_sync_impl(
            self._agenerate(messages, stop, async_rm, **kwargs),
            self._sdk,
        )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        async_rm = make_async_run_manager(run_manager) if run_manager else None
        return run_sync_generator_impl(
            self._astream(messages, stop, async_rm, **kwargs),
            self._sdk,
        )

    # -----------------------------------------------------------------
    # Core: invoke
    # -----------------------------------------------------------------

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        chat_messages = _transform_messages(messages)

        sdk_result: ChatModelResult = await self.ycmlsdk_model._run(
            messages=chat_messages,
            timeout=self.timeout,
        )

        usage = _make_usage(sdk_result)

        generations: list[ChatGeneration] = []
        for choice in sdk_result.choices:
            tool_calls = _parse_tool_calls(choice)

            ai_message = AIMessage(
                content=choice.text or "",
                tool_calls=tool_calls or [],
                usage_metadata=usage,
                response_metadata={
                    "finish_reason": choice.finish_reason.value,
                    "model": sdk_result.model,
                    "status": choice.status.name,
                },
            )
            generations.append(ChatGeneration(message=ai_message))

        return ChatResult(
            generations=generations,
            llm_output={"model": sdk_result.model, "id": sdk_result.id},
        )

    # -----------------------------------------------------------------
    # Core: stream
    # -----------------------------------------------------------------

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        chat_messages = _transform_messages(messages)

        async for sdk_result in self.ycmlsdk_model._run_stream(
            messages=chat_messages,
            timeout=self.timeout,
        ):
            choice = sdk_result.choices[0]
            usage = _make_usage(sdk_result)

            delta = choice.delta if isinstance(choice, DeltaChatChoice) else choice.text
            tool_calls = _parse_tool_calls(choice)

            # tool_call_chunks: args as JSON string (LangChain convention)
            tool_call_chunks = [
                {
                    "id": tc["id"],
                    "name": tc["name"],
                    "args": json.dumps(tc["args"], ensure_ascii=False),
                    "index": i,
                    "type": "tool_call_chunk",
                }
                for i, tc in enumerate(tool_calls)
            ] if tool_calls else []

            chunk = AIMessageChunk(
                content=delta or "",
                tool_call_chunks=tool_call_chunks,
                usage_metadata=usage,
                response_metadata={
                    "finish_reason": choice.finish_reason.value,
                    "status": choice.status.name,
                },
            )
            yield ChatGenerationChunk(message=chunk)

    # -----------------------------------------------------------------
    # Tool binding
    # -----------------------------------------------------------------

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | Any],
        *,
        tool_choice: str | dict[str, Any] | bool | None = None,
        **kwargs: Any,
    ) -> "ChatYandexGPT":
        """Bind tools to this model, returning a new configured instance.

        :param tools: LangChain-compatible tools: dicts (OpenAI schema),
            Pydantic models, callables, or BaseTool instances.
        :param tool_choice: Strategy for tool selection.
            ``True`` / ``"any"`` → ``"required"``.
            ``False`` → ``"none"``.
            A tool name string selects a specific tool.
        :returns: New :class:`ChatYandexGPT` with the tools configured.
        """
        yandex_tools = [_lc_tool_to_function_tool(t) for t in tools]

        if tool_choice is None:
            yandex_tool_choice = UNDEFINED
        elif isinstance(tool_choice, bool):
            yandex_tool_choice = "required" if tool_choice else "none"
        elif tool_choice == "any":
            yandex_tool_choice = "required"
        else:
            yandex_tool_choice = tool_choice

        configured = self.ycmlsdk_model.configure(
            tools=yandex_tools,
            tool_choice=yandex_tool_choice,
        )
        return self.__class__(ycmlsdk_model=configured, timeout=self.timeout)


ChatYandexGPT.model_rebuild()
