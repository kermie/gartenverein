# Inventory module

**Freely-configurable categories, not a fixed enum.** The original
request was explicit: groupings need to be something the club
configures itself (playground equipment, fences, locks & keys, water
infrastructure, etc.), not something requiring a code change to add
or rename. `InventoryCategory` is a plain lookup table, same shape as
`ClubRole`.

**Quantity-per-item rather than one row per physical unit,** confirmed
with the person requesting this feature before building it, since it's
a genuine fork: three wheelbarrows are one `InventoryItem` row with
`quantity_total = 3`, not three near-duplicate rows. Loans check out a
quantity, not a specific unit, and `available_quantity` is computed
from `quantity_total` minus what's currently on loan.

**Current value is manually maintained, not computed via
depreciation** -- also confirmed directly rather than assumed. A
depreciation formula needs a useful-life assumption per category and
produces a number that looks precise while really being a guess in a
formula's clothing. Manual entry with a visible "last checked" date is
more honest about what the number actually represents.

**Personally-owned items get the same financial fields as club-owned
ones** -- again confirmed directly: the instinct to skip financial
tracking for "just a member's personal tent" was wrong here, since
insurance/liability records are the actual reason to track these
items at all.

**`retired_at` (soft) vs. hard delete are two different, deliberate
actions.** A real asset register needs disposed-of items to remain on
record (financial history, loan history) rather than vanishing;
`retired_at` marks that without deleting anything, and is excluded
from the default list view but not from the data. Hard delete stays
available for genuine data-entry mistakes, and does cascade-delete
loan history, since a mistaken entry never had real history to
preserve.

**A route-ordering bug and a lazy-load bug were both found and fixed
while building this** -- see `docs/module-inventory.md` for the full
detail on each. Worth internalizing as house style: any router with a
single-segment `/{id}` catch-all needs every literal-path route
registered before it, and `db.refresh(obj, attribute_names=[...])`
after a commit only protects the named attributes, not the whole
object -- a full re-query is the safer pattern when the response needs
more than what's in `attribute_names`.

