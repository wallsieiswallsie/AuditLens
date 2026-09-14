"""Explicit Detector SDK. Trusted modules receive only frozen data and config."""
from dataclasses import dataclass
from typing import Mapping, Protocol
from audit_engine.models.contracts import Contract, AuditContext, AuditResult, ResultStatus
from audit_engine.policy import identifier, version


@dataclass(frozen=True)
class ConfigField(Contract):
    type: str
    default: object
    description: str

    def validate(self, value):
        # Deliberately small schema; extend only when an actual detector needs it.
        if self.type == 'optional_integer':
            if value is not None and type(value) is not int:
                raise ValueError('Invalid detector configuration type')
            return
        if self.type == 'list[string]':
            # Policy/default construction freezes JSON arrays to tuples.
            if type(value) not in (list, tuple) or any(type(item) is not str for item in value):
                raise ValueError('Invalid detector configuration type')
            return
        kinds = {'boolean': bool, 'integer': int, 'string': str}
        if self.type not in kinds or type(value) is not kinds[self.type]:
            raise ValueError('Invalid detector configuration type')


@dataclass(frozen=True)
class DetectorConfig(Contract):
    values: Mapping[str, object]


@dataclass(frozen=True)
class DetectorRequirements(Contract):
    schema_version: str
    required_tables: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class DetectorMetadata(Contract):
    detector_id: str
    detector_version: str
    name: str
    description: str
    category: str
    requirements: DetectorRequirements
    configuration: Mapping[str, ConfigField]

    def __post_init__(self):
        super().__post_init__()
        identifier(self.detector_id)
        version(self.detector_version)
        version(self.requirements.schema_version)
        for value in (self.name, self.description, self.category):
            if not isinstance(value, str) or not value:
                raise ValueError('Incomplete detector metadata')
        for table, columns in self.requirements.required_tables.items():
            identifier(table)
            if not isinstance(columns, tuple) or len(set(columns)) != len(columns):
                raise ValueError('Invalid required fields')
            for column in columns:
                identifier(column)
        for key, field in self.configuration.items():
            identifier(key)
            field.validate(field.default)
        self.to_json()


class AuditDetector(Protocol):
    def metadata(self) -> DetectorMetadata: ...
    def analyze(self, context: AuditContext, config: DetectorConfig) -> AuditResult: ...


class ConfiguredRequirementsDetector(AuditDetector, Protocol):
    def requirements_for(self, config: DetectorConfig) -> DetectorRequirements: ...


class DetectorRegistry:
    def __init__(self, detectors=()):
        self._entries = {}
        for detector in detectors:
            self.register(detector)

    def register(self, detector: AuditDetector):
        metadata = DetectorMetadata.from_json(detector.metadata().to_json())
        if not callable(getattr(detector, 'analyze', None)):
            raise ValueError('Invalid detector interface')
        if metadata.detector_id in self._entries:
            raise ValueError('Duplicate detector ID')
        self._entries[metadata.detector_id] = (detector, metadata)

    def get(self, detector_id, expected_version=None):
        if detector_id not in self._entries:
            raise ValueError('Unknown detector')
        detector, metadata = self._entries[detector_id]
        if detector.metadata() != metadata or (expected_version is not None and expected_version != metadata.detector_version):
            raise ValueError('Detector metadata/version mismatch')
        return detector

    def list(self):
        return tuple(self._entries[key][1] for key in sorted(self._entries))


def resolve_config(metadata, supplied):
    if not isinstance(supplied, Mapping) or set(supplied) - set(metadata.configuration):
        raise ValueError('Unknown detector configuration key')
    values = {}
    for key, field in sorted(metadata.configuration.items()):
        values[key] = supplied.get(key, field.default)
        field.validate(values[key])
    return DetectorConfig(values)


def validate_policy(policy, registry):
    for key in sorted(set(policy.enabled_detectors) | set(policy.disabled_detectors) | set(policy.detector_configuration)):
        detector = registry.get(key)
        config = resolve_config(detector.metadata(), policy.detector_configuration.get(key, {}))
        resolve_requirements(detector, config)
    return tuple((registry.get(key), resolve_config(registry.get(key).metadata(),
                  policy.detector_configuration.get(key, {})))
                 for key in policy.enabled_detectors if key not in policy.disabled_detectors)


def resolve_requirements(detector, config):
    """Optional trusted SDK hook; existing detectors retain static metadata requirements."""
    resolver = getattr(detector, 'requirements_for', None)
    requirements = resolver(config) if resolver is not None else detector.metadata().requirements
    # Reuse metadata validation for the resolved table/field declarations.
    from dataclasses import replace
    return replace(detector.metadata(), requirements=requirements).requirements


def compatibility(context, requirements):
    if context.snapshot.schema_version != requirements.schema_version:
        return 'unsupported_schema_version'
    # The loader validates rows against this versioned inventory, including empty tables.
    from audit_engine.snapshots import SCHEMA
    from audit_engine.versioning import SCHEMA_VERSION
    for table, columns in sorted(requirements.required_tables.items()):
        if table not in context.tables or table not in context.snapshot.manifest:
            return 'missing_table'
        if context.snapshot.schema_version != SCHEMA_VERSION or not set(columns) <= set(SCHEMA.get(table, ())):
            return 'missing_field'
        if any(not set(columns) <= set(row) for row in context.tables[table]):
            return 'missing_field'
    return None


def result_for(metadata, context, config, summary, findings=()):
    """Execution assigns run IDs and timestamps after validating detector output."""
    return AuditResult('', '', metadata.detector_id, metadata.detector_version,
        context.policy_version, ResultStatus.FINDINGS if findings else ResultStatus.PASSED,
        summary, len(findings), '', '', context.snapshot.snapshot_id,
        context.snapshot.snapshot_hash, findings, config.values)


class FrameworkHealthDetector:
    def metadata(self):
        from audit_engine.versioning import HEALTH_VERSION
        return DetectorMetadata('framework.health', HEALTH_VERSION, 'Framework health',
            'Verify snapshot readability; no business rules.', 'framework',
            DetectorRequirements('1', {}), {})

    def analyze(self, context, config):
        # Compatibility hook preserves the original execute/check API.
        from audit_engine.execution import check
        return result_for(self.metadata(), context, config, check(context))


class SnapshotIntegrityDetector:
    def metadata(self):
        return DetectorMetadata('framework.snapshot_integrity', '1.0.0', 'Snapshot inventory',
            'Demonstrate inventory evidence; no business risk conclusion.', 'framework',
            DetectorRequirements('1', {'roles': ('id',)}),
            {'emit_inventory': ConfigField('boolean', False, 'Emit informational inventory evidence.')})

    def analyze(self, context, config):
        from audit_engine.models.contracts import Finding, Evidence, Severity
        findings = ()
        if config.values['emit_inventory']:
            evidence = tuple(Evidence(table, table, {}, None, entry.rows, {'measurement': 'row_count'})
                for table, entry in sorted(context.snapshot.manifest.items()))
            findings = (Finding('inventory', self.metadata().detector_id, 'framework.inventory',
                'Snapshot inventory', 'Informational framework inventory; no business conclusion.',
                Severity.INFO, 1.0, 'snapshot', context.snapshot.snapshot_hash, evidence,
                context.snapshot.snapshot_id, ''),)
        return result_for(self.metadata(), context, config, 'Snapshot inventory verified; no business audit checks executed', findings)


from audit_engine.rules.duplicate_transaction_reference import DuplicateTransactionReferenceDetector
from audit_engine.rules.missing_required_field import MissingRequiredFieldDetector
from audit_engine.rules.sequence_gap import SequenceGapDetector
from audit_engine.rules.duplicate_payment import DuplicatePaymentDetector

DEFAULT_DETECTORS = DetectorRegistry((FrameworkHealthDetector(), SnapshotIntegrityDetector(),
                                     DuplicateTransactionReferenceDetector(), MissingRequiredFieldDetector(),
                                     SequenceGapDetector(), DuplicatePaymentDetector()))
