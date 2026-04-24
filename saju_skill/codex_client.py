"""Subprocess wrapper around `codex responses` using the user's OAuth session."""
from __future__ import annotations

import base64
import json
import os
import subprocess
from pathlib import Path


class CodexAuthError(RuntimeError):
    """Raised when Codex OAuth is unavailable."""


class CodexCallError(RuntimeError):
    """Raised when `codex responses` fails or returns an unexpected payload."""


class CodexClient:
    def __init__(self, codex_bin: str = "codex", timeout_sec: int = 900):
        self.codex_bin = codex_bin
        self.timeout_sec = timeout_sec
        self._verify_login()

    def _verify_login(self) -> None:
        if os.getenv("CODEX_API_KEY"):
            raise CodexAuthError(
                "`CODEX_API_KEY` is set. Unset it so `codex responses` uses the "
                "active ChatGPT/OAuth session."
            )
        try:
            result = subprocess.run(
                [self.codex_bin, "login", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError as e:
            raise CodexAuthError(
                f"`{self.codex_bin}` not found on PATH. Install Codex CLI first."
            ) from e
        if result.returncode != 0:
            raise CodexAuthError(
                f"`codex login status` failed (exit={result.returncode}). "
                f"Run `codex login` and choose ChatGPT/OAuth. stderr={result.stderr.strip()}"
            )

    def call_responses(
        self,
        *,
        model: str,
        instructions: str,
        messages: list[dict],
        response_format: dict | None = None,
    ) -> str:
        payload: dict = {
            "model": model,
            "instructions": instructions,
            "input": messages,
            "stream": True,
            "store": False,
        }
        if response_format:
            payload["text"] = {"format": response_format}
        return self._run_and_extract_text(payload)

    def generate_image(
        self,
        *,
        orchestrator_model: str,
        prompt: str,
        size: tuple[int, int],
        quality: str = "high",
    ) -> bytes:
        payload = {
            "model": orchestrator_model,
            "instructions": (
                "Create a premium vertical Korean fortune-card background. "
                "No readable text, no letters, no numbers. Leave clean whitespace "
                "for later text overlay."
            ),
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                }
            ],
            "tools": [
                {
                    "type": "image_generation",
                    "size": f"{size[0]}x{size[1]}",
                    "quality": quality,
                }
            ],
            "tool_choice": {"type": "image_generation"},
            "stream": True,
            "store": False,
        }
        return self._run_and_extract_image(payload)

    def _run_and_extract_text(self, payload: dict) -> str:
        proc = self._run_responses(payload)
        deltas: list[str] = []
        completed = False
        for line in proc.stdout.splitlines():
            event = _json_line(line)
            if not event:
                continue
            event_type = event.get("type", "")
            if event_type == "response.output_text.delta":
                deltas.append(event.get("delta", ""))
            elif event_type == "response.completed":
                completed = True
                break
        if not completed:
            raise CodexCallError(
                f"stream ended without response.completed (stdout={len(proc.stdout)} bytes)"
            )
        return "".join(deltas)

    def _run_and_extract_image(self, payload: dict) -> bytes:
        proc = self._run_responses(payload)
        for line in proc.stdout.splitlines():
            event = _json_line(line)
            if not event:
                continue
            if event.get("type") != "response.output_item.done":
                continue
            item = event.get("item", {})
            if item.get("type") == "image_generation_call" and item.get("result"):
                return base64.b64decode(item["result"])
        raise CodexCallError(
            f"no image_generation_call.result in stdout (stdout={len(proc.stdout)} bytes)"
        )

    def _run_responses(self, payload: dict) -> subprocess.CompletedProcess[str]:
        try:
            proc = subprocess.run(
                [self.codex_bin, "responses"],
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
            )
        except FileNotFoundError as e:
            raise CodexCallError(f"`{self.codex_bin}` not found on PATH.") from e
        if proc.returncode != 0:
            raise CodexCallError(
                f"codex responses exit={proc.returncode}: {proc.stderr.strip()[:700]}"
            )
        return proc


def _json_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def write_bytes(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path

