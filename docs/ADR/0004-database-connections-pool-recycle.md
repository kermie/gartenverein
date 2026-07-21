# Database connections: pool_recycle

**The bug:** after longer periods of inactivity (e.g. overnight), database
access occasionally failed with `MissingGreenlet` during the connection-
pool ping. Cause: `pool_pre_ping=True` alone isn't enough -- without
`pool_recycle`, connections in the pool can potentially stay open too
long, get silently terminated by the network/Postgres at some point, and
the ping mechanism then collides with the async driver.

**Fix:** `pool_recycle=1800` (30 minutes) in `app/database.py` --
proactively refreshes connections before they can go stale.

