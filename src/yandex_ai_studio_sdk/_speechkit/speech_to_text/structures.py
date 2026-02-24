# pylint: disable=unused-argument
from __future__ import annotations

from abc import abstractmethod
import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable, Sequence
from typing import Any, cast
from enum import StrEnum, auto
from typing_extensions import Self

# pylint: disable=no-name-in-module
from yandex.cloud.ai.stt.v3.stt_pb2 import (
    SummarizationProperty,
    TextNormalizationOptions as ProtoTextNormalizationOptions,
    DefaultEouClassifier as ProtoDefaultEouClassifier,
    RecognitionClassifier as ProtoRecognitionClassifier,
    SpeechAnalysisOptions as ProtoSpeechAnalysisOptions,
    SummarizationOptions as ProtoSummarizationOptions,
)

from yandex_ai_studio_sdk._utils.proto import proto_to_dict
from yandex_ai_studio_sdk._types.proto import ProtoBased, SDKType, ProtoMessageTypeT
from yandex_ai_studio_sdk._types.misc import UndefinedOr, UNDEFINED, get_defined_value, is_defined
from yandex_ai_studio_sdk._types.schemas import ResponseType, make_response_format_kwargs
from yandex_ai_studio_sdk._types.enum import (
    EnumWithUnknownAlias, ProtoBasedEnum, UndefinedOrEnumWithUnknownInput,
    EnumWithUnknownInput
)


class ProtoBasedWithBoolDefault(ProtoBased[ProtoMessageTypeT]):
    @abstractmethod
    def _to_proto(self, sdk: SDKType) -> ProtoMessageTypeT:
        pass

    @classmethod
    def _coerce(cls, value: Self | bool) -> Self | None:
        if isinstance(value, cls):
            return value

        if not isinstance(value, bool):
            name = cls.__name__
            raise TypeError(f"Value passed for {name} could be only isinstance of {name} or bool value")

        return cls()


@dataclass(frozen=True)
class TextNormalization(ProtoBasedWithBoolDefault[ProtoTextNormalizationOptions]):
    """Class which encapsulates `text normaliztion options <https://yandex.cloud/docs/speechkit/stt/normalization>`_.

    Usage of object of this class itself in speech to text configuration is turning on normalization.
    Options of this class have different defaults at backend, i.e. some options could turn on the feature
    and others could turn it off.

    >> TextNormalization()
    TextNormalization()

    >>> TextNormalization(phone_formatting=False)
    TextNormalization(phone_formatting=False, profanity_filter=Undefined, literature_text=Undefined)
    """

    #: Phone formatting
    phone_formatting: UndefinedOr[bool] = UNDEFINED
    #: Profanity filter
    profanity_filter: UndefinedOr[bool] = UNDEFINED
    #: Rewrite text in literature style
    literature_text: UndefinedOr[bool] = UNDEFINED

    @classmethod
    def _from_proto(cls, proto: ProtoTextNormalizationOptions, sdk: SDKType) -> Self:
        kwargs: dict[str, bool] = {}

        if proto.HasField('literature_text'):
            kwargs['literature_text'] = proto.literature_text
        if proto.HasField('profanity_filter'):
            kwargs['profanity_filter'] = proto.profanity_filter

        if proto.HasField('phone_formatting_mode'):
            kwargs['phone_formatting'] = (
                proto.phone_formatting_mode == ProtoTextNormalizationOptions.PhoneFormattingMode.PHONE_FORMATTING_MODE_DISABLED
            )

        return cls(**kwargs)

    def _to_proto(self, sdk: SDKType) -> ProtoTextNormalizationOptions:
        phone_formatting: bool | None = get_defined_value(self.phone_formatting, None)
        phone_formatting_proto: int = (
            ProtoTextNormalizationOptions.PhoneFormattingMode.PHONE_FORMATTING_MODE_UNSPECIFIED
        )
        if phone_formatting is False:
            phone_formatting_proto = ProtoTextNormalizationOptions.PhoneFormattingMode.PHONE_FORMATTING_MODE_DISABLED

        result = ProtoTextNormalizationOptions(
            text_normalization=ProtoTextNormalizationOptions.TextNormalization.TEXT_NORMALIZATION_ENABLED,
            phone_formatting_mode=phone_formatting_proto,  # type: ignore[arg-type]
        )
        if is_defined(self.literature_text):
            result.literature_text = self.literature_text

        if is_defined(self.profanity_filter):
            result.profanity_filter = self.profanity_filter

        return result


# pylint: disable-next=invalid-enum-extension
class EndOfUtteranceSensetivity(ProtoBasedEnum):
    """Level of EOU sensitivity"""

    __proto_enum_type__ = ProtoDefaultEouClassifier.EouSensitivity
    __common_prefix__ = ''
    __unspecified_name__ = 'EOU_SENSITIVITY_UNSPECIFIED'

    #: Default and more conservative EOU detector.
    DEFAULT = ProtoDefaultEouClassifier.EouSensitivity.DEFAULT
    #: A high-sensitive and fast EOU detector, which may produce more false positives.
    HIGH = ProtoDefaultEouClassifier.EouSensitivity.HIGH



@dataclass(frozen=True)
class EndOfUtteranceClassifier(ProtoBasedWithBoolDefault[ProtoDefaultEouClassifier]):
    """Class which encapsulates settings
    `end of utterance classifier <https://yandex.cloud/docs/speechkit/stt/eou>`_.

    Usage this class object in text to speech configuration turning on
    default end-of-utterance classification.

    >>> EndOfUtteranceClassifier()
    EndOfUtteranceClassifier(sensentivity=Undefined, max_pause_between_words_hint_ms=Undefined)

    >>> EndOfUtteranceClassifier(sensentivity='high')
    EndOfUtteranceClassifier(sensentivity=<EndOfUtteranceSensetivity.HIGH: 2>, ...)

    >>> EndOfUtteranceClassifier(max_pause_between_words_hint_ms=10)
    EndOfUtteranceClassifier(sensentivity=Undefined, max_pause_between_words_hint_ms=10)
    """

    #: EOU sensitivity
    sensentivity: UndefinedOrEnumWithUnknownInput[EndOfUtteranceSensetivity] = UNDEFINED

    #: Hint for max pause between words.
    #: SpeechKit EOU detector could use this information to adjust the speed of the EOU detection.
    #: For example, a long pause between words will help distinguish between
    #: the end of utterance from slow speech like ``One <long pause> two <long pause> three``.
    #: A short pause can be helpful if the speaker is speaking quickly
    #: and does not emphasize pauses between sentences.
    max_pause_between_words_hint_ms: UndefinedOr[int] = UNDEFINED

    def __post_init__(self) -> None:
        # we must do enum coerce here to validate input data at object creation time
        if is_defined(self.sensentivity):
            # I cannot understand why mypy thinks that self.sensitivity is str | int | Undefined
            # when it must be EndOfUtteranceSensetivity | str | int
            # (without Undefined due to is_defined TypeGuard)
            object.__setattr__(
                self,
                'sensentivity',
                EndOfUtteranceSensetivity._coerce(self.sensentivity)  # type: ignore[arg-type]
            )

    @classmethod
    def _from_proto(cls, proto: ProtoDefaultEouClassifier, sdk: SDKType) -> Self:
        kwargs: dict[str, Any] = {}
        if proto.HasField('type') and proto.type:
            kwargs['sensentivity'] = EndOfUtteranceSensetivity._coerce(proto.type)
        if proto.HasField('max_pause_between_words_hint_ms'):
            kwargs['max_pause_between_words_hint_ms'] = proto.max_pause_between_words_hint_ms

        return cls(**kwargs)

    def _to_proto(self, sdk: SDKType) -> ProtoDefaultEouClassifier:
        result = ProtoDefaultEouClassifier()
        if is_defined(self.sensentivity):
            # it was coerced in __post__init__
            coerced: EnumWithUnknownAlias[EndOfUtteranceSensetivity] = cast(
                EnumWithUnknownAlias[EndOfUtteranceSensetivity],
                self.sensentivity,
            )
            result.type = int(coerced)  # type: ignore[assignment]

        if is_defined(self.max_pause_between_words_hint_ms):
            result.max_pause_between_words_hint_ms = self.max_pause_between_words_hint_ms

        return result



# pylint: disable-next=invalid-enum-extension
class RecognitionTriggerType(ProtoBasedEnum):
    """Type of recognition classifier trigger."""

    __proto_enum_type__ = ProtoRecognitionClassifier.TriggerType
    __common_prefix__ = ''
    __unspecified_name__ = 'TRIGGER_TYPE_UNSPECIFIED'

    #: Apply classifier to utterance responses.
    ON_UTTERANCE = ProtoRecognitionClassifier.TriggerType.ON_UTTERANCE
    #: Apply classifier to final responses.
    ON_FINAL = ProtoRecognitionClassifier.TriggerType.ON_FINAL
    #: Apply classifier to partial responses.
    ON_PARTIAL = ProtoRecognitionClassifier.TriggerType.ON_PARTIAL


RecognitionTriggerTypeInput = EnumWithUnknownInput[RecognitionTriggerType]


class WellKnownRecognitionClassifiers(StrEnum):
    """Well known names of recognition classifier triggers.

    More on the topic in `article <https://yandex.cloud/docs/speechkit/stt/analysis#classifier>`_.
    """

    formal_greeting = auto()
    informal_greeting = auto()
    formal_farewell = auto()
    informal_farewell = auto()
    insult = auto()
    profanity = auto()
    gender = auto()
    negative = auto()
    answerphone = auto()


@dataclass(frozen=True)
class RecognitionClassifier(ProtoBased[ProtoRecognitionClassifier]):
    """Classifier to use in speech recognotion.

    For detailed information refer to `documentation
    <https://yandex.cloud/docs/speechkit/stt/analysis>`_.

    You can pass a string as a trigger:
    >>> RecognitionClassifier('insult', 'on_final')
    RecognitionClassifier(name='insult', triggers=(<RecognitionTriggerType.ON_FINAL: 2>,))

    Or any iterable of strings to declare few triggers:
    >>> RecognitionClassifier('insult', ['on_final', 'on_partial'])
    RecognitionClassifier(..., triggers=(...ON_FINAL: 2>, <...ON_PARTIAL: 3>))

    You could also use alternative constructors when you have only one trigger:
    >>> RecognitionClassifier.on_utterance('insult')
    RecognitionClassifier(name='insult', triggers=(<RecognitionTriggerType.ON_UTTERANCE: 1>,))

    There are special `RecognitionClassifier.WellKnown` enum with well-known classifier names:
    >>> RecognitionClassifier(RecognitionClassifier.WellKnown.gender, 'on_final')
    RecognitionClassifier(name=<WellKnownRecognitionClassifiers.gender: 'gender'>, ...)

    On unknown trigger names there will be exception raised:
    >>> RecognitionClassifier('insult', ['on_something'])
    Traceback (most recent call last):
        ...
    ValueError: wrong value "on_something" for use as an alias ...; known values: ('ON_UTTERANCE', ...)


    """

    #: Classifier name.
    name: str

    #: Describes the types of responses to which the classification results will come.
    #: Classification responses will follow the responses of the specified types.
    triggers: Iterable[RecognitionTriggerTypeInput] | RecognitionTriggerTypeInput

    #: Well known names of recognition classifier triggers.
    WellKnown = WellKnownRecognitionClassifiers

    def __post_init__(self) -> None:
        if not self.triggers:
            raise ValueError(
                'You mast pass at least one trigger into RecognitionClassifier constructor'
            )

        triggers_iterable: Iterable[RecognitionTriggerTypeInput]
        if isinstance(self.triggers, (int, str, RecognitionTriggerType)):
            triggers_iterable = (self.triggers, )
        else:
            triggers_iterable = self.triggers

        coerced: tuple[EnumWithUnknownAlias[RecognitionTriggerType], ...] = tuple(
            RecognitionTriggerType._coerce(v) for v in triggers_iterable
        )

        object.__setattr__(self, 'triggers', coerced)

    @classmethod
    def _from_proto(cls, proto: ProtoRecognitionClassifier, sdk: SDKType) -> Self:
        return cls(
            name=proto.classifier,
            triggers=(RecognitionTriggerType._coerce(t) for t in proto.triggers)
        )

    def _to_proto(self, sdk: SDKType) -> ProtoRecognitionClassifier:
        triggers = self.triggers
        assert isinstance(triggers, tuple)
        assert all(isinstance(t, RecognitionTriggerType) for t in triggers)

        return ProtoRecognitionClassifier(
            classifier=self.name,
            triggers=triggers
        )

    @classmethod
    def on_utterance(cls, name: str) -> Self:
        """Alternative constructor to use onle 'on_utterance' trigger"""
        return cls(name=name, triggers='on_utterance')

    @classmethod
    def on_final(cls, name: str) -> Self:
        """Alternative constructor to use onle 'on_final' trigger"""
        return cls(name=name, triggers='on_final')

    @classmethod
    def on_partial(cls, name: str) -> Self:
        """Alternative constructor to use onle 'on_partial' trigger"""
        return cls(name=name, triggers='on_partial')


@dataclass(frozen=True)
class SpeechAnalysis(ProtoBasedWithBoolDefault[ProtoSpeechAnalysisOptions]):
    """Class which encapsulates
    `speech analysis settings <https://yandex.cloud/docs/speechkit/stt/analysis>`_"""

    #: Analyse speech for every speaker
    speaker_analysis: UndefinedOr[bool] = UNDEFINED
    #: Analyse conversation of two speakers
    conversation_analysis: UndefinedOr[bool] = UNDEFINED
    #: Quantile levels in range (0, 1) for descriptive statistics
    descriptive_statistics_quantiles: UndefinedOr[Sequence[float]] = UNDEFINED

    @classmethod
    def _from_proto(cls, proto: ProtoSpeechAnalysisOptions, sdk: SDKType) -> Self:
        kwargs: dict[str, Any] = {}

        if proto.HasField('enable_speaker_analysis'):
            kwargs['speaker_analysis'] = proto.enable_speaker_analysis
        if proto.HasField('enable_conversation_analysis'):
            kwargs['conversation_analysis'] = proto.enable_conversation_analysis

        if proto.HasField('descriptive_statistics_quantiles'):
            kwargs['descriptive_statistics_quantiles'] = tuple(
                proto.descriptive_statistics_quantiles
            )

        return cls(**kwargs)

    def _to_proto(self, sdk: SDKType) -> ProtoSpeechAnalysisOptions:
        result = ProtoSpeechAnalysisOptions()
        if is_defined(self.speaker_analysis):
            result.enable_speaker_analysis = self.speaker_analysis

        if is_defined(self.conversation_analysis):
            result.enable_conversation_analysis = self.conversation_analysis

        if is_defined(self.descriptive_statistics_quantiles):
            result.descriptive_statistics_quantiles.extend(
                self.descriptive_statistics_quantiles
            )

        return result


@dataclass
class LLMPostProcessingInstruction:
    """Class for encapsulating exactly one post processing settings."""

    #: Instruction for model.
    instruction: str

    #: Format of the response returned by the model.
    #: Format could be described as:
    #:
    #: * `None` for usual text response (default);
    #: * '`json`' string to tell a model to return JSON object;
    #: * dictonary with a JsonSchema to enforce a specific JSON
    #:   structure for the model's response based on a provided schema;
    #: * pydantic model or pydantic dataclass
    #:   (which will be transformed into JsonSchema by SDK);
    response_format: ResponseType | None


@dataclass(frozen=True)
class LLMPostProcessing(ProtoBased[ProtoSummarizationOptions]):
    """Class for encapsulating
    `transcription llm post processing settings
    <https://yandex.cloud/docs/speechkit/stt/llm-results>`_

    You could pass a full model uri:
    >>> llm_post_processor = LLMPostProcessing('gpt://<folder_id>/yandexgt/latest')

    You could use model name, in this case model uri will be built using configurated folder_id:
    >>> llm_post_processor = LLMPostProcessing('yandexgt')

    You could also pass a model version, which have 'latest' by default:
    >>> llm_post_processor = LLMPostProcessing('yandexgt', model_version='latest')

    After post processor object creation you should add some instructions into it
    by using ``.with_instruction`` method (which is not mutates the object, but creates a copy):
    >>> llm_post_processor = llm_post_processor.with_instruction("Make a short review")
    >>> llm_post_processor = llm_post_processor.with_instruction(
    ...     "What the conversation topic",
    ...     response_format="json"
    ... )

    Created object will looks like this:
    >>> llm_post_processor
    LLMPostProcessing(model_name='yandexgt', model_version='latest', ...)
    >>> llm_post_processor
    LLMPostProcessing(..., instructions=(LLMPostProcessingInstruction(...), LLMPostProcessingInstruction(...)))

    You also can use pydantic model or pydantic dataclass as response format.

    """

    #: The `ID of the model <https://yandex.cloud/docs/foundation-models/concepts/yandexgpt/models>`_
    #: Model name to be used for completion generation;
    #: If the name contains '://', it is treated as a full URI.
    #: Otherwise constructs a URI in the form 'gpt://<folder_id>/<model_name>/<model_version>'
    model_name: str

    #: The version of the model to use.
    #: Defaults to 'latest'
    model_version: str = 'latest'

    #: A list of instructions to perform with transcription.
    instructions: Sequence[LLMPostProcessingInstruction] = ()

    def with_instruction(
        self,
        instruction: str,
        response_format: ResponseType | None = None
    ) -> LLMPostProcessing:
        """
        Creates a new LLMPostProcessing object, but with given instruction appended.

        :param instruction: instruction for model.
        :param response_format: format of the response returned by the model.
            Format could be described as:

            * `None` for usual text response (default);
            * '`json`' string to tell a model to return JSON object;
            * dictonary with a JsonSchema to enforce a specific JSON
              structure for the model's response based on a provided schema;
            * pydantic model or pydantic dataclass
              (which will be transformed into JsonSchema by SDK);
        """
        new_instructions = tuple(self.instructions) + (
            LLMPostProcessingInstruction(
                instruction=instruction,
                response_format=response_format
            ),
        )
        return dataclasses.replace(
            self,
            instructions=new_instructions
        )

    @classmethod
    def _response_format_from_proto(cls, proto: SummarizationProperty) -> ResponseType | None:
        if proto.HasField('json_object'):
            return 'json'

        if proto.HasField('json_schema'):
            return {
                "json_schema": proto_to_dict(proto.json_schema.schema),
            }

        return None

    @classmethod
    def _from_proto(cls, proto: ProtoSummarizationOptions, sdk: SDKType) -> Self:
        return cls(
            model_name=proto.model_uri,
            instructions=tuple(
                LLMPostProcessingInstruction(
                    instruction=i.instruction,
                    response_format=cls._response_format_from_proto(i)
                ) for i in proto.properties
            )
        )

    def _to_proto(self, sdk: SDKType) -> ProtoSummarizationOptions:
        uri = sdk._get_model_uri('gpt', self.model_name, self.model_version)

        if not self.instructions:
            raise ValueError(
                'LLMPostProcessing without instructions do not have any sense; '
                'use .with_instruction method to add instructions to the object'
            )

        return ProtoSummarizationOptions(
            model_uri=uri,
            properties=[
                SummarizationProperty(
                    instruction=i.instruction,
                    **make_response_format_kwargs(i.response_format)
                ) for i in self.instructions
            ]
        )
