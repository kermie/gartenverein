# i18n: one language per installation, English as runtime fallback

**Note: superseded in part.** The "authoring language" half of the
second decision below was German at the time this was written; it has
since changed to English (see "English becomes the one and only
base/authoring language" further down). Left as-is here rather than
edited, so the history of the decision is visible -- the "one language
per installation" decision and the "English as runtime fallback/default"
decision are both still accurate as written.

**Context:** the software started German-only. Making it a genuine
open-source product meant supporting other languages -- but *how* the
language is chosen matters as much as the translation content itself.

**Decision: one language per installation, not per user, not
browser-detected.** A shared club-management tool where different board
members privately see different languages would be more confusing than
helpful for a small volunteer-run association -- everyone should be
looking at the same labels when discussing the same screen together.
The admin picks a language once in Admin -> Settings; it applies to
everyone. This ruled out both a per-user profile setting and an
`Accept-Language`-header-based auto-detection.

**Decision (superseded, see note above): German remains the authoring
source language, but English is the runtime fallback -- not the same
thing.** New UI text is still written in German first (that hasn't
changed), but if a translation key is missing for whichever language is
currently selected -- most likely because a module hasn't been
translated into that language yet -- the string falls back to English,
not German. Same for a completely fresh install with no language chosen
yet: it starts in English. This was a deliberate, explicit request (not
an oversight) to make English the "safe default" a new international
user lands on, rather than German text they may not read. The two
decisions (source language vs. runtime default) are controlled by two
different mechanisms in `app/i18n.py` and can, in principle, diverge
further if needed.

**Implementation:** JSON translation catalogs (one file per language,
`app/translations/<code>.json`), loaded once at startup. `t()` in
templates, `t_for(request, ...)` in Python for web-UI-facing error
messages. REST API error messages (`detail=` strings in `api_*.py`
routers) are hardcoded English rather than going through the JSON
catalogs -- the API is for programmatic integrations, not a
language-switchable human UI, so a fixed language is fine there; it
just needed to be English rather than German once English became the
project's base language (see the entry on that below).

