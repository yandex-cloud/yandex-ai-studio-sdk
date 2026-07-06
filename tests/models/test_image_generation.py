from __future__ import annotations

import pytest

from yandex_ai_studio_sdk._models.completions.result import Alternative, GPTModelResult
from yandex_ai_studio_sdk._models.image_generation.message import (
    AnyMessage, ImageMessage, ProtoMessage, messages_to_proto
)
from yandex_ai_studio_sdk._types.message import TextMessage


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.models.image_generation('yandex-art')


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_run(model):
    operation = await model.run_deferred(['hello'])
    print(operation.id)
    result = await operation

    assert len(result.image_bytes) > 4

    assert result._repr_jpeg_() == result.image_bytes  # pylint: disable=protected-access


def test_inputs():
    def check_messages(messages, expected):
        assert len(messages) == len(expected)
        for message, expected_message in zip(messages, expected):
            assert isinstance(message, ProtoMessage)
            assert message.text == expected_message

    messages = messages_to_proto('text')
    check_messages(messages, ['text'])

    messages = messages_to_proto(['foo', 'bar'])
    check_messages(messages, ['foo', 'bar'])

    messages = messages_to_proto({'text': 'text', 'weight': 2})
    check_messages(messages, ['text'])
    assert messages[0].weight == 2

    messages = messages_to_proto([{'text': 'foo'}, {'text': 'bar'}])
    check_messages(messages, ['foo', 'bar'])
    assert messages[0].weight == 0

    messages = messages_to_proto(ImageMessage(text='bar'))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 0

    messages = messages_to_proto(ImageMessage(text='bar', weight=2))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 2

    messages = messages_to_proto([
        ImageMessage(text='bar', weight=2),
        ImageMessage(text='foo', weight=1)
    ])
    check_messages(messages, ['bar', 'foo'])
    assert messages[0].weight == 2
    assert messages[1].weight == 1

    messages = messages_to_proto(Alternative(role='foo', text='bar', status=None, tool_calls=None))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 0

    messages = messages_to_proto(TextMessage(role='foo', text='bar'))
    check_messages(messages, ['bar'])
    assert messages[0].weight == 0

    gpt_model_result = GPTModelResult(
        alternatives=[
            Alternative(role='1', text='1', status=None, tool_calls=None),
            Alternative(role='2', text='2', status=None, tool_calls=None),
        ],
        usage=None,
        model_version=''
    )
    messages = messages_to_proto(gpt_model_result)
    check_messages(messages, ['1'])

    # Test AnyMessage protocol — any object with a .text property should work
    class _AnyMessageImpl:
        def __init__(self, text: str) -> None:
            self._text = text

        @property
        def text(self) -> str:
            return self._text

    assert isinstance(_AnyMessageImpl('x'), AnyMessage)

    any_msg1 = _AnyMessageImpl('a\nb')
    messages = messages_to_proto(any_msg1)
    check_messages(messages, ['a\nb'])

    any_msg2 = _AnyMessageImpl('y\nz')
    messages = messages_to_proto(any_msg2)
    check_messages(messages, ['y\nz'])

    messages = messages_to_proto(['foo', {'text': 'bar'}, *gpt_model_result, any_msg1, any_msg2])
    check_messages(messages, ['foo', 'bar', '1', '2', 'a\nb', 'y\nz'])

    with pytest.raises(TypeError):
        messages_to_proto(1)

    with pytest.raises(TypeError):
        messages_to_proto({})
