"""Offline Wikipedia support utilities.

This module provides a tiny loader around an on-disk index so Mesh Master can
serve encyclopedia-style responses without touching the public internet.  The
index format is intentionally simple so the data set can be generated outside of
this project and copied onto the device.

Expected directory layout (configurable):

    offline_wiki/
      index.json
      apollo-11.json
      raspberry-pi.json
      ...

The ``index.json`` file contains an ``entries`` array.  Each entry includes:

    {
        "key": "apollo 11",           # canonical lowercase lookup key
        "title": "Apollo 11",         # display title
        "path": "apollo-11.json",     # content file relative to the index
        "aliases": ["apollo11"],      # optional alternate keys
        "summary": "..."               # optional default summary snippet
    }

The content files are UTF-8 JSON objects with at least a ``content`` field.  An
optional ``summary`` override and ``source`` string can also be provided.

Large deployments can shard the content into multiple subdirectories so long as
``path`` points to the correct relative location.  Everything is read lazily, so
only the metadata lives in memory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import difflib
import json
import threading

try:
    from unidecode import unidecode
except Exception:  # pragma: no cover - unidecode is part of the runtime deps
    def unidecode(value: str) -> str:
        return value


@dataclass
class OfflineWikiArticle:
    """Resolved offline article with the heavyweight context."""

    title: str
    summary: str
    content: str
    source: Optional[str] = None
    matched_alias: Optional[str] = None


@dataclass
class _IndexEntry:
    """Metadata stored in memory for quick lookups."""

    key: str
    title: str
    path: Path
    summary: Optional[str] = None
    aliases: Tuple[str, ...] = field(default_factory=tuple)


class OfflineWikiStore:
    """Loads the offline index and resolves topics on demand."""

    def __init__(self, index_file: Path, *, base_dir: Optional[Path] = None) -> None:
        self.index_file = Path(index_file)
        self.base_dir = Path(base_dir) if base_dir else self.index_file.parent
        self._entries: Dict[str, _IndexEntry] = {}
        self._alias_map: Dict[str, str] = {}
        self._loaded = False
        self._load_error: Optional[str] = None
        self._index_mtime: Optional[float] = None
        self._lock = threading.RLock()
        # Eagerly load metadata so we can report readiness immediately
        self._load_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_ready(self) -> bool:
        return self._loaded and not self._load_error and bool(self._entries)

    def error_message(self) -> Optional[str]:
        return self._load_error

    def available_topics(self) -> Iterable[str]:
        return (entry.title for entry in self._entries.values())

    def list_entries(self) -> List[Dict[str, object]]:
        """Return a snapshot of index entries with file stats for UI.

        Each item includes: key, title, aliases, path (relative), size_bytes, mtime_iso.
        """
        entries: List[Dict[str, object]] = []
        with self._lock:
            if not self._loaded:
                self._load_index()
            for key, entry in sorted(self._entries.items(), key=lambda kv: kv[1].title.lower()):
                try:
                    st = entry.path.stat()
                    size = int(getattr(st, "st_size", 0))
                    mtime = getattr(st, "st_mtime", None)
                except Exception:
                    size = 0
                    mtime = None
                rel_path = entry.path
                try:
                    rel_path = entry.path.relative_to(self.base_dir)
                except Exception:
                    rel_path = entry.path
                mtime_iso = None
                age_days = None
                if isinstance(mtime, (int, float)) and mtime > 0:
                    try:
                        import datetime as _dt
                        mdt = _dt.datetime.utcfromtimestamp(mtime).replace(tzinfo=_dt.timezone.utc)
                        mtime_iso = mdt.isoformat()
                        age_days = int(max(0, (_dt.datetime.now(tz=_dt.timezone.utc) - mdt).days))
                    except Exception:
                        mtime_iso, age_days = None, None
                entries.append(
                    {
                        "key": key,
                        "title": entry.title,
                        "summary": entry.summary or "",
                        "aliases": list(entry.aliases) if entry.aliases else [],
                        "path": rel_path.as_posix(),
                        "size_bytes": size,
                        "mtime_iso": mtime_iso,
                        "age_days": age_days,
                    }
                )
        return entries

    def lookup(
        self,
        topic: str,
        *,
        summary_limit: int = 400,
        context_limit: int = 40000,
    ) -> Tuple[Optional[OfflineWikiArticle], List[str]]:
        """Return the best-matching article and a list of suggestions."""

        normalized = _normalize(topic)
        if not normalized:
            return None, []

        with self._lock:
            if not self._loaded:
                self._load_index()

            key = self._resolve_key(normalized)
            matched_alias = None
            if key is None:
                suggestions = self._suggest(normalized)
                return None, suggestions

            if key != normalized:
                matched_alias = normalized

            entry = self._entries.get(key)
            if not entry:
                suggestions = self._suggest(normalized)
                return None, suggestions

            article = self._load_article(entry)
            if not article:
                suggestions = self._suggest(normalized)
                return None, suggestions

            summary = article.summary or entry.summary or _fallback_summary(article.content, summary_limit)
            summary = _clip(summary, summary_limit)
            content = _clip(article.content, max(2000, context_limit))
            return OfflineWikiArticle(
                title=article.title or entry.title,
                summary=summary,
                content=content,
                source=article.source,
                matched_alias=matched_alias,
            ), []

    def delete(self, title_or_key: str) -> bool:
        """Delete an article from disk and remove from the index.

        Accepts either the canonical key or display title; aliases are also
        resolved. Returns True if an entry was removed.
        """
        normalized = _normalize(title_or_key)
        if not normalized:
            return False
        with self._lock:
            if not self._loaded:
                self._load_index()
            key = self._resolve_key(normalized) or normalized
            entry = self._entries.get(key)
            if not entry:
                # Also try by matching display title
                for k, e in self._entries.items():
                    if _normalize(e.title) == normalized:
                        key, entry = k, e
                        break
            if not entry:
                return False
            try:
                entry.path.unlink(missing_ok=True)
            except Exception:
                # Continue even if file deletion fails; we can still drop the index entry
                pass
            # Remove entry and its aliases
            self._entries.pop(key, None)
            # Rebuild alias map excluding any alias pointing to the removed key
            self._alias_map = {a: tgt for a, tgt in self._alias_map.items() if tgt != key}
            self._write_index()
            self._load_error = None
            return True

    def prune_by_max(self, max_articles: int) -> Dict[str, int]:
        """Ensure the store has at most max_articles by deleting oldest.

        Returns a dict with {'before': N, 'removed': R, 'after': M}.
        """
        max_articles = max(0, int(max_articles))
        with self._lock:
            if not self._loaded:
                self._load_index()
            items = list(self._entries.items())
            before = len(items)
            if before <= max_articles:
                return {"before": before, "removed": 0, "after": before}
            # Sort by mtime (oldest first); fallback to path name for stability
            def sort_key(kv: Tuple[str, _IndexEntry]):
                entry = kv[1]
                try:
                    mtime = entry.path.stat().st_mtime
                except Exception:
                    mtime = 0
                return (mtime, entry.path.as_posix())

            items.sort(key=sort_key)
            to_remove = before - max_articles
            removed = 0
            for key, entry in items[:to_remove]:
                try:
                    entry.path.unlink(missing_ok=True)
                except Exception:
                    pass
                self._entries.pop(key, None)
                removed += 1
            # Rebuild alias map
            self._alias_map = {a: tgt for a, tgt in self._alias_map.items() if tgt in self._entries}
            self._write_index()
            after = len(self._entries)
            return {"before": before, "removed": removed, "after": after}

    def store_article(
        self,
        *,
        title: str,
        content: str,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        aliases: Optional[Iterable[str]] = None,
        summary_limit: int = 400,
        context_limit: int = 40000,
        overwrite: bool = False,
    ) -> bool:
        normalized = _normalize(title)
        if not normalized or not content:
            return False
        summary_clipped = _clip(summary or _fallback_summary(content, summary_limit), summary_limit)
        content_clipped = _clip(content, max(2000, context_limit))
        alias_list = [alias for alias in (aliases or []) if alias]
        normalized_aliases = [_normalize(alias) for alias in alias_list if alias]

        with self._lock:
            existing = self._entries.get(normalized)
            if existing and not overwrite:
                existing_aliases = set(existing.aliases)
                new_aliases = tuple(
                    alias
                    for alias in normalized_aliases
                    if alias and alias != normalized and alias not in existing_aliases
                )
                if not new_aliases:
                    return False
                updated_entry = _IndexEntry(
                    key=existing.key,
                    title=existing.title,
                    path=existing.path,
                    summary=existing.summary,
                    aliases=existing.aliases + new_aliases,
                )
                self._entries[normalized] = updated_entry
                for alias in new_aliases:
                    self._alias_map[alias] = normalized
                self._write_index()
                self._load_error = None
                return True
            slug = _slugify(title)
            rel_path = Path(f"{slug}.json")
            target = self.base_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "title": title,
                "summary": summary_clipped,
                "content": content_clipped,
            }
            if source:
                payload["source"] = source
            with target.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")

            entry = _IndexEntry(
                key=normalized,
                title=title,
                path=target,
                summary=summary_clipped,
                aliases=tuple(alias for alias in normalized_aliases if alias and alias != normalized),
            )
            self._entries[normalized] = entry
            for alias in entry.aliases:
                if alias:
                    self._alias_map[alias] = normalized
            self._write_index()
            self._load_error = None
            return True

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _resolve_key(self, normalized: str) -> Optional[str]:
        if normalized in self._entries:
            return normalized
        alias_target = self._alias_map.get(normalized)
        if alias_target:
            return alias_target
        return None

    def _load_index(self) -> None:
        """Load metadata from the index file, reloading if the file changed."""
        try:
            current_mtime = self.index_file.stat().st_mtime
        except FileNotFoundError:
            current_mtime = None

        if self._loaded:
            if current_mtime is None and self._index_mtime is None:
                return
            if (
                current_mtime is not None
                and self._index_mtime is not None
                and current_mtime <= self._index_mtime
            ):
                return

        try:
            if not self.index_file.is_file():
                self._load_error = f"Offline wiki index missing: {self.index_file}"
                self._entries.clear()
                self._alias_map.clear()
                self._index_mtime = None
                self._loaded = True
                return

            with self.index_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:  # pragma: no cover - file system failures
            self._load_error = f"Failed to load offline wiki index: {exc}"
            self._entries.clear()
            self._alias_map.clear()
            self._index_mtime = None
            self._loaded = True
            return

        entries = data.get("entries") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            self._load_error = "Offline wiki index is malformed (expected entries array)."
            self._entries.clear()
            self._alias_map.clear()
            self._index_mtime = current_mtime
            self._loaded = True
            return

        temp_entries: Dict[str, _IndexEntry] = {}
        temp_alias_map: Dict[str, str] = {}
        for raw in entries:
            if not isinstance(raw, dict):
                continue
            key = _normalize(raw.get("key") or raw.get("title"))
            title = str(raw.get("title") or raw.get("key") or "").strip()
            path_value = raw.get("path")
            if not key or not title or not isinstance(path_value, str):
                continue
            entry = _IndexEntry(
                key=key,
                title=title,
                path=self.base_dir / path_value,
                summary=str(raw.get("summary") or "").strip() or None,
                aliases=tuple(_normalize(alias) for alias in raw.get("aliases", []) if isinstance(alias, str)),
            )
            temp_entries[key] = entry
            for alias in entry.aliases:
                if alias and alias not in temp_alias_map:
                    temp_alias_map[alias] = key

        self._entries = temp_entries
        self._alias_map = temp_alias_map
        self._load_error = None
        self._index_mtime = current_mtime
        self._loaded = True

    def _load_article(self, entry: _IndexEntry) -> Optional[OfflineWikiArticle]:
        try:
            with entry.path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except FileNotFoundError:
            self._load_error = f"Offline wiki content missing: {entry.path}"
            return None
        except Exception as exc:  # pragma: no cover - JSON parsing errors
            self._load_error = f"Offline wiki content unreadable ({entry.path}): {exc}"
            return None

        if isinstance(payload, dict):
            title = str(payload.get("title") or entry.title)
            summary = str(payload.get("summary") or payload.get("abstract") or "").strip()
            content = str(payload.get("content") or payload.get("text") or "").strip()
            source = str(payload.get("source") or payload.get("url") or "").strip() or None
            if content:
                return OfflineWikiArticle(title=title, summary=summary, content=content, source=source)
        return None

    def _suggest(self, normalized: str) -> List[str]:
        if not self._entries:
            return []
        keys = list(self._entries.keys())
        close_matches = difflib.get_close_matches(normalized, keys, n=5, cutoff=0.6)
        titles = [self._entries[k].title for k in close_matches]
        if titles:
            return titles
        # Fall back to prefix matches for looser suggestions
        prefix_matches = [entry.title for entry in self._entries.values() if entry.key.startswith(normalized[:4])][:5]
        return prefix_matches

    def _write_index(self) -> None:
        entries = []
        for entry in sorted(self._entries.values(), key=lambda e: e.title.lower()):
            rel_path = entry.path.relative_to(self.base_dir)
            entries.append(
                {
                    "key": entry.key,
                    "title": entry.title,
                    "path": rel_path.as_posix(),
                    "summary": entry.summary,
                    "aliases": [alias for alias in entry.aliases if alias],
                }
            )
        payload = {"entries": entries}
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with self.index_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        try:
            self._index_mtime = self.index_file.stat().st_mtime
        except Exception:
            self._index_mtime = None


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
    return slug or "article"


def _clip(text: str, limit: int) -> str:
    limit = max(1, int(limit))
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _fallback_summary(content: str, limit: int) -> str:
    snippet = content.strip().split("\n", 1)[0]
    return _clip(snippet, limit)


__all__ = [
    "OfflineWikiArticle",
    "OfflineWikiStore",
]
