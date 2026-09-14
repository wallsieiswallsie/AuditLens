"""Versioned, canonical policy. No environment-derived defaults."""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import json
import re
from audit_engine.models.contracts import Contract, Severity
from audit_engine.versioning import POLICY_VERSION


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_.-]{0,99}', value):
        raise ValueError('Invalid identifier')


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', value):
        raise ValueError('Invalid version')


@dataclass(frozen=True)
class AuditPolicy(Contract):
    policy_id: str
    policy_version: str
    name: str
    description: str
    enabled_detectors: tuple[str, ...]
    disabled_detectors: tuple[str, ...]
    minimum_severity: Severity
    minimum_confidence: float
    fail_on_detector_error: bool
    allow_partial_results: bool
    detector_configuration: Mapping[str, Mapping[str, object]]
    contract_version: str = '1'

    def __post_init__(self):
        super().__post_init__()
        # Apply the same field typing to Python construction and JSON reads.
        from audit_engine.models.contracts import decode
        from typing import get_type_hints
        for key, kind in get_type_hints(type(self)).items():
            object.__setattr__(self, key, decode(kind, self.to_dict()[key]))
        identifier(self.policy_id)
        version(self.policy_version)
        if self.contract_version != '1' or not self.name or not self.description:
            raise ValueError('Unsupported or incomplete policy')
        if not 0 <= self.minimum_confidence <= 1:
            raise ValueError('Confidence outside range')
        for values in (self.enabled_detectors, self.disabled_detectors):
            if len(set(values)) != len(values):
                raise ValueError('Duplicate detector selection')
            for value in values:
                identifier(value)
        for value in self.detector_configuration:
            identifier(value)
        object.__setattr__(self, 'enabled_detectors', tuple(sorted(self.enabled_detectors)))
        object.__setattr__(self, 'disabled_detectors', tuple(sorted(self.disabled_detectors)))
        self.to_json()


DEFAULT_POLICY = AuditPolicy('framework.default', POLICY_VERSION, 'Framework health',
    'Framework checks only; business audit logic is not included.',
    ('framework.health',), (), Severity.INFO, 0.0, True, False, {})


def load_policy(path=None):
    if path is None:
        return DEFAULT_POLICY
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return AuditPolicy.from_dict(json.loads(Path(path).read_text(encoding='utf-8'),
        object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON'))))
