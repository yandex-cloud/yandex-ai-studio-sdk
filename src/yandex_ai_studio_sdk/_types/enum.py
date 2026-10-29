from __future__ import annotations

from enum import EnumMeta, IntEnum
from typing import Generic, Protocol, TypeVar, Union

from .misc import Undefined

T = TypeVar('T', bound=int)
ProtoBasedEnumTypeT = TypeVar('ProtoBasedEnumTypeT', bound='ProtoBasedEnum')


class EnumTypeWrapperProtocol(Protocol[T]):
    def Name(self, number: T) -> str: ...
    def Value(self, name: str) -> T: ...
    def items(self) -> list[tuple[str, T]]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[T]: ...


class UnknownEnumValue(Generic[ProtoBasedEnumTypeT], int):
    def __new__(cls, enum_type: type[ProtoBasedEnumTypeT], name: str, value: int):
        return super().__new__(cls, value)

    def __init__(self, enum_type: type[ProtoBasedEnumTypeT], name: str, value: int):
        self._enum_type = enum_type
        self._name = name
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> int:
        return self._value

    @property
    def enum_type(self) -> type[ProtoBasedEnumTypeT]:
        return self._enum_type

    def __str__(self) -> str:
        return f"{self._enum_type.__name__}.Unknown({self._name!r}, {self._value!r})"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        if isinstance(other, UnknownEnumValue):
            return (
                self._enum_type is other._enum_type
                and self._value == other._value
            )
        return False

    def __hash__(self) -> int:
        return hash((self._enum_type, self._value))


class EnumWithUnknownType(EnumMeta):
    __common_prefix__: str
    __proto_enum_type__: EnumTypeWrapperProtocol
    __aliases__: dict[str, str]

    def __instancecheck__(cls, inst):
        if isinstance(inst, UnknownEnumValue):
            return inst.enum_type is cls

        return super().__instancecheck__(inst)


class ProtoBasedEnum(IntEnum, metaclass=EnumWithUnknownType):
    """
    The ideas behind these special enums are as follows:
    1) Its descendants mirror __proto_enum_type__
       without metadata or autocompletion for users;
    2) The resulting enum can process user input:
       a user can pass a string, integer, or enum value to our interface
       and it will be verified and unambiguously translated into an enum value,
       which is suitable for gRPC/HTTP requests.
    3) If the ``__proto_enum_type__`` class is updated in the protobuf files,
       we want users to be able to continue without an SDK upgrade:
       if a new ``ProtoEnum`` protobuf enum value appears,
       users will be able to pass a string value to our interface as a workaround
       and it will be transformed to
       ``Enum.Unknown('new_enum_value_name', 'new_enum_value')`` value
       which is suitable to use in our grpc/http requests.
    """

    __common_prefix__: str
    __proto_enum_type__: EnumTypeWrapperProtocol
    __unspecified_name__: str = 'UNSPECIFIED'
    __aliases__: dict[str, str] = {}

    @classmethod
    # pylint: disable=too-many-return-statements
    def _coerce(
        cls: type[ProtoBasedEnumTypeT],
        value: EnumWithUnknownInput[ProtoBasedEnumTypeT],
    ) -> EnumWithUnknownAlias[ProtoBasedEnumTypeT]:
        common_prefix = cls.__common_prefix__
        proto_enum_type: EnumTypeWrapperProtocol = cls.__proto_enum_type__

        if isinstance(value, cls):
            return value

        if isinstance(value, int):
            try:
                return cls(value)
            except ValueError:
                pass

            try:
                # pylint: disable-next=no-member
                proto_name = proto_enum_type.Name(value)
                short_name = proto_name.removeprefix(common_prefix)
                return cls.Unknown(short_name, value)
            except ValueError:
                # pylint: disable-next=raise-missing-from
                raise ValueError(f'wrong value "{value}" for use as an alias for {cls}')

        if isinstance(value, str):
            name = value.upper()
            short_name = name.removeprefix(common_prefix)
            long_name = name if name.startswith(common_prefix) else common_prefix + name

            if result := getattr(cls, name, None):
                if isinstance(result, cls):
                    return result
            if result := getattr(cls, short_name, None):
                if isinstance(result, cls):
                    return result

            try:
                # pylint: disable-next=no-member
                proto_value = proto_enum_type.Value(long_name)
                return cls.Unknown(short_name, proto_value)
            except ValueError:
                if alias := cls.__aliases__.get(short_name.upper()):  # pylint: disable=no-member
                    return getattr(cls, alias)

                # pylint: disable-next=raise-missing-from
                raise ValueError(
                    f'wrong value "{value}" for use as an alias for {cls}; known values: {cls._get_available()}'
                )

        raise TypeError(f'wrong type "{type(value)}" for use as an alias for {cls}')

    @classmethod
    def Unknown(cls, name: str, value: int):
        return UnknownEnumValue(cls, name, value)

    @classmethod
    def _get_available(cls) -> tuple[str, ...]:
        names = (
            name.removeprefix(cls.__common_prefix__)
            for name in cls.__proto_enum_type__.keys()  # pylint: disable=no-member
        )
        return tuple(name for name in names if name != cls.__unspecified_name__)

#: Enum type which has a special Unknown value for values that are present
#: in the gRPC API but not described in our Python code
EnumWithUnknownAlias = Union[ProtoBasedEnumTypeT, UnknownEnumValue[ProtoBasedEnumTypeT]]
EnumWithUnknownInput = Union[EnumWithUnknownAlias[ProtoBasedEnumTypeT], str, int]
UndefinedOrEnumWithUnknownInput = Union[EnumWithUnknownInput[ProtoBasedEnumTypeT], Undefined]
