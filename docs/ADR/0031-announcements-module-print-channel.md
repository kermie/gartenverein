# Announcements module: print channel

**WeasyPrint over a lower-level PDF library, per the original plan.**
HTML/CSS -> PDF fits this project's stack (Jinja2-style templating
mindset, no need to hand-place text boxes) far better than a
coordinate-based library like reportlab would have.

**Real page-count measurement, not a heuristic, decides whether
content fits.** `app.announcement_utils.likely_fits_one_print_page()`
(a word-count guess, added back in the foundation phase purely as a
cheap UI hint) is *not* what decides shortening here -- the print
channel renders the actual PDF and checks `len(document.pages)`, since
that's the only way to know for certain, and a word-count guess would
inevitably be wrong for some combination of image size, title length,
and branding.

**Shortening happens paragraph-by-paragraph via repeated real
renders, not a single word-count-based truncation.** Cutting to
"approximately N words" can't account for how the specific text
reflows around the image and header on this specific page; rendering
each candidate length and checking the real result is slower but
actually correct. The search drops from the end (most content kept
first) and stops at the first attempt that fits.

**The shortened text is persisted onto `print_text_override`, not
just used for one render.** Consistent with that field's original
design (see the foundation-phase ADR entry above): it must remain a
real, freely editable field, not a computed preview regenerated from
scratch every time. This also means regenerating the PDF later doesn't
repeat the same search.

**The QR code requires a live check against WordPress, not a cached
URL.** A draft has no public URL. Storing one at draft-creation time
would either be wrong (nothing to store yet) or go stale (the club
publishes later, but Parcella never finds out). Instead, BLOG
deliveries now also store `external_id` (migration
`0031_delivery_external_id`) -- the raw WordPress post ID -- and the
print channel asks WordPress directly, at generation time, whether
that post's status is now `publish` and what its current `link` is
(`WordPressPublisher.get_public_url_if_published`). If it's still a
draft, the QR code is simply omitted -- generating the PDF is never
blocked on this.

**`PrintTooLongError` stops generation rather than truncating
further or emitting a multi-page file.** Per the original design
decision: if even a single paragraph doesn't fit alongside the
header/footer/image, that's a case for a human to shorten the source
text by hand, not for the software to guess at further.

**Images and the logo are embedded as base64 data URIs.** Avoids
depending on WeasyPrint resolving relative filesystem paths correctly
inside the rendering process, or on the app being able to reach its
own HTTP server to fetch its own uploaded files -- both are
unnecessary failure modes when the bytes are already available
directly from disk at render time.

