# pylint: disable=protected-access
from __future__ import annotations

from functools import cached_property
from typing import Generic

from yandex_ai_studio_sdk._types.domain import BaseDomain
from yandex_ai_studio_sdk._utils.doc import doc_from

from .function import AsyncFunctionTools, FunctionTools, FunctionToolsTypeT


class BaseTools(BaseDomain, Generic[FunctionToolsTypeT]):
    """
    Class for tools functionality.

    Tools are specialized utilities that extend the capabilities of language models and AI assistants
    by providing access to external functions, data sources, and computational resources. They enable
    models to perform actions beyond text generation, such as searching through knowledge bases,
    executing custom functions, and processing structured data.

    This class serves as the foundation for tool management in both synchronous and asynchronous
    contexts, providing a unified interface for tools. For more information see the description
    of members of this class.

    Tools are particularly useful in:

    - **Completions**: Enabling language models to invoke functions during text generation for
      dynamic content creation and problem-solving

    The tools framework supports both streaming and non-streaming operations, making it suitable
    for real-time applications and batch processing scenarios.
    """
    _functions_impl: type[FunctionToolsTypeT]

    @cached_property
    def function(self) -> FunctionToolsTypeT:
        """
        Get the function sub-domain for creating function tools.
        """
        return self._functions_impl(
            name='tools.function',
            sdk=self._sdk
        )


@doc_from(BaseTools)
class AsyncTools(BaseTools[AsyncFunctionTools]):
    _functions_impl = AsyncFunctionTools

@doc_from(BaseTools)
class Tools(BaseTools[FunctionTools]):
    _functions_impl = FunctionTools
