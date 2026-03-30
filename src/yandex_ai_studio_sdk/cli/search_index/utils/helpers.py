from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click
from yandex_ai_studio_sdk.cli.search_index.openai_types import OpenAIFileCreateParams, OpenAIVectorStoreCreateParams
from yandex_ai_studio_sdk.search_indexes import (
    HybridSearchIndexType, StaticIndexChunkingStrategy, TextSearchIndexType, VectorSearchIndexType
)

if TYPE_CHECKING:
    from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand


def validate_authentication(
    username: str | None,
    token: str | None,
    auth_type: str = "authentication",
) -> tuple[str, str]:
    if not username or not token:
        raise click.ClickException(
            f"{auth_type} required. Provide credentials via command line options or environment variables."
        )

    return username, token


def parse_metadata(label_tuples: tuple[str, ...]) -> dict[str, str]:
    """Parse metadata strings in format 'KEY=VALUE' into a dictionary."""
    labels = {}
    for label_str in label_tuples:
        if "=" not in label_str:
            raise click.BadParameter(
                f"Invalid metadata format '{label_str}', expected KEY=VALUE"
            )
        key, value = label_str.split("=", 1)
        labels[key.strip()] = value.strip()
    return labels


def _create_chunking_strategy(
    max_chunk_size_tokens: int,
    chunk_overlap_tokens: int,
) -> HybridSearchIndexType:
    chunking_strategy = StaticIndexChunkingStrategy(
        max_chunk_size_tokens=max_chunk_size_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
    )
    return HybridSearchIndexType(
        text_search_index=TextSearchIndexType(chunking_strategy=chunking_strategy),
        vector_search_index=VectorSearchIndexType(chunking_strategy=chunking_strategy),
    )


def run_command(command_class: type[BaseCommand], **kwargs: Any) -> None:
    file_create_params = OpenAIFileCreateParams(
        purpose=kwargs.pop("file_purpose"),
        expires_after_seconds=kwargs.pop("file_expires_after_seconds", None),
        expires_after_anchor=kwargs.pop("file_expires_after_anchor", None),
    )
    metadata_raw = kwargs.pop("metadata")
    vector_store_params = OpenAIVectorStoreCreateParams(
        name=kwargs.pop("name"),
        metadata=parse_metadata(metadata_raw) if metadata_raw else None,
        expires_after_days=kwargs.pop("expires_after_days"),
        expires_after_anchor=kwargs.pop("expires_after_anchor"),  # type: ignore[arg-type]
        chunking_strategy=_create_chunking_strategy(
            kwargs.pop("max_chunk_size_tokens"),
            kwargs.pop("chunk_overlap_tokens"),
        ),
    )
    command = command_class(
        file_create_params=file_create_params,
        vector_store_params=vector_store_params,
        **kwargs,
    )
    command.execute()
