# pylint: disable=no-name-in-module,protected-access,unused-argument
from __future__ import annotations

from typing import Literal

from yandex.cloud.ai.stt.v3.stt_pb2 import (
    AudioFormatOptions, EouClassifierOptions, ExternalEouClassifier, LanguageRestrictionOptions,
    RecognitionClassifierOptions, RecognitionModelOptions, RecognizeFileRequest, SpeakerLabelingOptions,
    SpeechAnalysisOptions, StreamingOptions, SummarizationOptions
)

from yandex_ai_studio_sdk._speechkit.enums import AudioFormat, LanguageCode
from yandex_ai_studio_sdk._types.proto import SDKType

from .config import SpeechToTextConfig
from .structures import (
    EndOfUtteranceClassifier, LLMPostProcessing, RecognitionClassifier, SpeechAnalysis, TextNormalization
)


def _create_recognition_model_options(
    sdk: SDKType,
    config: SpeechToTextConfig,
    mode: Literal['real_time', 'full_data']
) -> RecognitionModelOptions:
    language_restriction = LanguageRestrictionOptions(
        language_code=LanguageCode._coerce_to_proto(config.language_codes),
        restriction_type=LanguageRestrictionOptions.LanguageRestrictionType.WHITELIST,
    ) if config.language_codes else None

    text_normalization = TextNormalization._coerce_to_proto(
        sdk,
        TextNormalization._coerce(config.text_normalization),
    )

    audio_processing_type = {
        'real_time': RecognitionModelOptions.AudioProcessingType.REAL_TIME,
        'full_data': RecognitionModelOptions.AudioProcessingType.FULL_DATA,
    }[mode]

    return RecognitionModelOptions(
        audio_format=AudioFormat._to_proto(
            AudioFormatOptions, AudioFormat._coerce(config.audio_format),
        ),  # type: ignore[arg-type]
        audio_processing_type=audio_processing_type,
        language_restriction=language_restriction,
        model=config.model or '',
        text_normalization=text_normalization,
    )


def _create_speech_analysis(
    sdk: SDKType,
    config: SpeechToTextConfig,
) -> SpeechAnalysisOptions | None:
    return SpeechAnalysis._coerce_to_proto(sdk, config.speech_analysis)


def _create_speaker_labeling(
    sdk: SDKType,
    config: SpeechToTextConfig,
) -> SpeakerLabelingOptions:
    speaker_labeling = {
        True: SpeakerLabelingOptions.SpeakerLabeling.SPEAKER_LABELING_ENABLED,
        False: SpeakerLabelingOptions.SpeakerLabeling.SPEAKER_LABELING_DISABLED,
        None: SpeakerLabelingOptions.SpeakerLabeling.SPEAKER_LABELING_UNSPECIFIED,
    }[config.speaker_labeling]
    return SpeakerLabelingOptions(speaker_labeling=speaker_labeling)


def _create_summarization(
    sdk: SDKType,
    config: SpeechToTextConfig,
) -> SummarizationOptions | None:
    return LLMPostProcessing._coerce_to_proto(sdk, config.llm_post_process)


def _create_classifiers(
    sdk: SDKType,
    config: SpeechToTextConfig,
) -> RecognitionClassifierOptions:
    classifiers = None
    if raw_classifiers := config.recognition_classifiers:
        list_classifiers: list[RecognitionClassifier]
        if isinstance(raw_classifiers, RecognitionClassifier):
            list_classifiers = [raw_classifiers]
        else:
            list_classifiers = list(raw_classifiers)

        classifiers = [c._to_proto(sdk) for c in list_classifiers]
    return RecognitionClassifierOptions(
        classifiers=classifiers,
    )


def create_streaming_options(
    sdk: SDKType,
    config: SpeechToTextConfig,
    mode: Literal['real_time', 'full_data'],
) -> StreamingOptions:
    eou_classifier: EouClassifierOptions | None = None
    if eou := config.eou_classifier:  # EndOfUtteranceClassifier or True
        assert isinstance(eou, (bool, EndOfUtteranceClassifier))
        eou_classifier = EouClassifierOptions(
            default_classifier=EndOfUtteranceClassifier._coerce_to_proto(
                sdk,
                EndOfUtteranceClassifier._coerce(eou),
            )
        )
    elif config.eou_classifier is False:
        eou_classifier = EouClassifierOptions(
            external_classifier=ExternalEouClassifier()
        )

    return StreamingOptions(
        recognition_model=_create_recognition_model_options(sdk, config, mode),
        eou_classifier=eou_classifier,
        recognition_classifier=_create_classifiers(sdk, config),
        speaker_labeling=_create_speaker_labeling(sdk, config),
        speech_analysis=_create_speech_analysis(sdk, config),
        summarization=_create_summarization(sdk, config),
    )


def create_recognize_file_request(
    sdk: SDKType,
    config: SpeechToTextConfig,
) -> RecognizeFileRequest:
    return RecognizeFileRequest(
        recognition_classifier=_create_classifiers(sdk, config),
        recognition_model=_create_recognition_model_options(sdk, config, 'full_data'),
        speaker_labeling=_create_speaker_labeling(sdk, config),
        speech_analysis=_create_speech_analysis(sdk, config),
        summarization=_create_summarization(sdk, config),
    )
