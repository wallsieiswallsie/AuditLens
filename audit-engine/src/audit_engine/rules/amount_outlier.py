"""Deterministic Tukey median-of-halves monetary control over frozen records."""
from decimal import Context, Decimal, MAX_EMAX, MIN_EMIN, localcontext
import re

from audit_engine.models.contracts import Evidence, Finding, Severity, plain


def parse_amount(value):
    """Exact plain decimal strings only; never coerce other snapshot scalar types."""
    if type(value) is not str or not re.fullmatch(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?', value):
        raise ValueError('Amount must be an exact plain decimal string')
    return Decimal(value)


def decimal_context(values):
    # Align all coefficients to the largest fractional scale. The extra digits
    # cover carries, division by two, and both fence additions. Construct a fresh
    # Context so caller precision, rounding, traps and exponent bounds cannot leak.
    integer = max(max(value.adjusted() + 1, 1) for value in values)
    fraction = max(max(-value.as_tuple().exponent, 0) for value in values)
    return Context(prec=2 * (integer + fraction) + 10, Emin=MIN_EMIN, Emax=MAX_EMAX)


def decimal_string(value):
    """Plain exact notation, at least two places; retain necessary sub-cent digits."""
    if not value.is_finite():
        raise ValueError('Non-finite statistic')
    if value == 0:
        return '0.00'
    whole, _, fraction = format(value, 'f').partition('.')
    return whole + '.' + fraction.rstrip('0').ljust(2, '0')


def quartiles(ordered):
    """Tukey halves of already sorted Decimals; exclude the odd overall median."""
    if len(ordered) < 4:
        raise ValueError('At least four observations required')
    def median(values):
        middle = len(values) // 2
        return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / Decimal(2)
    with localcontext(decimal_context(ordered)):
        middle = len(ordered) // 2
        return median(ordered[:middle]), median(ordered[middle + len(ordered) % 2:])


class AmountOutlierDetector:
    def metadata(self):
        from audit_engine.detectors import ConfigField, DetectorMetadata, DetectorRequirements
        return DetectorMetadata(
            'business.amount_outlier', '1.0.0', 'Amount outlier',
            'Identify unusual monetary values using Tukey IQR fences.', 'monetary_anomaly',
            DetectorRequirements('1', {'payments': ('id', 'amount')}),
            {'table': ConfigField('string', 'payments', 'Snapshot table to evaluate.'),
             'id_field': ConfigField('string', 'id', 'Unique non-empty string record identity.'),
             'amount_field': ConfigField('string', 'amount', 'Exact plain decimal string or null.'),
             'group_by_fields': ConfigField('list[string]', (), 'Distinct ordered grouping fields; empty means whole table.'),
             'iqr_multiplier': ConfigField('string', '1.5', 'Positive canonical decimal string; no exponent or trailing fractional zeros.'),
             'minimum_sample_size': ConfigField('integer', 8, 'Eligible observations per group; at least four.'),
             'detect_lower_outliers': ConfigField('boolean', False, 'Report values strictly below the lower fence.'),
             'detect_upper_outliers': ConfigField('boolean', True, 'Report values strictly above the upper fence.'),
             'ignore_zero': ConfigField('boolean', False, 'Exclude exact zero from population and findings.'),
             'ignore_negative': ConfigField('boolean', False, 'Exclude negative values from population and findings.')})

    def requirements_for(self, config):
        from audit_engine.detectors import DetectorRequirements
        v = config.values
        if len(set(v['group_by_fields'])) != len(v['group_by_fields']):
            raise ValueError('Grouping fields must be distinct')
        if not re.fullmatch(r'(0|[1-9][0-9]*)(\.[0-9]*[1-9])?', v['iqr_multiplier']) or Decimal(v['iqr_multiplier']) <= 0:
            raise ValueError('Multiplier must be a positive canonical decimal string')
        if v['minimum_sample_size'] < 4:
            raise ValueError('Minimum sample size must be at least four')
        if not (v['detect_lower_outliers'] or v['detect_upper_outliers']):
            raise ValueError('At least one outlier direction must be enabled')
        return DetectorRequirements('1', {v['table']: tuple(sorted({v['id_field'], v['amount_field'], *v['group_by_fields']}))})

    def analyze(self, context, config):
        from audit_engine.detectors import result_for
        from audit_engine.execution import canonical_json
        v = config.values
        table, id_field, field = (v[key] for key in ('table', 'id_field', 'amount_field'))
        fields = v['group_by_fields']
        groups, identities = {}, set()
        for row in context.tables[table]:
            record_id, original = row[id_field], row[field]
            if type(record_id) is not str or not record_id or record_id in identities:
                raise ValueError('Record identities must be unique non-empty strings')
            identities.add(record_id)
            if original is None:
                continue
            amount = parse_amount(original)
            if (v['ignore_zero'] and amount == 0) or (v['ignore_negative'] and amount < 0):
                continue
            values = [plain(row[name]) for name in fields]
            key = canonical_json(values)
            groups.setdefault(key, []).append((amount, record_id, original, values))

        multiplier = Decimal(v['iqr_multiplier'])
        metadata, findings = self.metadata(), []
        for records in groups.values():
            if len(records) < v['minimum_sample_size']:
                continue
            ordered = sorted(record[0] for record in records)
            with localcontext(decimal_context([*ordered, multiplier])):
                q1, q3 = quartiles(ordered)
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
                statistics = {name: decimal_string(value) for name, value in
                              (('q1', q1), ('q3', q3), ('iqr', iqr), ('lower_fence', lower), ('upper_fence', upper))}
                for amount, record_id, original, values in records:
                    direction = ('lower' if v['detect_lower_outliers'] and amount < lower else
                                 'upper' if v['detect_upper_outliers'] and amount > upper else None)
                    if direction is None:
                        continue
                    content = {'amount_field': field, 'amount': original, 'direction': direction,
                               **statistics, 'iqr_multiplier': v['iqr_multiplier'], 'sample_size': len(records),
                               'group_by_fields': list(fields), 'group_values': values}
                    evidence = Evidence('', table, {id_field: record_id}, field, original, content)
                    findings.append(Finding('', metadata.detector_id, 'AMOUNT_OUTLIER', 'Amount outlier',
                        f'Amount is strictly beyond the {direction} Tukey IQR fence.', Severity.MEDIUM, 1.0,
                        table, record_id, (evidence,), context.snapshot.snapshot_id, ''))
        findings.sort(key=lambda finding: finding.entity_id)
        return result_for(metadata, context, config, 'Tukey IQR amount evaluation completed', tuple(findings))
