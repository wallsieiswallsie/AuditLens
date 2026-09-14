"""Record completeness over configured fields in a frozen snapshot."""
from audit_engine.models.contracts import Evidence, Finding, Severity


class MissingRequiredFieldDetector:
    def metadata(self):
        from audit_engine.detectors import ConfigField, DetectorMetadata, DetectorRequirements
        return DetectorMetadata(
            'business.missing_required_field', '1.0.0', 'Missing required field',
            'Identify records missing configured mandatory business values.', 'data_completeness',
            DetectorRequirements('1', {'transactions': ('id', 'reference')}),
            {'table': ConfigField('string', 'transactions', 'Snapshot table to evaluate.'),
             'id_field': ConfigField('string', 'id', 'Unique non-empty string record identity field.'),
             'required_fields': ConfigField('list[string]', ('reference',), 'Non-empty list of distinct required fields.'),
             'treat_empty_string_as_missing': ConfigField('boolean', True, 'Treat exactly empty strings as missing.')})

    def requirements_for(self, config):
        from audit_engine.detectors import DetectorRequirements
        values = config.values
        fields = values['required_fields']
        if not fields or len(set(fields)) != len(fields):
            raise ValueError('Required fields must be non-empty and distinct')
        return DetectorRequirements('1', {values['table']: tuple(sorted({values['id_field'], *fields}))})

    def analyze(self, context, config):
        from audit_engine.detectors import result_for
        values = config.values
        table, id_field = values['table'], values['id_field']
        fields = sorted(values['required_fields'])
        metadata = self.metadata()
        findings, identities = [], set()
        for row in context.tables[table]:
            record_id = row[id_field]
            if not isinstance(record_id, str) or not record_id or record_id in identities:
                raise ValueError('Record identities must be unique non-empty strings')
            identities.add(record_id)
            missing = [field for field in fields if row[field] is None or (
                values['treat_empty_string_as_missing'] and type(row[field]) is str and row[field] == '')]
            if not missing:
                continue
            # Store the record summary once; repeating the field list costs O(f squared).
            evidence = tuple(Evidence('', table, {id_field: record_id}, field, row[field],
                {'missing_classification': 'null' if row[field] is None else 'empty_string',
                 **({'missing_field_count': len(missing), 'missing_fields': missing} if index == 0 else {})})
                for index, field in enumerate(missing))
            findings.append(Finding('', metadata.detector_id, 'MISSING_REQUIRED_FIELD',
                'Missing required field', f'Record {record_id} is missing {len(missing)} required field(s).',
                Severity.MEDIUM, 1.0, table, record_id, evidence, context.snapshot.snapshot_id, ''))
        findings.sort(key=lambda finding: finding.entity_id)
        return result_for(metadata, context, config, 'Required field completeness evaluation completed', tuple(findings))
