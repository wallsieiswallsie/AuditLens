"""Exact business-reference grouping over frozen snapshot records only."""
from hashlib import sha256
import json

from audit_engine.models.contracts import Evidence, Finding, Severity


class DuplicateTransactionReferenceDetector:
    def metadata(self):
        from audit_engine.detectors import ConfigField, DetectorMetadata, DetectorRequirements
        return DetectorMetadata(
            'business.duplicate_transaction_reference', '1.0.0',
            'Duplicate transaction reference',
            'Identify repeated business references in a configured table.',
            'transaction_integrity',
            DetectorRequirements('1', {'transactions': ('id', 'reference_number')}),
            {'table': ConfigField('string', 'transactions', 'Snapshot table to evaluate.'),
             'id_field': ConfigField('string', 'id', 'Unique non-empty string record identity field.'),
             'reference_field': ConfigField('string', 'reference_number', 'Business reference field.'),
             'ignore_empty': ConfigField('boolean', True, 'Exclude null and empty string only.'),
             'case_sensitive': ConfigField('boolean', True, 'Compare string case exactly; otherwise use casefold.')})

    def requirements_for(self, config):
        from audit_engine.detectors import DetectorRequirements
        values = config.values
        return DetectorRequirements('1', {values['table']: tuple(sorted({
            values['id_field'], values['reference_field']}))})

    def analyze(self, context, config):
        from audit_engine.detectors import result_for
        from audit_engine.execution import canonical_json
        values = config.values
        table, id_field, field = (values[key] for key in ('table', 'id_field', 'reference_field'))
        groups, identities = {}, set()
        for row in context.tables[table]:
            record_id, original = row[id_field], row[field]
            if not isinstance(record_id, str) or not record_id or record_id in identities:
                raise ValueError('Record identities must be unique non-empty strings')
            identities.add(record_id)
            if original is not None and type(original) not in (str, int, bool):
                raise ValueError('Reference must be a normalized scalar')
            if values['ignore_empty'] and (original is None or original == ''):
                continue
            compared = original.casefold() if isinstance(original, str) and not values['case_sensitive'] else original
            # Canonical JSON distinguishes null, strings, integers and booleans.
            key = canonical_json(compared)
            groups.setdefault(key, []).append((record_id, original))

        findings = []
        metadata = self.metadata()
        for key, records in sorted(groups.items()):
            if len(records) < 2:
                continue
            group = {'table': table, 'reference_field': field, 'comparison_value': json.loads(key)}
            entity_id = sha256(canonical_json(group).encode('utf-8')).hexdigest()
            evidence = tuple(Evidence('', table, {id_field: record_id}, field, original,
                {'comparison_value': group['comparison_value'], 'group_size': len(records)})
                for record_id, original in sorted(records))
            findings.append(Finding('', metadata.detector_id, 'DUPLICATE_TRANSACTION_REFERENCE',
                'Duplicate transaction reference',
                f'{len(records)} records in {table} share {field} comparison value {key}.',
                Severity.MEDIUM, 1.0, 'transaction_reference', entity_id, evidence,
                context.snapshot.snapshot_id, ''))
        findings.sort(key=lambda finding: finding.entity_id)
        return result_for(metadata, context, config, 'Duplicate transaction reference evaluation completed', tuple(findings))
