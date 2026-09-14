"""Exact composite payment matching over frozen snapshot values."""
from hashlib import sha256
import json

from audit_engine.models.contracts import Evidence, Finding, Severity, plain


class DuplicatePaymentDetector:
    def metadata(self):
        from audit_engine.detectors import ConfigField, DetectorMetadata, DetectorRequirements
        return DetectorMetadata(
            'business.duplicate_payment', '1.0.0', 'Duplicate payment',
            'Identify repeated configured composite payment keys.', 'payment_integrity',
            DetectorRequirements('1', {'payments': ('id', 'invoice_id', 'amount', 'currency', 'reference')}),
            {'table': ConfigField('string', 'payments', 'Snapshot table to evaluate.'),
             'id_field': ConfigField('string', 'id', 'Unique non-empty string record identity.'),
             'match_fields': ConfigField('list[string]', ('invoice_id', 'amount', 'currency', 'reference'),
                                        'At least two distinct fields, in comparison order.'),
             'ignore_if_any_match_field_empty': ConfigField('boolean', True, 'Exclude null and empty string only.'),
             'case_sensitive_strings': ConfigField('boolean', True, 'Exact strings; false uses casefold only.')})

    def requirements_for(self, config):
        from audit_engine.detectors import DetectorRequirements
        v = config.values
        fields = v['match_fields']
        if len(fields) < 2 or len(set(fields)) != len(fields):
            raise ValueError('Match fields must contain at least two distinct fields')
        return DetectorRequirements('1', {v['table']: tuple(sorted({v['id_field'], *fields}))})

    def analyze(self, context, config):
        from audit_engine.detectors import result_for
        from audit_engine.execution import canonical_json
        v = config.values
        table, id_field, fields = v['table'], v['id_field'], v['match_fields']
        groups, identities = {}, set()
        for row in context.tables[table]:
            record_id = row[id_field]
            if not isinstance(record_id, str) or not record_id or record_id in identities:
                raise ValueError('Record identities must be unique non-empty strings')
            identities.add(record_id)
            originals = [plain(row[field]) for field in fields]
            if v['ignore_if_any_match_field_empty'] and any(
                    value is None or (type(value) is str and value == '') for value in originals):
                continue
            # Casefold only field-level strings. Nested JSON stays exact. JSON encoding
            # preserves scalar types, array order and canonical object key order.
            compared = [value.casefold() if type(value) is str and not v['case_sensitive_strings']
                        else value for value in originals]
            key = canonical_json(compared)
            groups.setdefault(key, []).append((record_id, originals))

        metadata = self.metadata()
        findings = []
        for key, records in groups.items():
            if len(records) < 2:
                continue
            identity = {'detector_id': metadata.detector_id, 'rule_id': 'DUPLICATE_PAYMENT',
                        'table': table, 'match_fields': list(fields), 'match_values': json.loads(key)}
            entity_id = sha256(canonical_json(identity).encode('utf-8')).hexdigest()
            evidence = tuple(Evidence('', table, {id_field: record_id}, None, None,
                {'match_fields': list(fields), 'match_values': dict(zip(fields, originals)),
                 'normalized_match_values': identity['match_values'], 'duplicate_count': len(records)})
                for record_id, originals in sorted(records, key=lambda r: canonical_json({id_field: r[0]})))
            findings.append(Finding('', metadata.detector_id, 'DUPLICATE_PAYMENT', 'Potential duplicate payment',
                f'Potential duplicate payment detected: {len(records)} records share the configured payment match key.',
                Severity.HIGH, 1.0, 'payment_match_group', entity_id, evidence, context.snapshot.snapshot_id, ''))
        findings.sort(key=lambda finding: finding.entity_id)
        return result_for(metadata, context, config, 'Duplicate payment evaluation completed', tuple(findings))
