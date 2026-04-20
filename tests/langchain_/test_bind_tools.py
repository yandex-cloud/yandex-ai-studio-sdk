"""Unit tests for ChatYandexGPT.bind_tools()."""
from __future__ import annotations

import pytest
from yandex_ai_studio_sdk._tools.tool import FunctionTool

pytestmark = [pytest.mark.require_env('langchain_core')]

_WEATHER_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.chat.completions('yandexgpt').langchain()


def test_bind_tools_returns_new_instance(model):
    bound = model.bind_tools([_WEATHER_TOOL])
    assert bound is not model


def test_bind_tools_configures_tools(model):
    bound = model.bind_tools([_WEATHER_TOOL])
    config = bound.ycmlsdk_model._config
    assert config.tools is not None
    assert len(config.tools) == 1
    assert isinstance(config.tools[0], FunctionTool)
    assert config.tools[0].name == "get_weather"
    assert config.tools[0].description == "Get the current weather"


def test_bind_tools_no_tool_choice_by_default(model):
    bound = model.bind_tools([_WEATHER_TOOL])
    assert bound.ycmlsdk_model._config.tool_choice is None


def test_bind_tools_tool_choice_true_maps_to_required(model):
    bound = model.bind_tools([_WEATHER_TOOL], tool_choice=True)
    assert bound.ycmlsdk_model._config.tool_choice == "required"


def test_bind_tools_tool_choice_any_maps_to_required(model):
    bound = model.bind_tools([_WEATHER_TOOL], tool_choice="any")
    assert bound.ycmlsdk_model._config.tool_choice == "required"


def test_bind_tools_tool_choice_false_maps_to_none(model):
    bound = model.bind_tools([_WEATHER_TOOL], tool_choice=False)
    assert bound.ycmlsdk_model._config.tool_choice == "none"
