# Synthetic fixture artifacts

Default seed 20260914, dataset version 1.0.0. `npm run db:generate` validates and regenerates metadata, ground truth, policy and three-row examples. The full dataset is generated in memory and loaded with db:seed; it is not duplicated here.

Ground truth is development/test/benchmark-only. Future audit detection must never consume it. Policy is separate expected configuration. See [dataset documentation](../../docs/16-SYNTHETIC-DATASET.md) for units, reproducibility and limitations.
