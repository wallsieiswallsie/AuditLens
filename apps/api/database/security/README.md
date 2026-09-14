# Source-reader administration

The explicit provisioner creates auditlens_source_reader as NOLOGIN, non-superuser, NOINHERIT, NOCREATEDB, NOCREATEROLE, NOREPLICATION and NOBYPASSRLS. It grants CONNECT, USAGE on business and SELECT on the eleven TABLES entries in the generator contract. It grants no sequence access, source writes, schema creation or audit access. It refuses an existing role with unsafe flags, parent memberships or object ownership. Runtime evidence belongs in [VERIFICATION](../../../../docs/VERIFICATION.md), not this provisioning specification.

Run only as the dedicated database's migration owner with role administration rights, after migrations:

```powershell
# Confirm this is your dedicated local development database first.
$env:AUDITLENS_ALLOW_READER_PROVISION='YES'
npm run db:provision-reader
Remove-Item Env:AUDITLENS_ALLOW_READER_PROVISION
```

The CLI also enforces development, a loopback URL with no query overrides, a password and database name auditlens. It never runs automatically at API startup. A Railway administrator must separately review and apply the API-owned provisionReader function in a controlled administration session; the local CLI deliberately refuses remote URLs. No remote role is claimed provisioned.

Provisioning changes PUBLIC permissions across this dedicated database: removes database CREATE/TEMP, all PUBLIC privileges in business/audit/public and existing tables/sequences/routines there, then grants only the reader allowlist. Review impacts on any other identities before applying. The administrator/owner retains ownership rights. CONNECT through PUBLIC is unchanged. PostgreSQL system catalogs remain normally visible; SELECT-only describes application source privileges, not invisible system metadata or protection against the administrator.

Future tables receive no automatic reader grant. For the provisioning owner, global PUBLIC function EXECUTE and global/schema table defaults are revoked, together with schema routine defaults. Re-run provisioning after adding an explicitly approved source table; independently review defaults for every other future object owner. Do not add reader memberships or publicly executable write-capable functions. Grants must be reverified after schema/role changes; this is not continuous drift monitoring.

The role is a permission group, with no password in Git. Acceptance creates an ephemeral non-superuser login, grants SET access to this role, and uses a separate authenticated connection with SET ROLE. It checks actual PostgreSQL denials, not mocks or a read-only transaction that would mask excess write grants. Each attempt rolls back, then fixture hashes and empty audit schema are checked. The login/password and cluster are only test infrastructure. A future extraction login must be separately provisioned with no parent privileges except this reader role. Its server-side secret and connection contract are deferred; DATABASE_URL remains the only current application database variable. Web receives none.

Use npm run test:db for the complete private-cluster acceptance. It requires PostgreSQL 17+ initdb and pg_ctl on PATH (or PG_BIN), creates random credentials and an unused loopback port, ignores any existing DATABASE_URL, and stops the server in finally. Temporary cluster files are retained for diagnosis; the password file is removed immediately after initialization. Never substitute a production URL. Normal npm test performs no live database writes.
