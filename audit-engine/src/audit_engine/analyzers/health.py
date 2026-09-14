"""Pipeline smoke check only; receives frozen data, never a connection."""
from audit_engine.models.contracts import AuditContext


def check(context: AuditContext):
    for table, entry in context.snapshot.manifest.items():
        if len(context.tables[table]) != entry.rows:
            raise ValueError('Unreadable snapshot population')
    return 'Snapshot readable; no business audit checks executed'
