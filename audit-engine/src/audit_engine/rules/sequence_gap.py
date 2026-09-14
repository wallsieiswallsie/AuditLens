"""Numeric continuity over frozen records; work scales with observations, not bounds."""
from bisect import bisect_left, bisect_right

from audit_engine.models.contracts import Evidence, Finding, Severity


class SequenceGapDetector:
    def metadata(self):
        from audit_engine.detectors import ConfigField, DetectorMetadata, DetectorRequirements
        return DetectorMetadata(
            'business.sequence_gap', '1.0.0', 'Sequence gap',
            'Identify contiguous missing numeric sequence ranges.', 'sequence_integrity',
            DetectorRequirements('1', {'transactions': ('id', 'sequence_number')}),
            {'table': ConfigField('string', 'transactions', 'Snapshot table to evaluate.'),
             'id_field': ConfigField('string', 'id', 'Unique non-empty string record identity field.'),
             'sequence_field': ConfigField('string', 'sequence_number', 'Integer sequence field.'),
             'minimum_value': ConfigField('optional_integer', None, 'Inclusive lower bound; null uses observed minimum.'),
             'maximum_value': ConfigField('optional_integer', None, 'Inclusive upper bound; null uses observed maximum.'),
             'allow_duplicates': ConfigField('boolean', True, 'Allow repeated sequence values.')})

    def requirements_for(self, config):
        from audit_engine.detectors import DetectorRequirements
        v = config.values
        if v['minimum_value'] is not None and v['maximum_value'] is not None and v['minimum_value'] > v['maximum_value']:
            raise ValueError('Minimum sequence bound exceeds maximum')
        return DetectorRequirements('1', {v['table']: tuple(sorted({v['id_field'], v['sequence_field']}))})

    def analyze(self, context, config):
        from audit_engine.detectors import result_for
        from audit_engine.execution import canonical_json
        v = config.values
        table, id_field, field = (v[key] for key in ('table', 'id_field', 'sequence_field'))
        records, identities = {}, set()
        # Validate the entire input before constructing any findings, even outside bounds.
        for row in context.tables[table]:
            record_id, value = row[id_field], row[field]
            if not isinstance(record_id, str) or not record_id or record_id in identities:
                raise ValueError('Record identities must be unique non-empty strings')
            identities.add(record_id)
            if value is None:
                continue
            if type(value) is not int:
                raise ValueError('Sequence values must be integers or null')
            candidate = (canonical_json({id_field: record_id}), record_id)
            if value in records:
                if not v['allow_duplicates']:
                    raise ValueError('Duplicate sequence values are forbidden')
                records[value] = min(records[value], candidate)
            else:
                records[value] = candidate

        observed = sorted(records)
        lower = v['minimum_value'] if v['minimum_value'] is not None else (observed[0] if observed else None)
        upper = v['maximum_value'] if v['maximum_value'] is not None else (observed[-1] if observed else None)
        findings = []
        metadata = self.metadata()

        def append_gap(start, end):
            content = {'table': table, 'id_field': id_field, 'sequence_field': field,
                       'missing_start': start, 'missing_end': end, 'missing_count': end - start + 1}
            evidence = []
            left, right = bisect_left(observed, start) - 1, bisect_right(observed, end)
            for index, role in ((left, 'before_gap'), (right, 'after_gap')):
                if 0 <= index < len(observed):
                    value = observed[index]
                    evidence.append(Evidence('', table, {id_field: records[value][1]}, field, value,
                        {'sequence_role': role, **content, 'minimum_value': v['minimum_value'],
                         'maximum_value': v['maximum_value']}))
            label = str(start) if start == end else f'{start}-{end}'
            # The frozen Finding contract has no content field. Canonical JSON identity
            # retains structured range data even when no source evidence exists.
            findings.append(Finding('', metadata.detector_id, 'SEQUENCE_GAP', 'Sequence gap',
                f'Sequence gap detected in {table}.{field}: {label}.', Severity.MEDIUM, 1.0,
                'sequence_range', canonical_json(content), tuple(evidence), context.snapshot.snapshot_id, ''))

        # A single bound with no observations cannot define a finite interval.
        # Inferred reversed bounds describe an empty expected population.
        if lower is not None and upper is not None and lower <= upper:
            cursor = lower
            for value in observed:
                if value < lower:
                    continue
                if value > upper:
                    break
                if cursor < value:
                    append_gap(cursor, value - 1)
                cursor = value + 1
            if cursor <= upper:
                append_gap(cursor, upper)
        return result_for(metadata, context, config, 'Sequence continuity evaluation completed', tuple(findings))
