"""Local, shared, attributed engineering lessons; no project scans or query log.

Content is advisory data. A verified source fingerprint establishes provenance,
not correctness, authenticated identity, product acceptance or general benefit.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import unicodedata

from .files import read_evidence
from .review import check_review

PHASES = ("planning", "implementation", "review", "diagnosis")
MAX_QUERY = 2000
MAX_RECORD_BYTES = 32_000
MAX_OUTPUT_BYTES = 64_000
MAX_DB_BYTES = 128 * 1024 * 1024
TEXT_LIMITS = {"title": 160, "context": 800, "problem": 800, "action": 1200, "check": 800}
LIST_LIMITS = {"topics": 8, "terms": 12, "phases": 4, "technologies": 8}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value, maximum, label):
    _require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum
             and not any(ord(char) < 32 and char not in "\n\t\r" or ord(char) == 127 for char in value),
             f"{label} requires nonempty text of at most {maximum} characters.")
    result = unicodedata.normalize("NFKC", " ".join(value.split()))
    _require(len(result) <= maximum, f"{label} exceeds its normalized length limit.")
    return result



def _generalized(value):
    """Reject common leakage, without claiming complete automatic sanitization."""
    patterns = (
        r"(?i)(?:/(?:users|home|private/var|var/folders|tmp)/|file://|[a-z]:[\\/]|~[\\/])",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{16,}|AKIA[A-Z0-9]{16})\b",
        r"(?i)\b(?:api[_-]?key|password|secret|access[_-]?token|authorization)\s*[:=]\s*[^\s]{4,}",
        r"(?i)\bbearer\s+[A-Za-z0-9._-]{12,}",
    )
    _require(not any(re.search(pattern, value) for pattern in patterns),
             "Generalize lesson text: obvious credentials or identifying local paths are not shareable.")
    return value

def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _identifier(value):
    _require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", value),
             "Lesson identity must be a bounded identifier, not a path.")
    return _generalized(value)


def _revision(value, *, required=False):
    _require(value is None and not required or type(value) is int and value >= 1,
             "Expected revision must be a positive integer.")


def _lesson(value):
    _require(isinstance(value, dict) and set(TEXT_LIMITS) <= set(value)
             and set(value) <= set(TEXT_LIMITS) | set(LIST_LIMITS) | {"notApplicable"},
             "Lesson requires title, context, problem, action and check; unsupported fields are rejected.")
    result = {key: _generalized(_text(value[key], maximum, key)) for key, maximum in TEXT_LIMITS.items()}
    for key, maximum in LIST_LIMITS.items():
        items = value.get(key, [])
        _require(isinstance(items, (list, tuple)) and len(items) <= maximum, f"{key} permits at most {maximum} entries.")
        normalized = [_generalized(_text(item, 80, key)).casefold() for item in items]
        _require(len(set(normalized)) == len(normalized), f"{key} entries must be distinct.")
        if key == "phases":
            _require(all(item in PHASES for item in normalized), "Unknown lesson phase.")
        result[key] = sorted(normalized)
    if "notApplicable" in value:
        result["notApplicable"] = _generalized(_text(value["notApplicable"], 600, "notApplicable"))
    _require(len(_json(result).encode()) <= MAX_RECORD_BYTES, "Lesson exceeds its byte limit.")
    return result


def default_registry():
    """Resolve the user's shared store without creating it."""
    return Path(os.environ.get("AIM_LEARNING_REGISTRY", "~/.aim/learning/registry.sqlite3")).expanduser()


def _path(value):
    raw = os.fspath(value)
    _require(isinstance(raw, str) and raw and not any(ord(c) < 32 for c in raw), "Invalid registry path.")
    path = Path(raw).expanduser().absolute()
    _require(".." not in path.parts, "Registry path must not contain traversal.")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.is_symlink():
            raise ValueError("Registry path must not traverse symbolic links.")
        if current.exists():
            _require(current.is_file() if current == path else current.is_dir(), "Unsafe registry path.")
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(path) + suffix)
        _require(not sidecar.is_symlink() and (not sidecar.exists() or sidecar.is_file()), "Unsafe SQLite sidecar.")
    if path.exists():
        _require(path.stat().st_size <= MAX_DB_BYTES, "Registry exceeds its size limit.")
    return path


def _schema(connection, *, create):
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == 0 and create:
        _require(not connection.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1").fetchone(),
                 "Refusing to initialize an unrelated database.")
        connection.execute("CREATE TABLE lessons (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, state TEXT NOT NULL, record TEXT NOT NULL)")
        connection.execute("CREATE TABLE revisions (id TEXT NOT NULL, revision INTEGER NOT NULL, record TEXT NOT NULL, PRIMARY KEY(id, revision))")
        connection.execute("CREATE TABLE topics (lesson_id TEXT NOT NULL, topic TEXT NOT NULL, PRIMARY KEY(lesson_id, topic))")
        connection.execute("CREATE INDEX topic_lookup ON topics(topic)")
        connection.execute("CREATE TABLE contexts (lesson_id TEXT NOT NULL, kind TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(lesson_id,kind,value))")
        connection.execute("CREATE INDEX context_lookup ON contexts(kind,value)")
        connection.execute("CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED, title, context, problem, action, checktext, terms, topics, technologies, tokenize='unicode61 remove_diacritics 2')")
        connection.execute("PRAGMA user_version=1")
    else:
        _require(version == 1, "Unsupported learning registry schema.")


@contextmanager
def _database(value, *, write=False):
    path = _path(value)
    if write:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        _path(path)  # Recheck newly created directories and sidecar paths.
    connection = sqlite3.connect(path.as_uri() + ("?mode=rwc" if write else "?mode=ro"),
                                 uri=True, timeout=3, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        if hasattr(connection, "setlimit"):
            connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 128_000)
        connection.execute("PRAGMA busy_timeout=3000")
        connection.execute("PRAGMA trusted_schema=OFF")
        if write:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            _require(version == 1 or version == 0 and not connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1").fetchone(),
                "Refusing to modify an unrelated or unsupported database.")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("BEGIN IMMEDIATE")
        else:
            connection.execute("PRAGMA query_only=ON")
            connection.execute("BEGIN")
        deadline = time.monotonic() + 3
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        _schema(connection, create=write)
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(path):
    """Create an empty registry only on this explicit call (or a valid share)."""
    with _database(path, write=True):
        pass
    return {"available": True, "schemaVersion": 1}


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result, "Duplicate JSON key in evidence or registry record.")
        result[key] = value
    return result


def _proof(repo, reference):
    _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
             "Evidence requires exactly path and sha256.")
    path, expected = reference["path"], reference["sha256"]
    _require(isinstance(path, str) and 0 < len(path) <= 1000 and not path.startswith("/")
             and "\\" not in path and ":" not in path and not any(ord(c) < 32 for c in path)
             and all(part not in ("", ".", "..") for part in path.split("/")), "Unsafe evidence path.")
    _require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "Evidence requires a lowercase SHA-256.")
    root = Path(repo).resolve()
    payload = read_evidence(root, path)
    _require(_sha(payload) == expected, "Evidence changed; do not refresh an old receipt.")
    try:
        record = json.loads(payload, object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError):
        record = None  # Ordinary raw test output remains an attributed observation.
    except RecursionError as exc:
        raise ValueError("Evidence JSON exceeds its nesting limit.") from exc
    verification = "fingerprinted-source"
    if isinstance(record, dict) and any(key in record for key in ("reviewMode", "reviewer", "implementers", "sources")):
        sources = record.get("sources")
        _require(isinstance(sources, list) and 1 <= len(sources) <= 256,
                 "Structured review requires one to 256 source bindings.")
        declared_paths = [source.get("path") if isinstance(source, dict) else None for source in sources]
        # Check the declared source set; this does not establish that every
        # changed file was declared or that reviewer identity is authenticated.
        assessment = check_review(root, record, record.get("changedPaths", declared_paths))
        _require(assessment["eligible"] and assessment["independentReviewDeclared"]
                 and assessment["provenance"]["status"] == "declared-separate",
                 "Structured review is stale, incomplete, conflicting or has unresolved findings.")
        verification = "declared-independent-review"
    return expected, _sha(str(root).encode()), verification


def _stored(raw):
    _require(isinstance(raw, str) and len(raw.encode()) <= MAX_RECORD_BYTES, "Invalid stored lesson size.")
    try:
        record = json.loads(raw, object_pairs_hook=_pairs)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid stored lesson JSON.") from exc
    _require(isinstance(record, dict), "Invalid stored lesson.")
    metadata = {"id", "revision", "state", "createdAt", "updatedAt", "evidenceSha256", "originSha256",
                "sourceVerification", "advisoryOnly", "benefitVerified", "withdrawalReason"}
    _lesson({key: value for key, value in record.items() if key not in metadata})
    _identifier(record.get("id"))
    _revision(record.get("revision"), required=True)
    _require(record.get("state") in ("active", "withdrawn")
             and record.get("sourceVerification") in ("fingerprinted-source", "declared-independent-review")
             and record.get("advisoryOnly") is True and record.get("benefitVerified") is False,
             "Invalid stored lesson metadata.")
    for name in ("evidenceSha256", "originSha256"):
        _require(isinstance(record.get(name), str) and re.fullmatch(r"[0-9a-f]{64}", record[name]),
                 "Invalid stored lesson fingerprint.")
    for name in ("createdAt", "updatedAt"):
        _require(isinstance(record.get(name), str) and len(record[name]) <= 40, "Invalid stored timestamp.")
        try:
            datetime.fromisoformat(record[name].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid stored timestamp.") from exc
    if "withdrawalReason" in record:
        _generalized(_text(record["withdrawalReason"], 800, "Withdrawal reason"))
    return record


def _persist(connection, record):
    encoded = _json(record)
    _require(len(encoded.encode()) <= MAX_RECORD_BYTES, "Lesson record exceeds its byte limit.")
    connection.execute("INSERT INTO lessons VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,state=excluded.state,record=excluded.record",
                       (record["id"], record["revision"], record["state"], encoded))
    connection.execute("INSERT INTO revisions VALUES(?,?,?)", (record["id"], record["revision"], encoded))
    connection.execute("DELETE FROM search WHERE id=?", (record["id"],))
    connection.execute("DELETE FROM topics WHERE lesson_id=?", (record["id"],))
    connection.execute("DELETE FROM contexts WHERE lesson_id=?", (record["id"],))
    if record["state"] == "active":
        connection.execute("INSERT INTO search VALUES(?,?,?,?,?,?,?,?,?)", (
            record["id"], record["title"], record["context"], record["problem"], record["action"], record["check"],
            " ".join(record["terms"]), " ".join(record["topics"]), " ".join(record["technologies"])))
        connection.executemany("INSERT INTO topics VALUES(?,?)", [(record["id"], topic) for topic in record["topics"]])
        connection.executemany("INSERT INTO contexts VALUES(?,?,?)",
                               [(record["id"], kind, value) for kind, key in (("technology", "technologies"), ("phase", "phases"))
                                for value in record[key]])


def share(path, repo, lesson, evidence_ref, *, lesson_id=None, expected_revision=None):
    """Publish an explicit generalized lesson, with evidence checked before writes."""
    normalized = _lesson(lesson)
    _revision(expected_revision)
    identifier = _identifier(lesson_id) if lesson_id is not None else "LRN-" + _sha(_json(
        {key: normalized[key].casefold() for key in ("problem", "action", "context")}).encode())[:24]
    evidence, origin, verification = _proof(repo, evidence_ref)
    with _database(path, write=True) as connection:
        row = connection.execute("SELECT substr(record,1,32001) FROM lessons WHERE id=?", (identifier,)).fetchone()
        previous = _stored(row[0]) if row else None
        if previous:
            same = (all(previous.get(key) == value for key, value in normalized.items())
                    and ("notApplicable" in previous) == ("notApplicable" in normalized)
                    and previous["state"] == "active" and previous["evidenceSha256"] == evidence
                    and previous["originSha256"] == origin and previous["sourceVerification"] == verification)
            if same:
                return {"changed": False, "record": previous}
            _require(expected_revision == previous["revision"], "Lesson changed or requires an explicit expected revision.")
            _require(previous["revision"] < 1000, "Lesson history reached its bounded revision limit.")
        else:
            _require(expected_revision is None, "Cannot update a missing lesson revision.")
            _require(connection.execute("SELECT count(*) FROM lessons").fetchone()[0] < 10000, "Registry lesson limit reached.")
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = {**normalized, "id": identifier, "revision": previous["revision"] + 1 if previous else 1,
                  "state": "active", "createdAt": previous["createdAt"] if previous else timestamp,
                  "updatedAt": timestamp, "evidenceSha256": evidence, "originSha256": origin,
                  "sourceVerification": verification, "advisoryOnly": True, "benefitVerified": False}
        _persist(connection, record)
    return {"changed": True, "record": record}


def withdraw(path, repo, lesson_id, expected_revision, reason, evidence_ref):
    identifier = _identifier(lesson_id)
    _revision(expected_revision, required=True)
    reason = _generalized(_text(reason, 800, "Withdrawal reason"))
    evidence, origin, verification = _proof(repo, evidence_ref)
    _require(_path(path).exists(), "Cannot withdraw from a missing registry.")
    with _database(path, write=True) as connection:
        row = connection.execute("SELECT substr(record,1,32001) FROM lessons WHERE id=?", (identifier,)).fetchone()
        _require(row is not None, "Unknown lesson.")
        previous = _stored(row[0])
        if (previous["state"] == "withdrawn" and previous.get("withdrawalReason") == reason
                and previous["evidenceSha256"] == evidence and previous["originSha256"] == origin
                and previous["sourceVerification"] == verification):
            return {"changed": False, "record": previous}
        _require(previous["revision"] == expected_revision, "Lesson changed; stale withdrawal revision.")
        _require(previous["revision"] < 1000, "Lesson history reached its bounded revision limit.")
        record = {**previous, "revision": previous["revision"] + 1, "state": "withdrawn",
                  "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                  "withdrawalReason": reason, "evidenceSha256": evidence, "originSha256": origin,
                  "sourceVerification": verification}
        _persist(connection, record)
    return {"changed": True, "record": record}


def _bounded(result, collection):
    while len(_json(result).encode()) > MAX_OUTPUT_BYTES and result[collection]:
        result[collection].pop()
        result["truncated"] = True
    return result


def recall(path, text="", phase="planning", technologies=()):
    _require(isinstance(text, str) and len(text) <= MAX_QUERY, "Recall text exceeds its input limit.")
    _require(phase in PHASES, "Unknown recall phase.")
    _require(isinstance(technologies, (list, tuple)) and len(technologies) <= 8, "Supply at most eight technologies.")
    tech = {_text(value, 80, "Technology").casefold() for value in technologies}
    result = {"available": False, "lessons": [], "topics": [], "advisoryOnly": True, "benefitVerified": False}
    if not _path(path).exists():
        return result
    stopwords = {"the", "and", "with", "from", "when", "then", "that", "this", "for", "are", "was", "not",
                 "och", "att", "det", "den", "med", "som", "för", "till", "inte", "ska", "kan", "ett", "har"}
    tokens = list(dict.fromkeys(token[:64] for token in re.findall(r"[^\W_]+", text.casefold())
                               if len(token) >= 3 and token not in stopwords))[:24]
    query = " OR ".join('"' + token + '"*' for token in tokens)
    with _database(path) as connection:
        result["available"] = True
        result["topics"] = [{"topic": row[0], "count": row[1]} for row in connection.execute(
            "SELECT substr(topic,1,81),count(*) FROM topics JOIN lessons ON lessons.id=topics.lesson_id WHERE state='active' GROUP BY topic ORDER BY count(*) DESC,topic LIMIT 5")]
        for topic in result["topics"]:
            _generalized(_text(topic["topic"], 80, "Stored topic"))
        lexical_rows = connection.execute(
            "SELECT substr(lessons.record,1,32001),bm25(search,0,5,1,3,2,1,4,2,2) AS score FROM search JOIN lessons ON lessons.id=search.id WHERE search MATCH ? AND lessons.state='active' ORDER BY score LIMIT 64", (query,)).fetchall() if query else []
        # Context has its own indexed candidate pool even when FTS has hits.
        # Otherwise one incidental word can hide every useful technology match.
        placeholders = ",".join("?" for _ in tech) or "NULL"
        context_rows = connection.execute(
            "SELECT substr(lessons.record,1,32001) FROM ("
            "SELECT lesson_id,sum(CASE WHEN kind='technology' THEN 5 ELSE 1 END) AS weight FROM contexts "
            f"WHERE (kind='technology' AND value IN ({placeholders})) OR (kind='phase' AND value=?) GROUP BY lesson_id"
            ") AS matches JOIN lessons ON lessons.id=matches.lesson_id WHERE state='active' "
            "ORDER BY matches.weight DESC,lessons.id LIMIT 64", (*sorted(tech), phase)).fetchall()
        pool = {}
        for row in lexical_rows:
            record = _stored(row[0])
            pool[record["id"]] = (record, float(row[1]))
        for row in context_rows:
            record = _stored(row[0])
            pool.setdefault(record["id"], (record, None))
        if not pool:
            for row in connection.execute("SELECT substr(record,1,32001) FROM lessons WHERE state='active' ORDER BY id LIMIT 64"):
                record = _stored(row[0])
                pool[record["id"]] = (record, None)
        candidates = []
        for record, lexical_score in pool.values():
            overlap = len(tech.intersection(record["technologies"]))
            phase_match = int(phase in record["phases"])
            indexed = " ".join([record[key] for key in TEXT_LIMITS] + record["terms"] + record["topics"] + record["technologies"]).casefold()
            words = re.findall(r"[^\W_]+", indexed)
            matched = sum(any(word.startswith(token) for word in words) for token in tokens)
            strong_text = lexical_score is not None and matched >= min(2, len(tokens)) and bool(tokens)
            match = "text" if strong_text else "context" if overlap else "discovery"
            why = ("Task text matched indexed lesson words or synonyms; check applicability." if match == "text"
                   else "Declared technology context overlaps; check applicability." if match == "context"
                   else "Discovery suggestion from the shared registry; task relevance is unverified.")
            # Keep strong lexical matches, explicit context and uncertain discovery
            # distinct; an arbitrarily strong score for one weak word cannot win.
            rank = ({"text": 0, "context": 1, "discovery": 2}[match], -overlap, -phase_match,
                    lexical_score if lexical_score is not None else 0, record["id"])
            candidates.append((rank, {**record, "matchKind": match, "why": why}))
        candidates.sort(key=lambda item: item[0])
        result["lessons"] = [item[1] for item in candidates[:3]]
        # Offer topics from the selected context/text results before global
        # popularity, so an incidental hit cannot conceal the useful topic too.
        preferred = list(dict.fromkeys(topic for record in result["lessons"] for topic in record["topics"]))[:5]
        if preferred:
            counts = dict(connection.execute(
                "SELECT topic,count(*) FROM topics JOIN lessons ON lessons.id=topics.lesson_id "
                f"WHERE state='active' AND topic IN ({','.join('?' for _ in preferred)}) GROUP BY topic", preferred))
            selected_topics = [{"topic": topic, "count": counts.get(topic, 0)} for topic in preferred]
            result["topics"] = (selected_topics + [topic for topic in result["topics"] if topic["topic"] not in preferred])[:5]
    return _bounded(result, "lessons")


def history(path, lesson_id):
    identifier = _identifier(lesson_id)
    result = {"available": False, "revisions": [], "truncated": False}
    if not _path(path).exists():
        return result
    with _database(path) as connection:
        result["available"] = True
        rows = connection.execute("SELECT substr(record,1,32001) FROM revisions WHERE id=? ORDER BY revision DESC LIMIT 21", (identifier,)).fetchall()
        result["truncated"] = len(rows) > 20
        result["revisions"] = [_stored(row[0]) for row in rows[:20]]
    return _bounded(result, "revisions")
