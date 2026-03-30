# pylint: disable=no-name-in-module,invalid-enum-extension
from __future__ import annotations

import re
from collections.abc import Sequence
from enum import Enum
from typing import TypeAlias, TypeVar, Union

from typing_extensions import Never
from yandex.cloud.ai.stt.v3.stt_pb2 import AudioFormatOptions as STTAudioFormatOptions
from yandex.cloud.ai.stt.v3.stt_pb2 import ContainerAudio as STTContainerAudio
from yandex.cloud.ai.stt.v3.stt_pb2 import RawAudio as STTRawAudio
from yandex.cloud.ai.tts.v3.tts_pb2 import AudioFormatOptions as TTSAudioFormatOptions
from yandex.cloud.ai.tts.v3.tts_pb2 import ContainerAudio as TTSContainerAudio
from yandex.cloud.ai.tts.v3.tts_pb2 import LoudnessNormalizationType
from yandex.cloud.ai.tts.v3.tts_pb2 import RawAudio as TTSRawAudio
from yandex_ai_studio_sdk._types.enum import (
    EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum, UnknownEnumValue
)

AudioFormatOptionsTypeT = TypeVar('AudioFormatOptionsTypeT', STTAudioFormatOptions, TTSAudioFormatOptions)


class PCM16(UnknownEnumValue['AudioFormat']):
    def __new__(cls, sample_rate_hertz: int, channels: int):
        return super().__new__(cls, enum_type=AudioFormat, name='PCM16', value=-1)

    def __init__(self, sample_rate_hertz: int, channels: int):
        super().__init__(
            enum_type=AudioFormat,
            name='PCM16',
            value=-1
        )
        self._sample_rate_hertz = sample_rate_hertz
        self._channels = channels

    @property
    def sample_rate_hertz(self) -> int:
        return self._sample_rate_hertz

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def value(self) -> Never:
        raise RuntimeError("PCM16 can't be used with a value")

    def __str__(self) -> str:
        return (
            f'{self._enum_type.__name__}'
            f'.{self.__class__.__name__}'
            f'({self.sample_rate_hertz!r}, channels={self.channels!r})'
        )

    def __eq__(self, other) -> bool:
        if not super().__eq__(other):
            return False

        assert isinstance(other, PCM16)
        return (
            other.sample_rate_hertz == self.sample_rate_hertz and
            other.channels == self.channels
        )

    def __hash__(self) -> int:
        return hash((self._sample_rate_hertz, self._value))


class AudioFormat(ProtoBasedEnum):
    __proto_enum_type__ = STTContainerAudio.ContainerAudioType
    __common_prefix__ = ''
    __unspecified_name__ = 'CONTAINER_AUDIO_TYPE_UNSPECIFIED'
    __pcm16_re__ = re.compile(
        r'(?:LINEAR16_PCM|PCM16)\((?P<sample_rate_hertz>\d+)(?:,[ ]?(?P<channels>\d+))?\)$'
    )

    __aliases__ = {
        'OPUS': 'OGG_OPUS',
    }

    #: Data is encoded using MPEG-1/2 Layer III and compressed using the MP3 container format
    MP3 = STTContainerAudio.ContainerAudioType.MP3
    #: Audio bit depth 16-bit signed little-endian (Linear PCM) packed into WAV container format
    WAV = STTContainerAudio.ContainerAudioType.WAV
    #: Data is encoded using the OPUS audio codec and compressed using the OGG container format
    OGG_OPUS = STTContainerAudio.ContainerAudioType.OGG_OPUS

    @classmethod
    def PCM16(cls, sample_rate_hertz: int, channels: int = 1) -> PCM16:
        """Audio bit depth 16-bit signed little-endian (Linear PCM)."""
        return PCM16(sample_rate_hertz, channels)

    @classmethod
    def _coerce(
        cls: type[AudioFormat],
        value: EnumWithUnknownInput[AudioFormat],
    ) -> EnumWithUnknownAlias[AudioFormat]:
        if isinstance(value, str):
            # pylint: disable-next=no-member
            if match := cls.__pcm16_re__.match(value):
                sample_rate_hertz, channels = match.groups()
                return cls.PCM16(
                    sample_rate_hertz=int(sample_rate_hertz),
                    channels=int(channels) if channels else 1
                )

        return super()._coerce(value)

    @classmethod
    def _get_available(cls) -> tuple[str, ...]:
        return super()._get_available() + ('PCM16(<int>)', 'PCM16(<int>, <int>)')

    @staticmethod
    def _to_proto(
        proto_type: type[AudioFormatOptionsTypeT],
        value: EnumWithUnknownAlias[AudioFormat] | None,
    ) -> AudioFormatOptionsTypeT | None:
        if isinstance(value, PCM16):
            raw_audio_type = {
                STTAudioFormatOptions: STTRawAudio,
                TTSAudioFormatOptions: TTSRawAudio,
            }[proto_type]
            encoding = getattr(raw_audio_type, 'AudioEncoding')
            kwargs = {}
            if raw_audio_type is STTRawAudio and value.channels > 1:
                kwargs['audio_channel_count'] = value.channels
            return proto_type(
                raw_audio=raw_audio_type(
                    audio_encoding=encoding.LINEAR16_PCM,
                    sample_rate_hertz=value.sample_rate_hertz,
                    **kwargs,
                )
            )

        if value is None:
            return proto_type()

        container_audio_type = {
            STTAudioFormatOptions: STTContainerAudio,
            TTSAudioFormatOptions: TTSContainerAudio,
        }[proto_type]

        return proto_type(
            container_audio=container_audio_type(
                container_audio_type=int(value)  # type: ignore[arg-type]
            )
        )


class LoudnessNormalization(ProtoBasedEnum):
    __proto_enum_type__ = LoudnessNormalizationType
    __common_prefix__ = ''
    __unspecified_name__ = 'LOUDNESS_NORMALIZATION_TYPE_UNSPECIFIED'

    #: The type of normalization, wherein the gain is changed to bring the highest PCM sample value or analog signal peak to a given level.
    MAX_PEAK = LoudnessNormalizationType.MAX_PEAK
    #: The type of normalization based on EBU R 128 recommendation
    LUFS = LoudnessNormalizationType.LUFS


class LanguageCode(str, Enum):
    __language_code_re__ = re.compile(r'([a-zA-Z]+)[-_]([a-zA-Z]+)$')

    #: `Automatic language detection <https://aistudio.yandex.ru/docs/speechkit/stt/models#language-labels>`_
    auto = 'auto'
    #: German
    de_DE = "de-DE"
    #: English
    en_US = "en-US"
    #: Spanish
    es_ES = "es-ES"
    #: Finnish
    fi_FI = "fi-FI"
    #: French
    fr_FR = "fr-FR"
    #: Hebrew
    he_IL = "he-IL"
    #: Italian
    it_IT = "it-IT"
    #: Kazakh
    kk_KZ = "kk-KZ"
    #: Dutch
    nl_NL = "nl-NL"
    #: Polish
    pl_PL = "pl-PL"
    #: Portuguese
    pt_PT = "pt-PT"
    #: Brazilian Portuguese
    pt_BR = "pt-BR"
    #: Russian (default)
    ru_RU = "ru-RU"
    #: Swedish
    sv_SE = "sv-SE"
    #: Turkish
    tr_TR = "tr-TR"
    #: Uzbek (Latin script)
    uz_UZ = "uz-UZ"

    @classmethod
    def _coerce_to_str(
        cls: type[LanguageCode],
        value: LanguageCodeInputType,
    ) -> str:
        if isinstance(value, LanguageCode):
            return value.value

        if not isinstance(value, str):
            raise TypeError(f'{value=} for language code is not a string nor LanguageCode enum value')

        value = value.lower()
        if value == 'auto':
            return value

        # pylint: disable-next=no-member
        if match := cls.__language_code_re__.match(value):
            first, second = match.groups()
            return f'{first}-{second.upper()}'

        raise ValueError(f'failed to parse language code string {value!r}')

    @classmethod
    def _coerce_to_proto(
        cls: type[LanguageCode],
        value: LanguageCodesInputType | None,
    ) -> list[str] | None:
        if value is None:
            return None

        codes: list[LanguageCodeInputType]
        if isinstance(value, (str, LanguageCode)):
            codes = [value]
        else:
            codes = list(value)

        return [cls._coerce_to_str(code) for code in codes]


LanguageCodeInputType: TypeAlias = Union[str, LanguageCode]
LanguageCodesInputType: TypeAlias = Union[LanguageCodeInputType | Sequence[LanguageCodeInputType]]
