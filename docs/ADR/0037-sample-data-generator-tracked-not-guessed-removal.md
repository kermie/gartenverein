# Sample data generator: tracked removal, not guessed

**Context:** An admin doing a fresh setup wants to explore every module
with realistic data before entering real records, and needs to remove
it all again afterward without hand-picking rows. `app/sample_data.py`
adds a one-click generator (`/admin/sample-data`) covering core
(members, parcels, assignments) plus every module that's enabled by
default: work hours, metering, insurance, tickets, purchase requests,
calendar, inventory, and the task board.

**Deliberately skipped:** `cloud_storage`, `announcements`, and
`public_signup_api` -- all three are off by default (see
`app/module_flags.py`) specifically because they carry real-world risk
(outbound credentials, an unauthenticated write endpoint, emailing
every member). Sample data for them would either be meaningless
(no credentials to fake) or actively risky to auto-populate.

**Tracked removal, not `is_sample` columns, not name-pattern matching,
not relying on cascade.** A new `SampleDataRecord` table logs
`(module, entity_type, entity_id)` for every row the generator creates,
as it creates it. "Remove all sample data" looks up exactly those rows
and deletes them -- nothing is inferred from a "DEMO-" prefix in a plot
number, and nothing relies on `ON DELETE CASCADE` happening to remove
the right things. The alternative (an `is_sample` boolean on every
business table) was rejected as far more invasive -- it would touch
nearly every table in the schema for a feature that's conceptually
orthogonal to any of them.

**Explicit leaf-to-root deletion order (`_DELETION_ORDER`), not
cascade-and-hope.** Removal deletes each tracked row explicitly via
`db.delete()` in a fixed leaf-to-root order (e.g. `SessionParticipation`
before `WorkSession`, `MemberParcel` before `Member`), rather than
deleting a handful of root rows and trusting `ON DELETE CASCADE` to
clean up the rest. Reason: it makes correctness independent of any
particular FK's `ondelete` setting -- if a future migration ever changes
a cascade to `RESTRICT` or `SET NULL`, removal still works, instead of
suddenly failing (or silently leaving orphans) because it happened to
rely on cascade behavior for a table it never explicitly deletes from.
It only ever issues `DELETE`s for rows logged in `SampleDataRecord` --
nothing not tracked is ever targeted directly.

**Known limitation, not solved by the above:** `ON DELETE CASCADE` is a
database-level property of the foreign key itself, and fires whenever a
referenced row is deleted -- regardless of which application code, or
in what order, issued that `DELETE`. If an admin creates a *real*
record that references a sample row before removing sample data (e.g. a
real `ItemLoan` against a sample member, since `ItemLoan.member_id` is
`CASCADE`), deleting that sample member as part of "remove all sample
data" will still cascade-delete the real `ItemLoan` along with it --
explicit ordering doesn't and can't prevent this, only foregoing
`CASCADE` on that FK entirely would. The intended workflow is "seed ->
explore -> remove sample data -> then enter real records," and the
admin UI says so; this is a real (if narrow) foot-gun for anyone who
doesn't follow that order, documented here rather than silently
accepted.

**Guard: blocked once real core data exists, not "always available."**
`add_sample_data()` refuses (`SampleDataBlockedError`) if any `Member`
or `Parcel` exists that isn't itself tracked as sample data. This is a
product decision, not a technical necessity -- removal is safe to run
against real data (it only ever touches tracked rows), but *adding*
sample data on top of a club's real membership list would be
confusing and easy to do by accident. Keeps this strictly a
fresh-install tool.

**No fake `User` accounts, ever.** Wherever a module optionally
references a `User` (ticket assignment, purchase-request approvals,
`created_by`/`recorded_by` fields), the generator either uses a real
existing account (found via a query, e.g. two distinct ADMIN/BOARD
users for the "approved" purchase-request demo) or leaves the field
`NULL`, or uses the module's own external-party fields where they exist
(`PurchaseRequest.requester_name`/`requester_email`, which the schema
already supports for non-login requesters). If fewer real users exist
than a particular demo scenario needs (e.g. only one board member, not
two), that specific scenario is skipped rather than inventing an
account -- user accounts are a security boundary and deliberately out
of scope for "demo data."

**Insurance household grouping is computed, not assumed.** The sample
parcel with two residents at different addresses (DEMO-03) needs an
`AccidentInsuranceAdditionalPerson` row for whichever resident
`household_grouping()` (`app/insurance_utils.py`) would classify as
"external" -- the generator calls that same function against the
in-memory `MemberParcel` objects it just built (assigning `.member`
directly, no DB round-trip needed) rather than hardcoding an assumption
about tie-breaking behavior.
