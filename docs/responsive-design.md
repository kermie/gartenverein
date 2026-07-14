# Responsive Design

The app is server-rendered Jinja2 + Bootstrap 5, no frontend framework.
Responsive behavior is plain CSS media queries and a small amount of
vanilla JS in `app/templates/base.html`, no build step involved.

## Off-canvas navigation (< 768px)

Below 768px, the sidebar (`.sidebar`) is translated fully off-screen
(`transform: translateX(-100%)`) instead of being always visible, and a
hamburger button (`.sidebar-toggle-btn`, hidden above 768px) appears in
the top bar to open it.

- Opening adds `.sidebar-open` (slides it in) and shows a semi-transparent
  backdrop (`#sidebar-backdrop`) behind it.
- Closing happens on: tapping the backdrop, pressing Escape, or clicking
  any navigation link inside the sidebar while narrower than 768px --
  nobody wants the menu still open after they've navigated somewhere.
- All of this is ~30 lines of vanilla JS at the bottom of `base.html`,
  no library.

If you add a new top-level nav item or nav-group, it inherits this
behavior automatically -- there's nothing per-link to wire up.

## Tables: `.table-responsive`

A `<table>` wider than the viewport needs to scroll *itself*
horizontally, not force the whole page to scroll sideways. Bootstrap's
`.table-responsive` wrapper does exactly that:

```html
<div class="table-responsive">
  <table class="table table-hover">
    ...
  </table>
</div>
```

**Every** template with a `<table>` needs this wrapper -- there is no
exception. This was audited across all 46 templates in one pass (16 of
19 tables were missing it at the time -- ticket lists, member lists,
annual evaluations, several with 5-8 columns that would otherwise break
the page layout or force page-level horizontal scroll on a phone). If
you add a table without this wrapper, it'll work fine on desktop and
silently break the mobile layout.

## Touch targets

Bootstrap's small-size variants (`btn-sm`, `form-control-sm`,
`form-select-sm`) are sized for mouse pointers and are too small to
reliably tap on a touchscreen. Below 768px, `base.html` bumps their
minimum height:

```css
.btn-sm { min-height: 2.25rem; padding-top: 0.4rem; padding-bottom: 0.4rem; }
.form-control-sm, .form-select-sm { min-height: 2.25rem; }
```

This is automatic for any element using those Bootstrap classes --
nothing to do per-template.

## Button groups that would otherwise clip

Bootstrap's `.btn-group` is `inline-flex` with no wrapping by default,
so a row of filter buttons (e.g. Tickets' "Active / Mine / Suspected /
Closed / All") would run off the edge of a narrow screen instead of
wrapping to a second line. Below 768px, `.btn-group` gets
`flex-wrap: wrap` and each button gets its border-radius back
individually (since Bootstrap normally only rounds the first/last
button in a group, which looks wrong once they wrap to multiple rows).
Again, automatic for anything using `.btn-group` -- no per-template
change needed.

## Breakpoints in use

| Breakpoint | What changes |
|---|---|
| `max-width: 768px` | Off-canvas sidebar, touch target sizing, `.btn-group` wrapping |
| `max-width: 480px` | Tighter page padding (`.page-body`, `.topbar`) for small phones |

## Testing responsiveness

No automated visual/screenshot tests -- this is checked manually with
browser dev tools' device emulation (e.g. "iPhone SE" ~375px, "iPad"
~768px) or on an actual phone:

1. **Navigation**: narrow the viewport -- a hamburger icon should appear
   top-left. Tapping it slides the sidebar in over a dimmed backdrop;
   tapping the backdrop or a nav link closes it again.
2. **Tables**: on any list/report page with several columns, only the
   *table* should scroll horizontally on a narrow screen, never the
   whole page.
3. **Filter button rows**: on pages like Tickets or Purchase Requests,
   the filter buttons should wrap to a second line on very narrow
   screens rather than getting cut off.

## What's still open

A closer per-page pass for remaining edge cases (very wide evaluation
tables with many columns, dense dashboard stat cards on very small
screens) was identified as follow-up work once the foundational layer
above had been used in practice for a while -- not yet revisited.
