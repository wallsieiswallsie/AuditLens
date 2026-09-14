import assert from 'node:assert/strict';
import { TABLES } from '../generators/core.js';

export const READER = 'auditlens_source_reader';

// Explicit administration, never a startup migration. Intended for a dedicated database.
export async function provisionReader(db) {
  await db.transaction(async trx => {
    const identity = (await trx.raw('SELECT current_user AS owner, current_database() AS database')).rows[0];
    const role = (await trx.raw('SELECT * FROM pg_catalog.pg_roles WHERE rolname=?', [READER])).rows[0];
    if (role) {
      assert.ok(!role.rolsuper && !role.rolcreatedb && !role.rolcreaterole && !role.rolreplication && !role.rolbypassrls && !role.rolcanlogin, 'Reader role has unsafe attributes');
      assert.equal((await trx.raw('SELECT 1 FROM pg_catalog.pg_auth_members WHERE member=?', [role.oid])).rows.length, 0, 'Reader must have no parent roles');
      assert.equal((await trx.raw("SELECT 1 FROM pg_catalog.pg_shdepend WHERE refclassid='pg_authid'::regclass AND refobjid=? AND deptype='o'", [role.oid])).rows.length, 0, 'Reader must not own objects');
    } else {
      await trx.raw('CREATE ROLE ?? NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS', [READER]);
    }
    // PUBLIC is inherited by every role. Revoking only direct reader grants is insufficient.
    await trx.raw('REVOKE CREATE, TEMPORARY ON DATABASE ?? FROM PUBLIC', [identity.database]);
    await trx.raw('REVOKE ALL ON DATABASE ?? FROM ??', [identity.database, READER]);
    await trx.raw('GRANT CONNECT ON DATABASE ?? TO ??', [identity.database, READER]);
    for (const schema of ['public', 'business', 'audit']) {
      await trx.raw('REVOKE ALL ON SCHEMA ?? FROM PUBLIC, ??', [schema, READER]);
      await trx.raw('REVOKE ALL ON ALL TABLES IN SCHEMA ?? FROM PUBLIC, ??', [schema, READER]);
      await trx.raw('REVOKE ALL ON ALL SEQUENCES IN SCHEMA ?? FROM PUBLIC, ??', [schema, READER]);
      await trx.raw('REVOKE ALL ON ALL ROUTINES IN SCHEMA ?? FROM PUBLIC, ??', [schema, READER]);
    }
    // Global defaults matter: schema-scoped revokes cannot remove global PUBLIC EXECUTE.
    await trx.raw('ALTER DEFAULT PRIVILEGES FOR ROLE ?? REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC', [identity.owner]);
    await trx.raw('ALTER DEFAULT PRIVILEGES FOR ROLE ?? REVOKE ALL ON TABLES FROM PUBLIC, ??', [identity.owner, READER]);
    for (const schema of ['public', 'business', 'audit']) {
      await trx.raw('ALTER DEFAULT PRIVILEGES FOR ROLE ?? IN SCHEMA ?? REVOKE ALL ON TABLES FROM PUBLIC, ??', [identity.owner, schema, READER]);
      await trx.raw('ALTER DEFAULT PRIVILEGES FOR ROLE ?? IN SCHEMA ?? REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, ??', [identity.owner, schema, READER]);
    }
    await trx.raw('GRANT USAGE ON SCHEMA business TO ??', [READER]);
    for (const name of TABLES) await trx.raw('GRANT SELECT ON TABLE ??.?? TO ??', ['business', name, READER]);
  });
}
