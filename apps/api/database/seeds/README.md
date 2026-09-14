# Seed workflow

`npm run db:seed` uses [workflow.js](workflow.js) to load the modular generator in a single PostgreSQL transaction. Tables must be empty. `npm run db:reset` deletes only local business rows with explicit opt-in. See [dataset instructions](../../docs/16-SYNTHETIC-DATASET.md). This is development fixture tooling, not an operational API or audit engine.
