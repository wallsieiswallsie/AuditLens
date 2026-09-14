"""Frozen, JSON-round-trippable contracts. No database dependencies."""
from dataclasses import dataclass, fields
from enum import Enum
from types import MappingProxyType
from typing import Mapping, get_type_hints, get_origin, get_args
import collections.abc
import json


def freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


def plain(value):
    if isinstance(value, Contract):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def decode(kind, value):
    origin, args = get_origin(kind), get_args(kind)
    if kind is object:
        return freeze(value)
    if origin is tuple:
        if not isinstance(value, list):
            raise ValueError("Expected array")
        return tuple(decode(args[0], v) for v in value)
    if origin is collections.abc.Mapping:
        if not isinstance(value, dict):
            raise ValueError("Expected object")
        return freeze({decode(args[0], k): decode(args[1], v) for k, v in value.items()})
    if origin is not None and type(None) in args:
        return None if value is None else decode(args[0], value)
    if isinstance(kind, type) and issubclass(kind, (Contract, Enum)):
        return kind.from_dict(value) if issubclass(kind, Contract) else kind(value)
    if type(value) is not kind:
        raise ValueError("Invalid contract field type")
    return value


class Contract:
    def __post_init__(self):
        for f in fields(self):
            object.__setattr__(self, f.name, freeze(getattr(self, f.name)))

    def to_dict(self):
        return plain(self)

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_dict(cls, value):
        hints = get_type_hints(cls)
        if not isinstance(value, dict) or set(value) != set(hints):
            raise ValueError("Invalid contract fields")
        return cls(**{k: decode(t, value[k]) for k, t in hints.items()})

    @classmethod
    def from_json(cls, value):
        return cls.from_dict(json.loads(value))


class RunStatus(str, Enum):
    CREATED = "created"
    EXTRACTING = "extracting"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultStatus(str, Enum):
    PASSED = "passed"
    FINDINGS = "findings"
    ERROR = "error"
    SKIPPED = "skipped"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SourceExtraction(Contract):
    source_type: str
    schema_version: str
    tables: Mapping[str, tuple[Mapping[str, object], ...]]


@dataclass(frozen=True)
class TableManifest(Contract):
    rows: int
    sha256: str


@dataclass(frozen=True)
class Snapshot(Contract):
    snapshot_id: str
    created_at: str
    source_type: str
    schema_version: str
    manifest: Mapping[str, TableManifest]
    snapshot_hash: str

    @property
    def record_counts(self):
        return MappingProxyType({k: v.rows for k, v in self.manifest.items()})

    @property
    def table_hashes(self):
        return MappingProxyType({k: v.sha256 for k, v in self.manifest.items()})


@dataclass(frozen=True)
class AuditRun(Contract):
    audit_run_id: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    status: RunStatus
    framework_version: str
    snapshot_id: str
    snapshot_hash: str
    policy_version: str
    execution_mode: str
    detector_versions: Mapping[str, str]
    detector_configuration: Mapping[str, object]


@dataclass(frozen=True)
class Provenance(Contract):
    audit_run_id: str
    snapshot_id: str
    snapshot_hash: str
    framework_version: str
    policy_version: str
    created_at: str
    operator: str
    execution_environment: str


@dataclass(frozen=True)
class Evidence(Contract):
    evidence_id: str
    source_table: str
    source_record_id: Mapping[str, str]
    field: str | None
    observed_value: object
    context: Mapping[str, object]


@dataclass(frozen=True)
class Finding(Contract):
    finding_id: str
    detector_id: str
    rule_id: str
    title: str
    description: str
    severity: Severity
    confidence: float
    entity_type: str
    entity_id: str
    evidence: tuple[Evidence, ...]
    snapshot_id: str
    audit_run_id: str


@dataclass(frozen=True)
class AuditResult(Contract):
    result_id: str
    audit_run_id: str
    detector_id: str
    detector_version: str
    policy_version: str
    status: ResultStatus
    summary: str
    finding_count: int
    started_at: str
    completed_at: str
    snapshot_id: str
    snapshot_hash: str
    findings: tuple[Finding, ...]
    detector_configuration: Mapping[str, object]


@dataclass(frozen=True)
class AuditContext(Contract):
    snapshot: Snapshot
    tables: Mapping[str, tuple[Mapping[str, object], ...]]
    policy_version: str
    framework_version: str
    detector_configuration: Mapping[str, object]
