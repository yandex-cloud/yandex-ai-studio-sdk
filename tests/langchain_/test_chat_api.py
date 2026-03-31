"""Tests for LangChain integration via Chat API."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.vcr, pytest.mark.require_env('langchain_core')]


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.chat.completions('yandexgpt').langchain()


@pytest.fixture(name='chat_history')
def fixture_chat_history():
    from langchain_core.messages import AIMessage, HumanMessage  # pylint: disable=import-outside-toplevel,import-error

    return [
        HumanMessage(content="hello!"),
        AIMessage(content="Hi there human!"),
        HumanMessage(content="Meow!"),
    ]


async def test_ainvoke(model, chat_history):
    result = await model.ainvoke(chat_history)

    assert result.content
    assert result.usage_metadata is not None
    assert result.usage_metadata.total_tokens > 0
    assert "finish_reason" in result.response_metadata
    assert "model" in result.response_metadata


async def test_astream(model, chat_history):
    chunks = [chunk async for chunk in model.astream(chat_history)]

    assert len(chunks) > 0
    assert any(c.content for c in chunks)
