from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from yandex_ai_studio_sdk.cli.search_index.openai_types import OpenAIFileCreateParams

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


def create_command_executor(command_class: type[BaseCommand], **kwargs: Any) -> None:
    file_create_params = OpenAIFileCreateParams(
        purpose=kwargs.pop("file_purpose"),
        expires_after_seconds=kwargs.pop("file_expires_after_seconds", None),
        expires_after_anchor=kwargs.pop("file_expires_after_anchor", None),
    )
    command = command_class(file_create_params=file_create_params, **kwargs)
    command.execute()
