"""Gemini API client for news processing."""

import logging
import json
import uuid
import tempfile
import mimetypes
import base64
from pathlib import Path
from urllib.parse import urlparse

import google.genai as genai
from google.genai import types
import httpx
from pydantic import BaseModel, Field, ValidationError

from app.ai.base import BaseAIClient
from app.schemas.newspaper import NewsItemNewspaperAIResponse
from app.schemas.ai_debug import AICaptionEntry
from app.models.newspaper import Newspaper


logger = logging.getLogger(__name__)


AUDIO_TRANSCRIPTION_PROMPT = (
    "Transcribe this audio and return strict JSON with shape: "
    '{"captions":[{"caption":string,"startTime":number,"endTime":number}]}. '
    "Use seconds for timings. Keep caption lines concise. "
    "Keep prepositions and pronouns with the words they belong to and "
    "do not leave them hanging at the end of a caption line."
)


class _AudioTranscriptionResponse(BaseModel):
    captions: list[AICaptionEntry] = Field(default_factory=list)


class _AudioContentURI(BaseModel):
    type: str = "audio"
    uri: str
    mime_type: str


class _AudioContentInline(BaseModel):
    type: str = "audio"
    data: str
    mime_type: str


class _TextContent(BaseModel):
    type: str = "text"
    text: str


class GeminiClient(BaseAIClient):
    """Client for interacting with Gemini API."""

    MODEL_NAME = "gemini-3.1-flash-lite"
    AUDIO_MODEL_NAME = "gemini-3.6-flash"
    CAPTION_MAX_CHARS_PER_LINE = 25
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav"}
    SUPPORTED_AUDIO_MIME_TYPES = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
    }
    MIME_CANDIDATES_BY_SUFFIX = {
        ".wav": ["audio/wav"],
        ".mp3": ["audio/mpeg", "audio/mp3"],
    }

    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        """Initialize Gemini client with API key.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        super().__init__(model_name)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    async def process_newspaper(
        self,
        prompt: str,
    ) -> Newspaper | None:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self._fix_schema_for_gemini(
                    NewsItemNewspaperAIResponse.model_json_schema()
                ),
            ),
        )
        return response.text

    async def generate_text_response(self, prompt: str) -> str:
        """Generate a text response from Gemini API.

        Args:
            prompt: The prompt to send to the Gemini API.
        """
        response = self.client.interactions.create(
            model=self.model_name,
            input=prompt,
        )
        return response.output_text

    async def _generate(
        self, system_instruction: str, user_message: str
    ) -> tuple[str, int]:
        """Call Gemini API and return (response_text, tokens_used)."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "boolean"},
                        "thinking": {"type": "string"},
                    },
                    "required": ["result", "thinking"],
                },
            ),
        )
        return response.text, self._count_tokens(response)

    def _count_tokens(self, response) -> int:
        """Count tokens used in the response."""
        usage_metadata = response.usage_metadata
        if not usage_metadata:
            return 0
        return (
            usage_metadata.prompt_token_count
            + usage_metadata.candidates_token_count
        )

    def _fix_schema_for_gemini(self, schema: dict) -> dict:
        """Convert tuple prefixItems notation to items.
        Gemini SDK doesn't support prefixItems.

        """
        if isinstance(schema, dict):
            if "prefixItems" in schema:
                item_types = schema["prefixItems"]
                schema = {
                    k: v for k, v in schema.items() if k != "prefixItems"
                }
                schema["items"] = item_types[0] if item_types else {}
            return {
                k: self._fix_schema_for_gemini(v) for k, v in schema.items()
            }
        if isinstance(schema, list):
            return [self._fix_schema_for_gemini(item) for item in schema]
        return schema

    async def transcribe_audio_to_videoflow_captions(
        self,
        audio_url: str,
        output_dir: str = "/app/tmp/downloads",
    ) -> tuple[list[dict], str]:
        """Transcribe audio and return VideoFlow captions + JSON file URL."""
        audio_bytes, content_type = await self._download_file(audio_url)
        parsed = urlparse(audio_url)
        suffix = self._resolve_audio_suffix(
            filename=Path(parsed.path).name,
            content_type=content_type,
        )
        return await self.transcribe_audio_file_to_videoflow_captions(
            audio_bytes,
            filename=f"audio{suffix}",
            content_type=content_type,
            output_dir=output_dir,
        )

    async def transcribe_audio_file_to_videoflow_captions(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        content_type: str | None = None,
        output_dir: str = "/app/tmp/downloads",
    ) -> tuple[list[dict], str]:
        """Transcribe uploaded audio bytes and return VideoFlow captions."""
        suffix = self._resolve_audio_suffix(
            filename=filename,
            content_type=content_type,
        )
        mime_type = self._resolve_audio_mime_type(
            suffix=suffix,
            content_type=content_type,
        )

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            temp.write(audio_bytes)
            temp_path = temp.name

        try:
            uploaded_file = self.client.files.upload(file=temp_path)
            uploaded_mime_type = self._resolve_audio_mime_type(
                suffix=suffix,
                content_type=uploaded_file.mime_type or mime_type,
            )
            mime_candidates = self._build_mime_candidates(
                suffix=suffix,
                preferred=uploaded_mime_type,
            )

            interaction = self._create_audio_interaction_with_fallbacks(
                mime_candidates=mime_candidates,
                audio_uri=uploaded_file.uri,
                audio_bytes=audio_bytes,
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

        response_json = self._extract_json_object(
            interaction.output_text or ""
        )
        captions = self._parse_and_limit_captions(
            response_json,
            self.CAPTION_MAX_CHARS_PER_LINE,
        )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_name = f"captions_{uuid.uuid4()}.json"
        file_path = output_path / file_name
        file_path.write_text(
            json.dumps({"captions": captions}, ensure_ascii=True),
            encoding="utf-8",
        )

        return captions, f"/api/download/files/{file_name}"

    def _build_mime_candidates(
        self, *, suffix: str, preferred: str
    ) -> list[str]:
        candidates = [preferred]
        candidates.extend(self.MIME_CANDIDATES_BY_SUFFIX.get(suffix, []))
        deduped: list[str] = []
        for candidate in candidates:
            if candidate not in deduped:
                deduped.append(candidate)
        return deduped

    def _create_audio_interaction_with_fallbacks(
        self,
        *,
        mime_candidates: list[str],
        audio_uri: str,
        audio_bytes: bytes,
    ):
        last_error: Exception | None = None

        for candidate_mime_type in mime_candidates:
            try:
                return self.client.interactions.create(
                    model=self.AUDIO_MODEL_NAME,
                    input=[
                        _TextContent(
                            text=AUDIO_TRANSCRIPTION_PROMPT
                        ).model_dump(),
                        _AudioContentURI(
                            uri=audio_uri,
                            mime_type=candidate_mime_type,
                        ).model_dump(),
                    ],
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if not self._is_mime_related_error(exc):
                    raise

        inline_audio_data = base64.b64encode(audio_bytes).decode("ascii")
        for candidate_mime_type in mime_candidates:
            try:
                return self.client.interactions.create(
                    model=self.AUDIO_MODEL_NAME,
                    input=[
                        _TextContent(
                            text=AUDIO_TRANSCRIPTION_PROMPT
                        ).model_dump(),
                        _AudioContentInline(
                            data=inline_audio_data,
                            mime_type=candidate_mime_type,
                        ).model_dump(),
                    ],
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if not self._is_mime_related_error(exc):
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Failed to create audio transcription request")

    def _is_mime_related_error(self, error: Exception) -> bool:
        message = str(error).lower()
        return "mime_type" in message or "invalid argument" in message

    def _parse_and_limit_captions(
        self,
        response_json: dict,
        max_chars_per_line: int,
    ) -> list[dict]:
        try:
            parsed = _AudioTranscriptionResponse.model_validate(response_json)
            captions: list[dict] = [
                item.model_dump() for item in parsed.captions
            ]
        except ValidationError:
            raw_captions = response_json.get("captions", [])
            if isinstance(raw_captions, list):
                captions = [
                    item for item in raw_captions if isinstance(item, dict)
                ]
            else:
                captions = []

        return self._limit_caption_line_length(captions, max_chars_per_line)

    async def _download_file(self, file_url: str) -> tuple[bytes, str | None]:
        parsed = urlparse(file_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("audio_url must be an absolute URL")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(file_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            if content_type:
                content_type = content_type.split(";")[0].strip().lower()
            return response.content, content_type

    def _resolve_audio_suffix(
        self,
        *,
        filename: str,
        content_type: str | None,
    ) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in self.SUPPORTED_AUDIO_EXTENSIONS:
            return suffix

        if content_type:
            normalized_mime = content_type.lower()
            if normalized_mime in {"audio/wav", "audio/x-wav", "audio/wave"}:
                return ".wav"
            if normalized_mime in {"audio/mpeg", "audio/mp3"}:
                return ".mp3"

        raise ValueError(
            "Only .mp3 and .wav audio files are supported for transcription"
        )

    def _resolve_audio_mime_type(
        self,
        *,
        suffix: str,
        content_type: str | None,
    ) -> str:
        if content_type:
            normalized_mime = content_type.lower()
            if normalized_mime in self.SUPPORTED_AUDIO_MIME_TYPES:
                if normalized_mime in {"audio/x-wav", "audio/wave"}:
                    return "audio/wav"
                if normalized_mime == "audio/mp3":
                    return "audio/mpeg"
                return normalized_mime

        mime_type, _ = mimetypes.guess_type(f"sample{suffix}")
        if mime_type and mime_type.lower() in self.SUPPORTED_AUDIO_MIME_TYPES:
            if mime_type.lower() in {"audio/x-wav", "audio/wave"}:
                return "audio/wav"
            if mime_type.lower() == "audio/mp3":
                return "audio/mpeg"
            return mime_type.lower()

        if suffix == ".wav":
            return "audio/wav"
        return "audio/mpeg"

    def _extract_json_object(self, text: str) -> dict:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}

        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}

        return {}

    def _limit_caption_line_length(
        self,
        captions: list[dict],
        max_chars_per_line: int,
    ) -> list[dict]:
        limited: list[dict] = []
        for caption_item in captions:
            text = caption_item.get("caption")
            start_time = caption_item.get("startTime")
            end_time = caption_item.get("endTime")

            if not isinstance(text, str):
                limited.append(caption_item)
                continue

            normalized_text = " ".join(text.strip().split())
            if not normalized_text:
                limited.append(caption_item)
                continue

            chunks = self._split_caption_into_single_line_chunks(
                normalized_text,
                max_chars_per_line,
            )
            if len(chunks) == 1:
                limited.append({**caption_item, "caption": chunks[0]})
                continue

            if (
                not isinstance(start_time, (int, float))
                or not isinstance(end_time, (int, float))
                or end_time <= start_time
            ):
                limited.extend(
                    [{**caption_item, "caption": chunk} for chunk in chunks]
                )
                continue

            total_duration = float(end_time) - float(start_time)
            total_chars = sum(len(chunk) for chunk in chunks) or len(chunks)
            cursor = float(start_time)
            for idx, chunk in enumerate(chunks):
                if idx == len(chunks) - 1:
                    chunk_end = float(end_time)
                else:
                    ratio = len(chunk) / total_chars
                    chunk_end = cursor + total_duration * ratio
                limited.append(
                    {
                        **caption_item,
                        "caption": chunk,
                        "startTime": cursor,
                        "endTime": chunk_end,
                    }
                )
                cursor = chunk_end

        return limited

    def _split_caption_into_single_line_chunks(
        self,
        text: str,
        max_chars_per_line: int,
    ) -> list[str]:
        words = text.split(" ")
        chunks: list[str] = []
        current = ""

        for word in words:
            if len(word) > max_chars_per_line:
                if current:
                    chunks.append(current)
                    current = ""
                for i in range(0, len(word), max_chars_per_line):
                    chunks.append(word[i : i + max_chars_per_line])
                continue

            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars_per_line:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = word

        if current:
            chunks.append(current)

        return chunks or [text[:max_chars_per_line]]
