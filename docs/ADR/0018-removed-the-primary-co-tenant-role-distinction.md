# Removed the primary/co-tenant role distinction

**Context:** `member_parcels` originally had `is_primary_tenant`, marking
one resident of a parcel as the "primary" tenant and any others as
"co-tenants." The board's actual position: liability for a parcel (e.g.
outstanding mandatory-hours debt) is held jointly by everyone assigned to
it, regardless of who signed first -- the hierarchy didn't reflect how
responsibility is actually assigned. Migration `0022_remove_tenant_role`
drops the column; either a member is currently assigned to a parcel or
they aren't, with no rank between residents.

**The one place this wasn't just a UI label:** insurance auto-coverage.
`household_grouping()` in `app/insurance_utils.py` previously anchored on
"same address as the primary tenant" to decide who's automatically
covered by the accident-insurance base amount vs. who needs opt-in
coverage for an extra charge. With no more designated "primary" person,
that anchor doesn't exist. Reworked to group current residents by
matching address to *each other* instead: the largest address-matching
group becomes the auto-covered household, everyone else (different or no
address on file) stays opt-in/external. Same result for the common case
(one household on a parcel), but arguably more correct than the old
logic for the edge case of 3+ residents where two share an address that
happens to differ from whoever was marked "primary" -- the old code
would have incorrectly split them from each other.

**Reworded, not just removed:** the German UI text explaining
auto-coverage ("gleiche Adresse wie Hauptpächter") referenced the
now-gone concept directly and needed rewording (in all 7 languages, not
just German) to describe the actual mechanism ("share an address with
other residents") rather than a no-longer-existing role.

