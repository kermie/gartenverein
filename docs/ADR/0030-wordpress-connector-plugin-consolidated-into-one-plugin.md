# WordPress connector plugin: consolidated into one plugin

The original `parcella-work-signup` plugin was single-purpose (just
the work-session signup form). With more WordPress <-> Parcella
integrations planned in the same direction -- WordPress calling
Parcella, the same direction as signup -- (a contact-form-to-tickets
bridge, applicant management, calendar display via shortcode instead
of passive ICS), each shipping as its own separate plugin would mean a
club installs and configures N plugins, each asking for the same base
URL and API token again. Consolidated into `parcella-connector`: one
plugin, one settings screen (Settings -> Parcella Connector) holding
the shared base URL/token, with each capability living in its own file
under `includes/modules/` (`signup.php` today).

This consolidation applies only to the WordPress-calls-Parcella
direction. The blog channel (Parcella calls WordPress, using
WordPress's own built-in REST API) stays entirely separate and needs
no plugin at all -- see the blog-channel ADR entries above for why
folding it into this plugin would add a dependency for zero capability
gained.

**Upgrade path preserves existing configuration.** The WordPress
option names (`parcella_signup_base_url`, `parcella_signup_api_token`)
were deliberately kept unchanged from the old plugin, even though
everything else was renamed (`parcella_signup_*` function prefixes to
`parcella_connector_signup_*`, text domain, settings page slug). A club
that already configured the old plugin just deactivates it, installs
this one, and their base URL/token carry over with nothing to
re-enter. The `[parcella_work_signup]` shortcode tag is also unchanged,
so existing pages/posts using it keep working without edits.

