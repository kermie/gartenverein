# Router factory for structurally identical modules

See the [metering documentation](../module-metering.md) for the
router-factory pattern. In short: when two modules (water/electricity)
are structurally identical and differ only in configuration values (unit,
icon, decimal places), a factory function is worth it instead of
duplicating code.

