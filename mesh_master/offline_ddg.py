"""Offline storage utilities for DuckDuckGo search snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
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
class OfflineDDGRecord:
    """Resolved search entry with captured metadata."""

    query: str
    title: str
    summary: str
    context: str
    results: List[Dict[str, str]] = field(default_factory=list)
    source: Optional[str] = None
    fetched_at: Optional[str] = None
    language: Optional[str] = None
    matched_alias: Optional[str] = None


@dataclass
class _IndexEntry:
    key: str
    query: str
    title: str
    path: Path
    summary: Optional[str] = None
    source: Optional[str] = None
    fetched_at: Optional[str] = None
    aliases: Tuple[str, ...] = field(default_factory=tuple)
    language: Optional[str] = None


class OfflineDDGStore:
    """Manages on-disk DDG query archives under a simple index manifest."""

    def __init__(self, index_file: Path, *, base_dir: Optional[Path] = None) -> None:
        self.index_file = Path(index_file)
        self.base_dir = Path(base_dir) if base_dir else self.index_file.parent
        self._entries: Dict[str, _IndexEntry] = {}
        self._alias_map: Dict[str, str] = {}
        self._loaded = False
        self._load_error: Optional[str] = None
        self._lock = threading.RLock()
        self._load_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_ready(self) -> bool:
        return self._loaded and not self._load_error and bool(self._entries)

    def error_message(self) -> Optional[str]:
        return self._load_error

    def list_entries(self) -> List[Dict[str, object]]:
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
                        mdt = datetime.utcfromtimestamp(mtime).replace(tzinfo=timezone.utc)
                        mtime_iso = mdt.isoformat()
                        age_days = int(max(0, (datetime.now(tz=timezone.utc) - mdt).days))
                    except Exception:
                        mtime_iso, age_days = None, None
                entries.append(
                    {
                        "key": key,
                        "query": entry.query,
                        "title": entry.title,
                        "summary": entry.summary or "",
                        "source": entry.source or "",
                        "fetched_at": entry.fetched_at or "",
                        "language": entry.language or "",
                        "aliases": list(entry.aliases) if entry.aliases else [],
                        "path": rel_path.as_posix(),
                        "size_bytes": size,
                        "mtime_iso": mtime_iso,
                        "age_days": age_days,
                    }
                )
        return entries

    def lookup(self, identifier: str) -> Tuple[Optional[OfflineDDGRecord], List[str]]:
        normalized = _normalize(identifier)
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
            record = self._load_record(entry)
            if not record:
                suggestions = self._suggest(normalized)
                return None, suggestions
            record.matched_alias = matched_alias
            return record, []

    def delete(self, identifier: str) -> bool:
        normalized = _normalize(identifier)
        if not normalized:
            return False
        with self._lock:
            if not self._loaded:
                self._load_index()
            key = self._resolve_key(normalized) or normalized
            entry = self._entries.get(key)
            if not entry:
                return False
            try:
                entry.path.unlink(missing_ok=True)
            except Exception:
                pass
            self._entries.pop(key, None)
            self._alias_map = {a: tgt for a, tgt in self._alias_map.items() if tgt != key}
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

            def sort_key(kv: Tuple[str, _IndexEntry]):
                entry = kv[1]
                try:
                    mtime = entry.path.stat().st_mtime
                except Exception:
                    mtime = 0
                return (mtime, entry.path.as_posix())

            items.sort(key=sort_key)
            to_remove = before - max_entries
            removed = 0
            for key, entry in items[:to_remove]:
                try:
                    entry.path.unlink(missing_ok=True)
                except Exception:
                    pass
                self._entries.pop(key, None)
                removed += 1
            self._alias_map = {a: tgt for a, tgt in self._alias_map.items() if tgt in self._entries}
            self._write_index()
            after = len(self._entries)
            return {"before": before, "removed": removed, "after": after}

    def store_search(
        self,
        *,
        query: str,
        summary: str,
        context: str,
        results: Optional[List[Dict[str, str]]] = None,
        source: Optional[str] = None,
        fetched_at: Optional[datetime] = None,
        aliases: Optional[Iterable[str]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        normalized_query = _normalize(query)
        if not normalized_query:
            return {}
        timestamp = fetched_at or datetime.now(tz=timezone.utc)
        fetched_iso = _isoformat(timestamp)
        slug_source = f"{query} {fetched_iso}"
        slug = _slugify(slug_source)
        rel_path = Path(f"{slug}.json")
        target = self.base_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "query": query,
            "title": query,
            "summary": summary,
            "context": context,
            "results": results or [],
            "source": source,
            "fetched_at": fetched_iso,
            "language": language,
        }
        with self._lock:
            with target.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")
            alias_list = [alias for alias in (aliases or []) if alias]
            normalized_aliases = tuple({alias for alias in (_normalize(a) for a in alias_list) if alias})
            key = _normalize(f"{query} {fetched_iso}")
            entry = _IndexEntry(
                key=key,
                query=query,
                title=query,
                path=target,
                summary=summary,
                source=source,
                fetched_at=fetched_iso,
                aliases=normalized_aliases,
                language=language,
            )
            self._entries[key] = entry
            for alias in normalized_aliases:
                self._alias_map[alias] = key
            self._alias_map[normalized_query] = key
            self._write_index()
            self._load_error = None
            return {"key": key, "slug": rel_path.stem}

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
        if self._loaded:
            return
        try:
            if not self.index_file.is_file():
                self._entries.clear()
                self._alias_map.clear()
                self._loaded = True
                self._load_error = None
                try:
                    self._write_index()
                except Exception:
                    pass
                return
            with self.index_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self._entries.clear()
            self._alias_map.clear()
            self._loaded = True
            self._load_error = None
            try:
                self._write_index()
            except Exception:
                pass
            return
        except Exception as exc:
            self._entries.clear()
            self._alias_map.clear()
            self._loaded = True
            self._load_error = f"Failed to load index: {exc}"
            return

        entries_raw = data.get("entries") if isinstance(data, dict) else []
        entries: Dict[str, _IndexEntry] = {}
        alias_map: Dict[str, str] = {}
        for entry in entries_raw or []:
            if not isinstance(entry, dict):
                continue
            key = _normalize(entry.get("key"))
            query = entry.get("query") or entry.get("title") or ""
            path_raw = entry.get("path") or ""
            summary = entry.get("summary") or ""
            source = entry.get("source") or None
            fetched_at = entry.get("fetched_at") or None
            aliases = entry.get("aliases") or []
            language = entry.get("language") or None
            if not key or not path_raw:
                continue
            path = self.base_dir / Path(path_raw)
            idx_entry = _IndexEntry(
                key=key,
                query=query,
                title=entry.get("title") or query,
                path=path,
                summary=summary,
                source=source,
                fetched_at=fetched_at,
                aliases=tuple(_normalize(alias) for alias in aliases if alias),
                language=language,
            )
            entries[key] = idx_entry
            alias_map[_normalize(query)] = key
            for alias in idx_entry.aliases:
                if alias:
                    alias_map[alias] = key
        self._entries = entries
        self._alias_map = alias_map
        self._loaded = True
        self._load_error = None if entries else "Index has no entries"

    def _write_index(self) -> None:
        entries = []
        for entry in sorted(self._entries.values(), key=lambda e: e.title.lower()):
            rel_path = entry.path
            try:
                rel_path = entry.path.relative_to(self.base_dir)
            except Exception:
                rel_path = entry.path
            entries.append(
                {
                    "key": entry.key,
                    "query": entry.query,
                    "title": entry.title,
                    "path": rel_path.as_posix(),
                    "summary": entry.summary,
                    "source": entry.source,
                    "fetched_at": entry.fetched_at,
                    "language": entry.language,
                    "aliases": [alias for alias in entry.aliases if alias],
                }
            )
        payload = {"entries": entries}
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with self.index_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")

    def _load_record(self, entry: _IndexEntry) -> Optional[OfflineDDGRecord]:
        try:
            with entry.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None
        query = data.get("query") or entry.query
        title = data.get("title") or query
        summary = data.get("summary") or entry.summary or ""
        context = data.get("context") or ""
        results = data.get("results") or []
        source = data.get("source") or entry.source
        fetched_at = data.get("fetched_at") or entry.fetched_at
        language = data.get("language") or entry.language
        return OfflineDDGRecord(
            query=query,
            title=title,
            summary=summary,
            context=context,
            results=list(results) if isinstance(results, list) else [],
            source=source,
            fetched_at=fetched_at,
            language=language,
        )

    def _suggest(self, normalized: str) -> List[str]:
        if not self._entries:
            return []
        keys = list(self._entries.keys())
        import difflib

        close_matches = difflib.get_close_matches(normalized, keys, n=5, cutoff=0.6)
        titles = [self._entries[k].title for k in close_matches]
        if titles:
            return titles
        prefix_matches = [entry.title for entry in self._entries.values() if entry.key.startswith(normalized[:4])][:5]
        return prefix_matches


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
    return slug or "search"


def _isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


__all__ = ["OfflineDDGStore", "OfflineDDGRecord"]
