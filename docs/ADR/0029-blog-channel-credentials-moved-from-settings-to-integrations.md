# Blog channel: credentials moved from Settings to Integrations

WordPress blog credentials were initially added to Admin -> Settings,
reusing the generic `SETTINGS_FIELDS` mechanism (encrypted storage,
"blank = unchanged", masked placeholder -- all built for SMTP) purely
because it was the path of least implementation effort. On review,
that reasoning was about implementation convenience, not where a board
member configuring this would actually expect to find it: Integrations
is already "the page where Parcella connects to other systems" (it's
where the public-signup API token lives), and WordPress blog
credentials are the same category of thing, just pointed in the
opposite direction. Moved to a dedicated card on
Admin -> Integrations with its own form handling
(`app/routers/admin.py`'s `integrations_wordpress_speichern` /
`integrations_wordpress_testen`), hand-rolling the same "blank
Application Password field leaves the existing one unchanged"
convention rather than reusing `SETTINGS_FIELDS` -- a small amount of
extra code in exchange for the credentials living where they
conceptually belong. No schema change was needed: the underlying
`ClubSetting` keys (`wordpress_site_url`/`wordpress_username`/
`wordpress_app_password`) are unchanged, only which admin page reads
and writes them.

