# Historization: ending instead of deleting

A recurring pattern throughout the project: tenant assignments, water
meters, club-role memberships are not deleted when they "end", but ended
via an "until" date (or an `is_active` flag + removal date). This keeps
the history searchable ("who was the tenant of G042 in 2019?") without
needing a separate archive table.

