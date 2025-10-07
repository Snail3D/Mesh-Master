"""Storage helpers for user-authored reports and logs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import json
import threading

try:
    from unidecode import unidecode
except Exception:  # pragma: no cover
    def unidecode(value: str) -> str:  # type: ignore
        return value


@dataclass
class UserEntryRecord:
    """A saved user-authored note (report/log)."""

    title: str
    content: str
    summary: str
    author: str
    author_id: Optional[str]
    created_at: str
    language: Optional[str] = None
    group: Optional[str] = None


@dataclass
class _IndexEntry:
    key: str
    title: str
    path: Path
    summary: str
    author: str
    author_id: Optional[str]
    created_at: str
    language: Optional[str]
    group: Optional[str]


class UserEntryStore:
    """Stores user-provided reports/logs with a lightweight index."""

    def __init__(self, index_file: Path, *, base_dir: Optional[Path] = None) -> None:
        self.index_file = Path(index_file)
        self.base_dir = Path(base_dir) if base_dir else self.index_file.parent
        self._entries: Dict[str, _IndexEntry] = {}
        self._lock = threading.RLock()
        self._loaded = False
        self._load_error: Optional[str] = None
        self._load_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_ready(self) -> bool:
        return self._loaded and not self._load_error

    def error_message(self) -> Optional[str]:
        return self._load_error

    def list_entries(self) -> List[Dict[str, object]]:
        with self._lock:
            if not self._loaded:
                self._load_index()
            result: List[Dict[str, object]] = []
            for entry in sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True):
                try:
                    st = entry.path.stat()
                    size = int(getattr(st, "st_size", 0))
                except Exception:
                    size = 0
                rel_path = entry.path
                try:
                    rel_path = entry.path.relative_to(self.base_dir)
                except Exception:
                    rel_path = entry.path
                result.append(
                    {
                        "key": entry.key,
                        "title": entry.title,
                        "summary": entry.summary,
                        "author": entry.author,
                        "author_id": entry.author_id,
                        "created_at": entry.created_at,
                        "language": entry.language or "",
                        "group": entry.group or "",
                        "path": rel_path.as_posix(),
                        "size_bytes": size,
                    }
                )
            return result

    def lookup(self, key: str) -> Optional[UserEntryRecord]:
        normalized = _normalize(key)
        if not normalized:
            return None
        with self._lock:
            if not self._loaded:
                self._load_index()
            entry = self._entries.get(normalized)
            if not entry:
                return None
            try:
                with entry.path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                return None
            return UserEntryRecord(
                title=data.get("title") or entry.title,
                content=data.get("content") or "",
                summary=data.get("summary") or entry.summary,
                author=data.get("author") or entry.author,
                author_id=data.get("author_id") or entry.author_id,
                created_at=data.get("created_at") or entry.created_at,
                language=data.get("language") or entry.language,
                group=data.get("group") or entry.group,
            )

    def delete(self, key: str) -> bool:
        normalized = _normalize(key)
        if not normalized:
            return False
        with self._lock:
            if not self._loaded:
                self._load_index()
            entry = self._entries.get(normalized)
            if not entry:
                return False
            try:
                entry.path.unlink(missing_ok=True)
            except Exception:
                pass
            self._entries.pop(normalized, None)
            self._write_index()
            self._load_error = None
            return True

    def prune_by_max(self, max_entries: int) -> Dict[str, int]:
        max_entries = max(0, int(max_entries))
        with self._lock:
            if not self._loaded:
                self._load_index()
            items = list(self._entries.items())
            before = len(items)
            if before <= max_entries:
                return {"before": before, "removed": 0, "after": before}
            items.sort(key=lambda kv: kv[1].created_at)
            removed = 0
            for key, entry in items[: before - max_entries]:
                try:
                    entry.path.unlink(missing_ok=True)
                except Exception:
                    pass
                self._entries.pop(key, None)
                removed += 1
            self._write_index()
            after = len(self._entries)
            return {"before": before, "removed": removed, "after": after}

    def store_entry(
        self,
        *,
        title: str,
        content: str,
        author: str,
        author_id: Optional[str],
        language: Optional[str] = None,
        aliases: Optional[Iterable[str]] = None,
    ) -> Dict[str, str]:
        if not title or not content:
            return {}
        timestamp = datetime.now(tz=timezone.utc)
        created_iso = timestamp.isoformat()
        slug = _slugify(title)
        key = _normalize(f"{slug} {created_iso}")
        rel_path = Path(f"{slug}-{timestamp.strftime('%Y%m%dT%H%M%S')}.json")
        target = self.base_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        summary = _clip_text(content, 240)
        payload = {
            "title": title,
            "content": content,
            "summary": summary,
            "author": author,
            "author_id": author_id,
            "created_at": created_iso,
            "language": language,
            "group": slug,
            "aliases": list(aliases or []),
        }
        with self._lock:
            with target.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")
            entry = _IndexEntry(
                key=key,
                title=title,
                path=target,
                summary=summary,
                author=author,
                author_id=author_id,
                created_at=created_iso,
                language=language,
                group=slug,
            )
            self._entries[key] = entry
            self._write_index()
            self._load_error = None
            return {"key": key, "slug": slug, "created_at": created_iso}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _load_index(self) -> None:
        if self._loaded:
            return
        try:
            if not self.index_file.is_file():
                self._entries.clear()
                self._loaded = True
                self._load_error = "Index missing"
                return
            with self.index_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self._entries.clear()
            self._loaded = True
            self._load_error = "Index missing"
            return
        except Exception as exc:
            self._entries.clear()
            self._loaded = True
            self._load_error = f"Failed to load index: {exc}"
            return

        entries_raw = data.get("entries") if isinstance(data, dict) else []
        entries: Dict[str, _IndexEntry] = {}
        for item in entries_raw or []:
            if not isinstance(item, dict):
                continue
            key = _normalize(item.get("key"))
            title = item.get("title") or ""
            path_raw = item.get("path") or ""
            summary = item.get("summary") or ""
            author = item.get("author") or "Unknown"
            author_id = item.get("author_id")
            created_at = item.get("created_at") or datetime.now(tz=timezone.utc).isoformat()
            language = item.get("language") or None
            group = item.get("group") or None
            if not key or not path_raw:
                continue
            path = self.base_dir / Path(path_raw)
            entries[key] = _IndexEntry(
                key=key,
                title=title,
                path=path,
                summary=summary,
                author=author,
                author_id=author_id,
                created_at=created_at,
                language=language,
                group=group,
            )
        self._entries = entries
        self._loaded = True
        self._load_error = None

    def _write_index(self) -> None:
        entries = []
        for entry in sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True):
            rel_path = entry.path
            try:
                rel_path = entry.path.relative_to(self.base_dir)
            except Exception:
                rel_path = entry.path
            entries.append(
                {
                    "key": entry.key,
                    "title": entry.title,
                    "summary": entry.summary,
                    "author": entry.author,
                    "author_id": entry.author_id,
                    "created_at": entry.created_at,
                    "language": entry.language,
                    "group": entry.group,
                    "path": rel_path.as_posix(),
                }
            )
        payload = {"entries": entries}
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with self.index_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")


def _normalize(value: Optional[str]) -> str:
    if not value:
        return ""
    lowered = unidecode(str(value)).lower()
    return " ".join(lowered.split())


def _slugify(value: str) -> str:
    slug = unidecode(value or "").lower()
    slug = slug.replace("'", "")
    slug = slug.replace("\"", "")
    slug = slug.replace("/", " ")
    slug = slug.replace("\\", " ")
    slug = "".join(ch if ch.isalnum() else "-" for ch in slug)
    slug = "-".join(part for part in slug.split('-') if part)
    return slug or "entry"


def _clip_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    limit = max(1, int(limit))
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


__all__ = ["UserEntryStore", "UserEntryRecord"]
