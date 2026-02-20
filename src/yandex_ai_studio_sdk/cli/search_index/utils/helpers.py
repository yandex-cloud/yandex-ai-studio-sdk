from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

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
    command = command_class(**kwargs)
    command.execute()
