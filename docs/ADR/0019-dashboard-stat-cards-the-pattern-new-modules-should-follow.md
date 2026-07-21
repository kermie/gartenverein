# Dashboard stat cards: the pattern new modules should follow

**Context:** the dashboard started with four stat cards (Members, Active
Parcels, Terminated, Total Area) for the core module. As Purchase
Requests and Tickets got their own cards, it was worth writing down the
pattern so the *next* module's dashboard card doesn't reinvent it
slightly differently each time.

**The pattern:** one `col-sm-6 col-xl-3` card per stat, appended to the
same row as the existing ones (Bootstrap wraps extras to a new row
automatically -- with an optional module's card, the row won't always
divide evenly, and that's fine). Structure: icon in a colored circle,
big number, small uppercase label, a one-line footer link ("Show All" or
similar) to the filtered view that number represents. A short sub-line
under the number is optional and, when used, should flag something
actionable in a warning color (e.g. Active Parcels' "vacant" count,
Tickets' "N spam suspected") rather than restating the headline number
in different words.

**Always gate on the module flag, not on the count.** A card for an
optional module (Purchase Requests, Tickets) is wrapped in
`{% if request.state.module_flags.<name> %}` so it simply doesn't exist
for associations that don't use that module -- never shown-with-zero.
Core-module cards (Members, Parcels) have no such guard since those
modules can't be disabled.

**The stat query should match the list page's own default filter,
exactly.** The "Open Tickets" count uses the identical status set
(ACTIVE/ASSIGNED/WAITING) as `/tickets/`'s own "Active" filter tab, and
the footer link points at that same filtered URL -- so the number on the
dashboard and the list you land on after clicking always agree with each
other. This was a deliberate design constraint, prompted directly by the
bug below.

**Lesson from a real bug, not a hypothetical one:** the pre-existing
"Terminated" parcels card linked to `/parcels/?status_filter=gekuendigt`
-- a leftover German enum value from before the identifier-renaming work,
which no longer matched anything (`ParcelStatus` had long since become
`ACTIVE`/`TERMINATED`/`DELETED`). The filter silently matched zero
results, so the link just showed the full, unfiltered parcel list
instead. A hardcoded filter value in a dashboard link is exactly the
kind of stale reference that survives a rename undetected, because
nothing about it looks broken -- the link still worked, it just quietly
stopped filtering. Worth double-checking any hardcoded query-string
filter value against the actual current enum whenever either side
changes.

