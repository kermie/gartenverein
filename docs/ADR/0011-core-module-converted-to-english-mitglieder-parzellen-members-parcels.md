# Core module converted to English (Mitglieder/Parzellen -> Members/Parcels)

**Why now, not later:** as long as only one association uses the software
in production, every point in time is more favorable than the next. Once
external associations or contributors join, every rename of tables, URLs,
and API endpoints becomes a breaking change. The association therefore
deliberately chose a rigorous, complete conversion -- no half-finished
result, even if it means more effort in the short term.

**Proceeded module by module, core module first.** Members/Parcels are
anchored via foreign keys in practically every other module (work hours,
metering, insurance, tickets, purchase requests) -- so they had to be
converted first, as the template for all following modules. Other modules
deliberately kept their German identifiers (tables, own columns, URLs) for
the time being -- only their foreign-key references to the new
`members`/`parcels` tables and the `Member`/`Parcel` class names had to be
updated as well, otherwise the app would no longer have run after this
step.

**CamelCase word boundaries as a stumbling block for automated renames.**
A script using `\bMitglied\b`/`\bParzelle\b` word-boundary regex does NOT
hit compound class names like `MitgliedVereinsrolle` or
`ParzelleVersicherung` (no regex word-boundary transition between a
lowercase and an uppercase letter in camelCase) -- that was desired here
(those classes belong to other modules, their own round comes later), but
it would have equally missed "MitgliedParzelle" (the actual core class)
had it not been explicitly handled as a compound string beforehand.
Lesson: with automated renames in code, ALWAYS first check which compound
identifiers a word-boundary regex actually does (or doesn't) catch, before
relying on the result.

**SQLAlchemy identity map + relationship attribute names are a chain
trap.** When renaming `relationship()` attributes (e.g.
`MitgliedParzelle.mitglied` -> `MemberParcel.member`), it's not enough to
just change the definition -- EVERY caller that reads `.mitglied` on a
`MemberParcel` object breaks with `AttributeError`. These accesses are
spread across many modules (work-hours evaluation, insurance household
detection, dashboard statistics), since `Parcel.member_assignments`/
`Member.parcel_assignments` are iterated almost everywhere. A plain
`\bmitglied\b` word-boundary regex couldn't have cleanly distinguished
this from unrelated local variables of the same name in OTHER, not-yet-
converted modules -- targeted, file-by-file review was needed here
instead of a blind global replace.

**Found orphaned schema fields while cleaning up.** Both
`ParzelleUpdate.kuendigung_datum` (Pydantic) and the corresponding column
should have been removed long ago (migration 0006 had already dropped the
DB column) -- only the API schema had lagged behind. This surfaced during
the thorough pass for the rename and was cleaned up along with it.

