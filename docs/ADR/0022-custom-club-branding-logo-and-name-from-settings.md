# Custom club branding: logo and name from settings

**Context:** the software is meant for adoption by any allotment-garden
association, not just the one it was originally built for -- a
hardcoded "Gartenverein" name and a fixed tree icon in the sidebar
doesn't fit that goal.

**Decision:** two things, loaded once per request via a new middleware
(`app/branding.py`), following the exact same pattern already
established for language, module flags, and region/currency
(`request.state.club_name` / `request.state.logo_url`, available on
every page without any router needing to fetch them individually):
- The club's display name reuses the existing `verein_name` ClubSetting
  (already used for the address block) rather than introducing a
  second, redundant name field.
- A new `logo_filename` ClubSetting, paired with an actual uploaded
  image file under `app/static/uploads/logo.<ext>` -- validated
  (allowed image types, 2MB limit) and always saved under a fixed name
  so re-uploading a different file type cleanly replaces the old one
  rather than leaving it orphaned but still reachable.

Falls back to "Gartenverein" and the default tree icon when nothing's
configured, so a fresh install doesn't look broken before an admin sets
things up.

