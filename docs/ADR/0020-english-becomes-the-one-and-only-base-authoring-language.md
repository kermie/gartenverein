# English becomes the one and only base/authoring language

**Context:** the project started as a personal tool with German as the
natural authoring language throughout -- identifiers were English from
early on (see the module-renaming entries above), but UI text, code
comments, and docstrings stayed German, and for a while there was even a
brief split where German was "the authoring language" while English was
merely "the runtime fallback" (see the i18n entry above, left unedited
as a record of that). As this became a genuine open-source project meant
for adoption by any allotment-garden association in any country, that
split stopped making sense: a contributor who doesn't read German
shouldn't hit a language barrier reading the code, and a translator
working from the UI-text source of truth shouldn't need to go through
German first.

**Decision: English is the one and only base/authoring language, full
stop.** Not "also," not "as well as German" -- the prior split between
an authoring language and a fallback language is gone. Concretely:
- New UI text is written in English first, then translated into the
  other six languages (`app/translations/en.json` is the source of
  truth other language files are validated against, not `de.json`).
- New code comments and docstrings are written in English.
- The REST API's hardcoded error `detail=` strings (previously German,
  see the i18n entry above) are now English too.

**What this does NOT mean:** a one-time mechanical sweep translating
every existing German comment and docstring across the whole codebase
in a single pass. That's a large, low-risk-per-line but high-volume
change spanning nearly every file, and batch-translating it without care
risks subtly mangling technical nuance that was fine in the original
German. The policy applies to new work from now on; existing German
comments are being translated incrementally as files are touched for
other reasons, not stripped out in one disruptive commit. High-value,
low-risk spots (a module's own docstring describing its own behavior,
like `app/i18n.py`'s) are translated opportunistically when working in
the area anyway.

**German is not going away as a supported language** -- this is purely
about which language the *source* is written in and read from; `de.json`
remains one of the seven fully-supported UI languages, same as before.

