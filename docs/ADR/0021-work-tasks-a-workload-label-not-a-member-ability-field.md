# Work tasks: a workload label, not a member-ability field

**Context:** the feature request was explicit that tasks should be
matchable to the right person -- specifically calling out that elderly
or disabled members should get lighter work while younger, stronger
members handle more demanding tasks. The tempting, "obvious" way to
build that is a field on the Member record (age already exists via
`date_of_birth`; a new field for health/ability/mobility would complete
the picture) and some matching logic that uses it.

**Decision: the system stores none of that.** `WorkTask.workload` is a
plain three-value label (Light / Moderate / Demanding) describing the
*task*, never the person. There's no field anywhere recording a
member's health, ability, or any reason they might need lighter work,
and no automated suggestion or matching logic at all -- assigning a task
to a participant is a single manual dropdown selection made by whoever
is coordinating that session.

**Why:** the actual judgment of who's suited to which task belongs to a
human who knows the person -- their health, their preferences on a given
day, whether they mentioned a bad back last week -- none of which
belongs in a database record, and none of which this software could
reason about responsibly even if it were stored. A stored "ability"
field would also inevitably drift out of date, and worse, would frame a
volunteer's capability as a fixed data point rather than something they
get to communicate for themselves each time. The workload label on the
*task* solves the actual coordination problem (knowing at a glance which
jobs are light) without creating a sensitive, easily-stale, and
easily-misused attribute on a person.

