"""
title: Yandex AI Studio Agents Integration for Open WebUI
version: 0.1.2
description: Integration with Yandex AI Studio Agents using Responses API with real-time status and streaming
author: https://github.com/vhaldemar
license: MIT
"""

from __future__ import annotations

import asyncio
import copy
import io
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import TypeVar

import openai
from fastapi import Request, UploadFile
from open_webui.env import VERSION as OPEN_WEBUI_VERSION
from open_webui.models.chats import Chats
from open_webui.models.files import FileModel
from open_webui.models.users import UserModel
from open_webui.routers.files import upload_file_handler
from open_webui.routers.openai import convert_to_responses_payload
from openai import AsyncOpenAI, NotFoundError
from openai.types.responses.response_code_interpreter_call_code_done_event import (
    ResponseCodeInterpreterCallCodeDoneEvent
)
from openai.types.responses.response_output_item_done_event import ResponseOutputItemDoneEvent
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import (
    AnnotationContainerFileCitation, AnnotationFileCitation, AnnotationURLCitation
)
from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent
from openai.version import VERSION as OPENAI_VERSION
from pydantic import BaseModel, Field

EventEmitterType = Callable[[dict], Awaitable[None]]
T = TypeVar("T")

THIS_PIPE_VERSION = "0.1.2"
PIPE_ORIGIN = (
    "https://github.com/yandex-cloud/yandex-ai-studio-sdk/tree/master/open-webui"
)
TICKETS_URL = "https://github.com/yandex-cloud/yandex-ai-studio-sdk/issues"
FILES_LINK = "https://aistudio.yandex.ru/platform/folders/{folder_id}/files"
LAST_TESTED_WEBUI_VERSION = "0.9.1"
USER_AGENT = f"AsyncOpenAI/Python {OPENAI_VERSION}/OpenWebUI Agents Pipe {THIS_PIPE_VERSION}"

STATUS_NAMES = {
    # Open WebUI task names, we are using it instead of responses event.type
    # in case of they exists
    "follow_up_generation": "Generating follow up...",
    "title_generation": "Generating title for the chat...",
    "tags_generation": "Generating tags for the chat...",
    # Web Search
    "response.web_search_call.in_progress": "Searching the web...",
    "response.web_search_call.searching": "Searching the web...",
    "response.web_search_call.completed": "Search complete, analyzing results...",
    # MCP
    "response.mcp_list_tools.in_progress": "Connecting tools...",
    "response.mcp_list_tools.completed": "Tools connected",
    "response.mcp_call.in_progress": "Calling tool...",
    "response.mcp_call.completed": "Tool executed, generating response...",
    # File Search
    "response.file_search_call.in_progress": "Searching documents...",
    "response.file_search_call.searching": "Searching documents...",
    "response.file_search_call.completed": "Documents found, analyzing...",
    # Code Interpreter
    "response.code_interpreter_call.in_progress": "Executing code...",
    "response.code_interpreter_call.interpreting": "Executing code...",
    "response.code_interpreter_call.completed": "Code executed",
    "response.code_interpreter_call_code.done": "Code generated",
    # Response Lifecycle
    "response.created": "Creating response...",
    "response.in_progress": "Generating response...",
    "response.completed": "Response complete",
    "response.failed": "Response failed",
    "response.cancelled": "Response cancelled",
    "response.incomplete": "Response incomplete",
    # Output Item
    "response.output_item.added": "Processing output...",
    "response.output_item.done": "Output ready",
    # Text
    "response.output_text.delta": "Streaming text...",
    "response.output_text.done": "Text complete",
    "response.output_text.annotation.added": "Adding annotation...",
    # Reasoning
    "response.reasoning.delta": "Thinking...",
    "response.reasoning.done": "Reasoning complete",
    "response.reasoning_summary.delta": "Summarizing reasoning...",
    "response.reasoning_summary.done": "Reasoning summary complete",
    # I really dunno what is *_part/_text statuses means, but it is before response.reasoning_summary.done
    "response.reasoning_summary_part.added": "Thinking...",
    "response.reasoning_summary_text.delta": "Thinking...",
    "response.reasoning_summary_text.done": "Thinking...",
    "response.reasoning_summary_part.done": "Thinking...",
    # Content Part
    "response.content_part.added": "Adding content...",
    "response.content_part.done": "Content part complete",
    # Function Call
    "response.function_call_arguments.delta": "Preparing tool call...",
    "response.function_call_arguments.done": "Tool call ready",
    # Image Generation
    "response.image_generation_call.in_progress": "Generating image...",
    "response.image_generation_call.generating": "Generating image...",
    "response.image_generation_call.partial_image": "Image rendering...",
    "response.image_generation_call.completed": "Image generated",
    # Rate Limits / Usage
    "rate_limit_updated": "Rate limit updated",
    "response.refusal.delta": "Generating refusal...",
    "response.refusal.done": "Refusal complete",
    # Errors
    "error": "Error occurred",
}
TEXT_TRIM_LENGTH = 3000

SILENT_STATUSES = {
    'response.output_item.added',
    'response.output_item.done',
    'response.content_part.added',
    'response.content_part.done',
    'response.created',
    'response.output_text.done',
}


class Pipe:
    class Valves(BaseModel):
        YANDEX_CLOUD_API_KEY: str = Field(
            default="",
            description=(
                "Yandex Cloud API key, "
                "more on the topic at https://aistudio.yandex.ru/docs/ai-studio/operations/get-api-key.html"
            ),
            json_schema_extra={"input": {"type": "password"}},
        )

        YANDEX_CLOUD_FOLDER_ID: str = Field(
            default="",
            description="Yandex Cloud folder ID (e.g. b1grc91ju8et9rl2b8jg)",
        )

        AGENT_IDS: list[str] = Field(
            default_factory=list,
            description=(
                "Agents IDs from Yandex AI Studio, "
                'for example: "fvt210rlb66c, fvtp4kvcgiu36u"'
            ),
        )

        AGENT_NAMES: list[str] = Field(
            default_factory=list,
            description=(
                "Agent names to show in OpenWebUI instead of IDs; "
                "number and order of names must match IDs number and order"
            ),
        )

        AI_STUDIO_BASE_URL: str = Field(
            default="https://ai.api.cloud.yandex.net/v1",
            description="Yandex AI Studio API base URL",
        )

        MODEL_PREFIX: str = Field(
            default="",
            description="Optional prefix for model names in Open WebUI (e.g. 'Yandex: ')",
        )

        REQUEST_TIMEOUT: int = Field(
            default=90,
            description="Timeout for API requests in seconds",
            gt=0,
        )

        SILENT_FILES_WARNING: bool = Field(
            default=False,
            description="Silent warning about attaching files with OpenWebUI RAG enabled"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False
        self._files_cache = {}
        self._files_lock = asyncio.Lock()

    def _get_client(self) -> AsyncOpenAI:

        return AsyncOpenAI(
            api_key=self.valves.YANDEX_CLOUD_API_KEY,
            base_url=self.valves.AI_STUDIO_BASE_URL,
            project=self.valves.YANDEX_CLOUD_FOLDER_ID,
            timeout=self.valves.REQUEST_TIMEOUT,
            default_headers={"User-Agent": USER_AGENT},
        )

    def get_agent_name(self, agent_id: str) -> str:
        prefix = self.valves.MODEL_PREFIX
        name = self.agent_names.get(agent_id, f"Agent {agent_id}")
        return f"{prefix}{name}"

    @property
    def agent_names(self) -> dict[str, str]:
        ids = self.valves.AGENT_IDS
        names = self.valves.AGENT_NAMES
        return dict(zip(ids, names))

    def pipes(self) -> list[dict]:
        # TODO: Validate existence of agent ids or
        # add auto listing from backend
        try:
            self._validate_configuration()
        except ValueError as e:
            return [
                {
                    "id": "configuration_error",
                    "name": f"Configuration error: {e}",
                }
            ]

        models = []

        for agent_id in self.valves.AGENT_IDS:
            model_id = f"gpt://{self.valves.YANDEX_CLOUD_FOLDER_ID}/{agent_id}"
            name = self.get_agent_name(agent_id)
            models.append({"id": model_id, "name": name})

        return models

    @property
    def _error_string(self):
        return (
            f"{LAST_TESTED_WEBUI_VERSION=}, "
            f"{OPEN_WEBUI_VERSION=}, {THIS_PIPE_VERSION=}, "
            f"{OPENAI_VERSION=}, "
            f"please, try to update plugin from {PIPE_ORIGIN} "
            f"or create a ticket at {TICKETS_URL}"
        )

    def _assert_not_none(self, value: T | None, message: str) -> T:
        """I want to make "smart" assert with good error message and
        make it able to narrow types as usual assert"""

        if value is not None:
            return value

        raise RuntimeError(f"assertion error {message!r}, {self._error_string}")

    async def _emit_status(
        self, emitter: EventEmitterType, description: str, done: bool = False
    ):
        await emitter(
            {
                "type": "status",
                "data": {"description": description, "done": done},
            }
        )

    async def _emit_notification(self, emitter: EventEmitterType, level: str, content: str) -> None:
        await emitter({
            "type": "notification",
            "data": {
                 "type": level,
                 "content": content,
             }
        })

    # pylint: disable=too-many-locals
    async def _process_annotations(
        self,
        *,
        client: AsyncOpenAI,
        event_emitter: EventEmitterType,
        request: Request,
        user: dict,
        metadata: dict,
        event: ResponseOutputItemDoneEvent,
    ) -> None:
        item = event.item
        citations: set[tuple[str, str, str]] = set()
        files_link = FILES_LINK.format(folder_id=self.valves.YANDEX_CLOUD_FOLDER_ID)
        file_citations: set[tuple[str, str]] = set()
        if isinstance(item, ResponseOutputMessage):
            content = item.content
            for message in content:
                annotations = getattr(message, 'annotations', [])
                for annotation in annotations:
                    if isinstance(annotation, AnnotationFileCitation):
                        citations.add((annotation.filename, files_link, annotation.filename))
                    elif isinstance(annotation, AnnotationURLCitation):
                        citations.add((annotation.title, annotation.url, annotation.title))
                    elif isinstance(annotation, AnnotationContainerFileCitation):
                        file_citations.add((annotation.file_id, annotation.filename))

        for title, url, document in citations:
            source = {
                "name": title,
                'url': url
            }
            metadata = {
                'source': url,
                'name': title,
            }

            await event_emitter({
                "type": "citation",
                "data": {
                    "document": [document],
                    "metadata": [metadata],
                    "source": source,
                }
            })

        files: list[tuple[str, bytes]] = []
        for file_id, filename in file_citations:
            await self._emit_status(event_emitter, f'Downloading generated file {filename}...')
            content = await client.files.content(file_id)
            files.append((filename, content.content))

        await self._attach_files_to_webui(
            event_emitter=event_emitter,
            request=request,
            user=user,
            metadata=metadata,
            files=files
        )

    def _fixup_input_images(self, body: dict) -> None:
        input_ = body.get('input')
        _input = self._assert_not_none(input_, "input field")

        for message in _input:
            assert isinstance(message, dict)
            content = message.get('content', [])
            for submessage in content:
                assert isinstance(submessage, dict)
                if submessage.get('type') == 'input_image':
                    submessage['detail'] = submessage.get('detail', 'auto')

    async def _get_full_message_list(self, metadata: dict) -> list[dict]:
        """We are fetching messages from open webui database here.
        Right now it is only way to get a connection between message and attached file:
        official Open WebUI Pipe API is giving only unordered files with no
        information about message it was attached to.
        """

        chat_id = self._assert_not_none(metadata.get('chat_id'), 'chat_id in metadata')
        parent_message_id = self._assert_not_none(metadata.get('user_message_id'), 'user_message_id in metadata')

        messages_map = await Chats.get_messages_map_by_chat_id(chat_id)
        all_messages = self._assert_not_none(messages_map, f'{chat_id} present in DB')

        messages: list[dict] = []

        parent_id: str | None = parent_message_id

        while parent_id:
            message = self._assert_not_none(
                all_messages.get(parent_id),
                f'message {parent_id} is present in DB'
            )

            messages.append(message)
            parent_id = message.get('parentId')

        return messages[::-1]

    @staticmethod
    def _get_message_text(message: dict) -> str:
        """Extract text from Open WebUI and Responses API message formats."""

        content = message.get('content', '')
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, dict):
            text = content.get('text')
            return text.strip() if isinstance(text, str) else ''

        if not isinstance(content, list):
            return ''

        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                text = part.get('text')
                if isinstance(text, str):
                    text_parts.append(text)

        return '\n'.join(text_parts).strip()

    def _match_messages_with_files(
        self,
        responses_messages: list[dict],
        stored_messages: list[dict],
    ) -> list[tuple[dict, dict]]:
        """Match stored file attachments to messages present in the request.

        Open WebUI context compaction removes old messages and inserts a synthetic
        summary system message. It can also expand structured assistant output into
        several request messages, so list lengths and positions are not stable.
        """

        matches: list[tuple[dict, dict]] = []
        response_cursor = len(responses_messages) - 1

        for stored_index in range(len(stored_messages) - 1, -1, -1):
            stored_message = stored_messages[stored_index]
            stored_role = stored_message.get('role')
            stored_text = self._get_message_text(stored_message)
            matched_index: int | None = None

            for response_index in range(response_cursor, -1, -1):
                response_message = responses_messages[response_index]
                if response_message.get('role') != stored_role:
                    continue
                if self._get_message_text(response_message) == stored_text:
                    matched_index = response_index
                    break

            is_current_user_message = (
                stored_index == len(stored_messages) - 1
                and stored_role == 'user'
            )
            if matched_index is None and is_current_user_message:
                # Inlet filters may modify the current user message text. The last
                # user request still corresponds to metadata["user_message_id"].
                for response_index in range(response_cursor, -1, -1):
                    if responses_messages[response_index].get('role') == 'user':
                        matched_index = response_index
                        break

            if matched_index is None:
                # The message was compacted out or transformed beyond safe matching.
                continue

            response_cursor = matched_index - 1
            if stored_message.get('files'):
                matches.append((responses_messages[matched_index], stored_message))

        matches.reverse()
        return matches

    async def _upload_if_not_exists(
        self,
        client: AsyncOpenAI,
        event_emitter: EventEmitterType,
        webui_file_id: str,
        file_path: str,
        file_name: str,
    ) -> str:
        async with self._files_lock:
            if file_id := self._files_cache.get(webui_file_id):
                try:
                    await client.files.retrieve(file_id)
                except NotFoundError:
                    pass
                else:
                    return file_id
            with open(file_path, 'rb') as file_data:
                await self._emit_status(event_emitter, f'Uploading file {file_name}...')
                uploaded_file = await client.files.create(
                    file=file_data,
                    purpose='assistants'
                )

            file_id = self._files_cache[webui_file_id] = uploaded_file.id
            return file_id

    async def _get_file_ids(
        self,
        client: AsyncOpenAI,
        event_emitter: EventEmitterType,
        files: list[dict]
    ) -> list[str]:
        ids = []
        for file in files:
            webui_file_id: str = self._assert_not_none(file.get('id'), 'file_id')
            file_info: dict = self._assert_not_none(file.get('file'), 'file info')
            file_path: str = self._assert_not_none(file_info.get('path'), 'file path')
            file_name: str = self._assert_not_none(file.get('name'), 'file_name')
            file_id = await self._upload_if_not_exists(client, event_emitter, webui_file_id, file_path, file_name)
            ids.append(file_id)

        return ids

    def _check_file_context_enabled(self, metadata: dict) -> bool:
        model = metadata.get('model', {})
        model_info = model.get('info', {})
        meta = model_info.get('meta', {})
        capabilities = meta.get('capabilities') or {}
        file_context_enabled = capabilities.get('file_context', True)

        return file_context_enabled

    # pylint: disable=too-many-locals
    async def _get_responses_kwargs(
        self,
        client: AsyncOpenAI,
        body: dict,
        files: list[dict],
        metadata: dict,
        task_name: str | None,
        event_emitter: EventEmitterType,
    ) -> dict:
        # open-webui doing smth with body after calling a pipe,
        # but convert_to_responses_payload modifies it
        body = copy.deepcopy(body)
        responses_kwargs = convert_to_responses_payload(body)
        self._fixup_input_images(responses_kwargs)
        responses_kwargs.pop("stream", None)

        # task_name exists means it is not main request, but some kind of sub-request
        # like "follow up generation"
        # It is probably not right to not to attach files here, but it requires additional
        # testing I don't want to do right now
        if task_name:
            return responses_kwargs

        # if there is no attached files, we do not need to do anything anymore
        if not files:
            return responses_kwargs

        # if there are Open WebUI RAG enabled, it is heavily interferes
        # with our wish to get and upload files;
        # also in this case Open WebUI modifies original user request
        # with RAG data.
        if self._check_file_context_enabled(metadata):
            if self.valves.SILENT_FILES_WARNING:
                return responses_kwargs

            await self._emit_notification(
                event_emitter, 'warning',
                (
                    'Attached files will not be used in AIStudio requests due to '
                    'enabled Open WebUI RAG feature; '
                    'you can turn off the "File Context" feature in WebUI model settings.'
                )
            )
            await self._emit_status(event_emitter, 'Skipping file usage in AIStudio...')
            return responses_kwargs

        full_message_list = await self._get_full_message_list(metadata)

        input_ = self._assert_not_none(responses_kwargs.get('input'), "input field must be present")

        message_matches = self._match_messages_with_files(input_, full_message_list)

        for responses_message, full_message in message_matches:
            if attached_files := full_message.get('files'):
                file_ids = await self._get_file_ids(client, event_emitter, attached_files)

                # NB: we are modifying content list in-place
                content: list[dict] = self._assert_not_none(
                    responses_message.get('content'),
                    'responses input content'
                )
                for file_id in reversed(file_ids):
                    file_dict = {
                        'type': 'input_file',
                        'file_id': file_id,
                    }
                    content.insert(0, file_dict)

        return responses_kwargs

    async def _upload_file_to_webui(
        self,
        *,
        event_emitter: EventEmitterType,
        request: Request,
        user: dict,
        metadata: dict,
        filename: str,
        content: bytes,
        content_type: str | None = None
    ) -> FileModel:
        chat_id = self._assert_not_none(metadata.get('chat_id'), 'chat_id')
        message_id = self._assert_not_none(metadata.get('message_id'), 'message_id')
        session_id = self._assert_not_none(metadata.get('session_id'), 'session_id')

        file_headers = {}
        if not content_type:
            file_extension = filename.rsplit('.', 1)[0]
            content_type = {
                'csv': 'text/csv',
                'txt': 'text/plain',
                'py': 'text/x-python',
            }.get(file_extension)

        if content_type:
            file_headers['content-type'] = content_type

        kwargs = {
            'request': request,
            'file': UploadFile(
                file=io.BytesIO(content),
                filename=filename,
                headers=file_headers,  # ty: ignore[invalid-argument-type]
            ),
            'process': False,
            'process_in_background': False,
            'user': UserModel.model_validate(user),
            'metadata': {
                'chat_id': chat_id,
                'message_id': message_id,
                'session_id': session_id,
            },
        }
        await self._emit_status(event_emitter, f'Uploading {filename} to WebUI....')
        result = await upload_file_handler(**kwargs)  # ty: ignore[invalid-argument-type]
        return result

    async def _attach_files_to_webui(
        self,
        event_emitter: EventEmitterType,
        request: Request,
        user: dict,
        metadata: dict,
        files: list[tuple[str, bytes]]
    ) -> None:
        uploaded_files: list[FileModel] = []
        urls: list[str] = []

        for filename, content in files:
            uploaded_file = await self._upload_file_to_webui(
                event_emitter=event_emitter,
                request=request,
                user=user,
                metadata=metadata,
                filename=filename,
                content=content
            )
            uploaded_files.append(uploaded_file)

            url = str(request.app.url_path_for('get_file_content_by_id', id=uploaded_file.id))
            urls.append(url)

        for uploaded_file, file_url, (filename, content) in zip(
            uploaded_files, urls, files
        ):
            text = ''
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                pass

            # random big number to not to send to browser too much data
            if len(text) > TEXT_TRIM_LENGTH:
                text = f"{text[:TEXT_TRIM_LENGTH]}<trimmed>"

            await event_emitter({
                "type": "citation",
                "data": {
                    "document": [text],
                    "metadata": [
                        {
                            "source": file_url,
                            'file_id': uploaded_file.id,
                        }

                    ],
                    "source": {
                        "name": filename,
                        "url": file_url,
                        "id": uploaded_file.id,
                        "type": "file",
                    },
                }
            })

    async def _event_emit_dummy(self, data: dict) -> None:
        pass

    async def pipe(
        self,
        body: dict,
        __files__: list[dict] | None = None,
        __metadata__: dict | None = None,
        __event_emitter__: EventEmitterType | None = None,
        __task__: str | None = None,
        __request__: Request | None = None,
        __user__: dict | None = None,
    ) -> AsyncGenerator[str]:
        event_emitter = __event_emitter__ or self._event_emit_dummy
        metadata = self._assert_not_none(__metadata__, 'request metadata')
        user = self._assert_not_none(__user__, 'user')
        request = self._assert_not_none(__request__, 'request')

        client = self._get_client()

        responses_kwargs = await self._get_responses_kwargs(
            client=client,
            body=body,
            files=__files__ or [],
            metadata=metadata,
            task_name=__task__,
            event_emitter=event_emitter,
        )

        raw_model_id = body.get("model")
        _raw_model_id = self._assert_not_none(raw_model_id, "model_id not None")
        model_id = _raw_model_id.split(".", 1)[-1]
        assistant_id = model_id.rsplit("/", 1)[-1]

        responses_kwargs["model"] = model_id

        last_status_name: str | None = None
        code_generated_index = 0

        async with client:
            try:
                async with client.responses.stream(
                    prompt={"id": assistant_id}, **responses_kwargs
                ) as stream:
                    async for event in stream:
                        if event.type == "response.output_text.delta":
                            assert isinstance(event, ResponseTextDeltaEvent)
                            yield event.delta

                        if event.type == 'response.output_item.done':
                            assert isinstance(event, ResponseOutputItemDoneEvent)
                            await self._process_annotations(
                                client=client,
                                event_emitter=event_emitter,
                                event=event,
                                request=request,
                                user=user,
                                metadata=metadata,
                            )
                        if event.type == 'response.code_interpreter_call_code.done':
                            assert isinstance(event, ResponseCodeInterpreterCallCodeDoneEvent)

                            if not __task__:
                                code = event.code
                                await self._attach_files_to_webui(
                                    event_emitter=event_emitter,
                                    request=request,
                                    user=user,
                                    metadata=metadata,
                                    files=[
                                        (f'generated_code{code_generated_index}.py', code.encode('utf-8'))
                                    ]
                                )
                                code_generated_index += 1

                        if event.type in SILENT_STATUSES:
                            continue

                        event_type = __task__ or event.type
                        status_name = STATUS_NAMES.get(event_type, event_type)
                        if status_name != last_status_name:
                            last_status_name = status_name
                            await self._emit_status(event_emitter, status_name)
            except openai.BadRequestError as e:
                raise openai.BadRequestError(
                    message=f'{e.message};\n Responses kwargs: {responses_kwargs}',
                    response=e.response,
                    body=e.body
                ) from e

        await self._emit_status(event_emitter, 'Done', done=True)

        return

    def _validate_configuration(self) -> None:
        # pylint: disable-next=no-member
        if not self.valves.YANDEX_CLOUD_API_KEY.strip():
            raise ValueError("Yandex Cloud API Key is required")

        # pylint: disable-next=no-member
        if not self.valves.YANDEX_CLOUD_FOLDER_ID.strip():
            raise ValueError("Yandex Cloud Folder ID is required")

        ids = self.valves.AGENT_IDS
        if not ids:
            raise ValueError("Add at least one agent ID into Agent Ids Valve")

        names = self.valves.AGENT_NAMES
        if names and len(names) != len(ids):
            raise ValueError("Number of Agent names must match number of Agent Ids")
