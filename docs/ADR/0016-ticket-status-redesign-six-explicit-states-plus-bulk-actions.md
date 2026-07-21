# Ticket status redesign: six explicit states, plus bulk actions

**Context:** the original four statuses (`UNASSIGNED`, `ASSIGNED`,
`DEFERRED`, `CLOSED`) didn't give the board what they actually needed
day-to-day: no way to mark "we replied, waiting on the customer" as
distinct from "just sitting in the queue," no real hiding of postponed
tickets (see below), and no way to act on more than one ticket at a
time.

**Decision: six statuses -- `ACTIVE`, `ASSIGNED`, `WAITING`, `POSTPONED`,
`CLOSED`, `DELETED`.** `WAITING` (new) means the ticket is waiting on the
sender's reply -- no date attached, manually set, and cleared the moment
a new reply arrives. `DELETED` (new) is a genuine soft-delete modeled as
a status rather than a separate `deleted_at` column, since `Ticket`
didn't have one and a sixth enum value was simpler than adding a column
plus updating every query. `DELETED` tickets are hidden from every
filter, including "All" -- no trash/recovery view was built, since it
wasn't asked for.

**Decision: `POSTPONED` tickets are actually hidden, and actually
reactivate -- not just computed for display.** The original `DEFERRED`
status was purely a computed display flag (`is_due`); the underlying
ticket stayed visible in the active list the whole time, just with an
"overdue" badge once its date passed. That never matched what "postponed"
should mean. Now a postponed ticket disappears from Active/Mine
entirely until its date, and once the date passes, a lazy check (run on
every ticket-list or ticket-detail page load, since there's no
scheduler in this app) actually flips its status in the database back
to `ACTIVE`/`ASSIGNED`. Extended the pre-existing "closed ticket reopens
on a new reply" logic to also cover `POSTPONED` and `WAITING` -- one
consistent rule: any reply from the sender clears whichever "we're
waiting" state a ticket was in, regardless of which one.

**Decision: bulk actions via one form, two `formaction` buttons, not two
forms.** The ticket list needed both "change status for N selected
tickets" and "assign N selected tickets to one user" -- two different
actions over the same selection. Duplicating the checkboxes across two
separate `<form>`s (and keeping their selection state in sync via JS)
would have been more fragile than the alternative: one form with all the
checkboxes, and each action's submit button overrides the form's
`action` via the HTML `formaction` attribute. No JS needed to keep two
selections in sync, because there's only ever one.

