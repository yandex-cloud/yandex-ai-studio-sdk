from __future__ import annotations

from typing import Any

import pytest

from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._speechkit.speech_to_text.structures import (
    EndOfUtteranceClassifier, EndOfUtteranceSensitivity, LLMPostProcessing, LLMPostProcessingInstruction,
    ProtoDefaultEouClassifier, ProtoRecognitionClassifier, ProtoSpeechAnalysisOptions, ProtoSummarizationOptions,
    ProtoTextNormalizationOptions, RecognitionClassifier, RecognitionTriggerType, SpeechAnalysis, SummarizationProperty,
    TextNormalization, WellKnownRecognitionClassifiers
)
from yandex_ai_studio_sdk._types.misc import UNDEFINED


def test_text_normalization(async_sdk: AsyncAIStudio) -> None:
    assert TextNormalization() == TextNormalization(
        phone_formatting=UNDEFINED,
        profanity_filter=UNDEFINED,
        literature_text=UNDEFINED
    )

    enabled = ProtoTextNormalizationOptions.TextNormalization.TEXT_NORMALIZATION_ENABLED
    assert TextNormalization()._to_proto(async_sdk) == ProtoTextNormalizationOptions(
        text_normalization=enabled
    )

    assert TextNormalization(phone_formatting=True)._to_proto(async_sdk) == ProtoTextNormalizationOptions(
        text_normalization=enabled
    )
    assert TextNormalization(phone_formatting=False)._to_proto(async_sdk) == ProtoTextNormalizationOptions(
        text_normalization=enabled,
        phone_formatting_mode=ProtoTextNormalizationOptions.PhoneFormattingMode.PHONE_FORMATTING_MODE_DISABLED
    )

    for field in ('profanity_filter', 'literature_text'):
        for value in (True, False):
            obj = TextNormalization(**{field: value})
            proto = obj._to_proto(async_sdk)
            obj_value = getattr(obj, field)
            proto_value = getattr(proto, field)
            assert value == proto_value == obj_value


def test_end_of_utterance_classifier(async_sdk: AsyncAIStudio) -> None:
    assert EndOfUtteranceClassifier() == EndOfUtteranceClassifier(
        sensitivity=UNDEFINED,
        max_pause_between_words_hint_ms=UNDEFINED
    )

    assert EndOfUtteranceClassifier(
        max_pause_between_words_hint_ms=10
    )._to_proto(async_sdk) == ProtoDefaultEouClassifier(
        max_pause_between_words_hint_ms=10
    )

    for value, etalon in (
        ('default', EndOfUtteranceSensitivity.DEFAULT),
        ('DEFAULT', EndOfUtteranceSensitivity.DEFAULT),
        (EndOfUtteranceSensitivity.DEFAULT, EndOfUtteranceSensitivity.DEFAULT),
        ('high', EndOfUtteranceSensitivity.HIGH),
        ('HIGH', EndOfUtteranceSensitivity.HIGH),
        (EndOfUtteranceSensitivity.HIGH, EndOfUtteranceSensitivity.HIGH),
    ):
        obj = EndOfUtteranceClassifier(sensitivity=value)

        assert obj.sensitivity == etalon
        assert obj._to_proto(async_sdk).type == etalon

    with pytest.raises(TypeError):
        EndOfUtteranceClassifier(sensitivity={})  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        EndOfUtteranceClassifier(sensitivity='foo')


def test_recognition_classifier(async_sdk: AsyncAIStudio) -> None:
    enum = ProtoRecognitionClassifier.TriggerType
    assert RecognitionClassifier(
        name='foo', triggers='on_final'
    )._to_proto(async_sdk) == ProtoRecognitionClassifier(
        classifier='foo',
        triggers=[enum.ON_FINAL]
    )
    assert RecognitionClassifier(
        name='foo', triggers=['on_final', 'ON_PARTIAL', RecognitionTriggerType.ON_UTTERANCE]
    )._to_proto(async_sdk) == ProtoRecognitionClassifier(
        classifier='foo',
        triggers=[enum.ON_FINAL, enum.ON_PARTIAL, enum.ON_UTTERANCE]
    )

    for trigger_type, enum_value in (
        ('on_final', RecognitionTriggerType.ON_FINAL),
        ('on_utterance', RecognitionTriggerType.ON_UTTERANCE),
        ('on_partial', RecognitionTriggerType.ON_PARTIAL),
        ('ON_PARTIAL', RecognitionTriggerType.ON_PARTIAL),
    ):
        simple_constructor = getattr(RecognitionClassifier, trigger_type.lower())
        assert RecognitionClassifier('foo', enum_value) == \
            RecognitionClassifier('foo', [enum_value]) == \
            simple_constructor('foo') == \
            RecognitionClassifier('foo', trigger_type) == \
            RecognitionClassifier('foo', [trigger_type])

    bad_trigger_type: Any
    exc_type: type[Exception] | tuple[type[Exception], ...]
    for bad_trigger_type, exc_type in (
        (..., TypeError),
        ({}, (TypeError, ValueError)),
        ('bar', ValueError),
        (15, ValueError)
    ):
        with pytest.raises(exc_type):
            RecognitionClassifier('foo', bad_trigger_type)

        with pytest.raises(exc_type):
            RecognitionClassifier('foo', [bad_trigger_type])

    assert WellKnownRecognitionClassifiers == RecognitionClassifier.WellKnown


def test_speech_analysis(async_sdk: AsyncAIStudio) -> None:
    for field, proto_field, value in (
        ('speaker_analysis', 'enable_speaker_analysis', True),
        ('conversation_analysis', 'enable_conversation_analysis', True),
        ('descriptive_statistics_quantiles', 'descriptive_statistics_quantiles', (123,)),
        ('descriptive_statistics_quantiles', 'descriptive_statistics_quantiles', [123]),
    ):
        kwargs: dict[str, Any] = {
            'speaker_analysis': UNDEFINED,
            'conversation_analysis': UNDEFINED,
            'descriptive_statistics_quantiles': UNDEFINED
        }
        kwargs[field] = value

        assert SpeechAnalysis(**{field: value}) == SpeechAnalysis(**kwargs)  # type: ignore[arg-type]
        assert SpeechAnalysis(
            **{field: value}  # type: ignore[arg-type]
        )._to_proto(async_sdk) == ProtoSpeechAnalysisOptions(
            **{proto_field: value}  # type: ignore[arg-type]
        )


def test_llm_post_processing(async_sdk: AsyncAIStudio, folder_id: str) -> None:
    post_processor = LLMPostProcessing('some_model')
    assert post_processor == LLMPostProcessing(
        model_name='some_model',
        model_version='latest',
        instructions=(),
    )
    with pytest.raises(ValueError):
        post_processor._to_proto(async_sdk)

    post_processor = post_processor.with_instruction('foo')
    assert post_processor == LLMPostProcessing(
        model_name='some_model',
        model_version='latest',
        instructions=(LLMPostProcessingInstruction(instruction='foo', response_format=None),),
    )

    proto_obj = post_processor._to_proto(async_sdk)
    assert proto_obj == ProtoSummarizationOptions(
        model_uri=f'gpt://{folder_id}/some_model/latest',
        properties=[SummarizationProperty(
            instruction='foo',
            json_object=False,
            json_schema=None,
        )]
    )

    post_processor = post_processor.with_instruction('bar', response_format='json')
    properties = post_processor._to_proto(async_sdk).properties
    assert len(properties) == 2
    assert properties[1] == SummarizationProperty(
        instruction='bar',
        json_object=True,
        json_schema=None
    )

    post_processor = post_processor.with_instruction('baz', response_format={'json_schema': {'anykey': True}})
    properties = post_processor._to_proto(async_sdk).properties
    assert len(properties) == 3
    assert properties[2] == SummarizationProperty(
        instruction='baz',
        json_object=None,  # type: ignore[arg-type]
        json_schema={'schema': {'anykey': True}}  # type: ignore[arg-type]
    )
