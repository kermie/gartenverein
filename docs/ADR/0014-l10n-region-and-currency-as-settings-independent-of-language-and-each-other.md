# l10n: region and currency as settings independent of language and each other

**Context:** once several languages existed, it became obvious that
"language" and "regional formatting conventions" are not the same axis.
An English-speaking board member isn't necessarily using GBP; a
French-speaking one isn't necessarily in France. Tying number format or
currency to the language selector would have been a false shortcut.

**Decision:** two more `ClubSettings`, `region` and `currency`, each
independently selectable from `language` and from each other. `region`
(a Babel locale string like `de_DE`, `en_GB`, `fr_FR`) drives number
formatting and address field order; `currency` (an ISO code like `EUR`,
`GBP`) drives the money symbol and its position. Defaults (`de_DE` /
`EUR`) were chosen to match where this software actually runs today,
independent of the `language` default being English -- these three
settings don't have to agree, and in practice often won't for
associations outside German-speaking countries.

**Decision: use Babel instead of hand-rolled formatting.** Before this,
formatting was ad-hoc and broken for anything but German -- e.g. the
dashboard had a literal `.format(x).replace(",", ".")` hack to force
German-style thousands separators, and every monetary value across ~30
templates hardcoded a trailing `€`. Babel's `format_currency`/
`format_decimal` get real per-locale nuances right that are easy to miss
by hand: Dutch puts the symbol *before* the number (`€ 1.234,50`), French
uses a narrow no-break space for thousands and a non-breaking space
before the symbol (`3 000,00 €`), British English has no space at all
between symbol and number (`£127.50`). Two Jinja filters (`money`,
`number`) replace every hand-written format string app-wide.

**Decision: address format via a five-line dict, not a library.** Full
address-formatting libraries (e.g. Google's `libaddressinput` data)
model dozens of countries with genuinely different field structures.
Across the 7 countries this project currently supports, the only real
variation is whether the postal code sits before the city (continental
Europe) or gets its own line after the city (UK) -- a small
region-to-template dict in `app/l10n.py` covers that completely without
pulling in a much larger dependency. Revisit if a country with a
genuinely different address structure gets added later.

See [i18n & l10n](../i18n-l10n.md) for the practical how-to (adding a
language, a region, a currency).

