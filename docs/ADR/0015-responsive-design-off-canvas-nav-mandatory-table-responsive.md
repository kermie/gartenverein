# Responsive design: off-canvas nav + mandatory `.table-responsive`

**Context:** the app was originally built and used almost exclusively on
desktop by board members at a computer. As usage extended to checking
things on a phone (e.g. during a work session, or a quick lookup at the
allotment itself), the always-visible sidebar and un-wrapped tables broke
down badly on narrow screens -- the sidebar ate half the viewport
permanently, and wide tables (5-8 columns: ticket lists, member lists,
annual evaluations) forced the whole page to scroll sideways instead of
just the table.

**Decision:** plain CSS media queries and a small amount of vanilla JS,
no frontend framework and no separate mobile template set. Below 768px:
the sidebar becomes an off-canvas overlay (hidden via
`transform: translateX(-100%)`, toggled by a hamburger button, closed by
backdrop tap / Escape / clicking a nav link), Bootstrap's small button
and form-control variants get a minimum touch-target height, and
`.btn-group` rows (e.g. ticket status filters) wrap instead of clipping.

**Rule going forward: every `<table>` gets wrapped in
`.table-responsive`, no exceptions.** This was audited in one pass across
all 46 templates at the time -- 16 of 19 tables were missing the wrapper.
Any new template with a table that skips this works fine on desktop and
silently breaks on mobile, which is exactly the kind of bug that doesn't
show up until someone happens to test on a phone.

**Bug found along the way:** the sidebar's "active page" highlighting for
Members/Parcels had silently never worked since those URLs were
translated from German to English (`/mitglieder` -> `/members/`) --
the highlighting logic still checked the old paths. Caught and fixed
during the same pass; a reminder that even a purely visual/CSS-focused
change is worth cross-checking against still-current routes.

See [Responsive Design](../responsive-design.md) for the practical
reference (breakpoints, what's automatic vs. what needs a per-template
wrapper, how to test it).

