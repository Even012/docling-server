import base64
import logging
import mimetypes
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from docling_worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# Matches markdown image syntax: ![alt text](url)
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Max size per image to embed (2 MB); larger images are dropped.
_MAX_IMAGE_SIZE = 2 * 1024 * 1024


def _embed_images(markdown: str, output_dir: Path) -> str:
    """Replace local image paths in markdown with base64 data URIs.

    Images already using http(s) or data: URLs are left untouched.
    Images exceeding ``_MAX_IMAGE_SIZE`` are silently removed.
    """

    def _replace(m: re.Match) -> str:
        alt = m.group(1)
        src = m.group(2).strip()

        # Keep remote URLs and existing data URIs
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)

        img_path = (output_dir / src).resolve()

        # Security: must be under output_dir
        resolved_base = output_dir.resolve()
        if resolved_base not in img_path.parents and img_path != resolved_base:
            return ""

        if not img_path.is_file():
            return ""

        if img_path.stat().st_size > _MAX_IMAGE_SIZE:
            return ""

        mime = mimetypes.guess_type(str(img_path))[0] or "image/png"
        b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        return f"![{alt}](data:{mime};base64,{b64})"

    return _IMAGE_RE.sub(_replace, markdown)


def _require_under_dir(path: Path, base_dir: Path) -> Path:
    path = path.resolve()
    base_dir = base_dir.resolve()
    if base_dir not in path.parents and path != base_dir:
        raise ValueError(f"Path must be under {base_dir}: {path}")
    return path


@celery_app.task(name="docling.convert", bind=True)
def convert(self, *, input: str, output_subdir: str | None = None, extra_args: list[str] | None = None) -> dict[str, Any]:
    """
    Convert a document using the `docling` CLI.

    - input: either a URL (http/https) or a file path under DOCLING_INPUT_DIR
    - output_subdir: subfolder under DOCLING_OUTPUT_DIR (defaults to celery task id)
    - extra_args: list of additional CLI args to pass to `docling`
    """
    input_dir = Path(os.getenv("DOCLING_INPUT_DIR", "/app/documents"))
    output_dir = Path(os.getenv("DOCLING_OUTPUT_DIR", "/app/output"))

    out_subdir = output_subdir or (self.request.id or "job")
    out_dir = (output_dir / out_subdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    is_url = input.startswith("http://") or input.startswith("https://")
    input_arg: str

    # Log the file source being processed
    if is_url:
        # Extract readable OSS key from presigned URL path
        parsed = urlparse(input)
        oss_path = unquote(parsed.path).lstrip("/")
        logger.info(
            "[docling.convert] task=%s source=URL oss_path=%s",
            self.request.id,
            oss_path,
        )
        input_arg = input
    else:
        in_path = _require_under_dir((input_dir / input).resolve(), input_dir)
        if not in_path.exists():
            raise FileNotFoundError(f"Input file not found: {in_path}")
        logger.info(
            "[docling.convert] task=%s source=FILE path=%s",
            self.request.id,
            in_path,
        )
        input_arg = str(in_path)

    cmd: list[str] = ["docling", input_arg, "--output", str(out_dir), "--ocr-engine", "rapidocr"]
    if extra_args:
        cmd.extend(extra_args)

    logger.info("[docling.convert] task=%s running: %s", self.request.id, " ".join(shlex.quote(c) for c in cmd))
    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.monotonic() - t0

    logger.info(
        "[docling.convert] task=%s finished in %.1fs returncode=%d",
        self.request.id,
        elapsed,
        proc.returncode,
    )
    if proc.returncode != 0:
        logger.error(
            "[docling.convert] task=%s stderr: %s",
            self.request.id,
            proc.stderr[-2000:] if proc.stderr else "(empty)",
        )

    # Read converted markdown from output directory
    markdown_content = None
    if proc.returncode == 0:
        md_files = sorted(out_dir.glob("*.md"))
        if md_files:
            parts = []
            for md_path in md_files:
                try:
                    parts.append(md_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            markdown_content = "\n\n".join(parts) if parts else None

    # Embed extracted images as base64 data URIs
    if markdown_content:
        image_count = len(_IMAGE_RE.findall(markdown_content))
        markdown_content = _embed_images(markdown_content, out_dir)
        logger.info(
            "[docling.convert] task=%s markdown=%d chars, %d images embedded",
            self.request.id,
            len(markdown_content),
            image_count,
        )
    else:
        logger.warning("[docling.convert] task=%s no markdown output produced", self.request.id)

    return {
        "cmd": " ".join(shlex.quote(c) for c in cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-20000:],
        "stderr": proc.stderr[-20000:],
        "output_dir": str(out_dir),
        "ok": proc.returncode == 0,
        "markdown": markdown_content,
    }

