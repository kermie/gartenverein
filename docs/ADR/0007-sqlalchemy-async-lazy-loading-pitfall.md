# SQLAlchemy async: lazy-loading pitfall

Freshly created objects (`db.add()` + `commit()`, not loaded via a query
with `selectinload`) do not have their `relationship` fields eagerly
loaded. A later synchronous access to one (`object.relationship`) triggers
a lazy load, which raises `MissingGreenlet` with the async database
driver. This affected `ParzelleVersicherung.zusatzpersonen` and
`Zaehlpunkt` relationships.

**Rule:** after creating a new row with relationships that will be needed
later, explicitly reload the row with `selectinload(...)` instead of
continuing to use the original (freshly created) object.

