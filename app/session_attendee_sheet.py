"""
Renders a single work session's attendee sheet: registered
participants with their parcel, expected hours, any task assigned to
them for this session, and a blank signature line -- for printing and
bringing to the actual work session, so the coordinator can confirm
attendance and hours on paper.

Like the meeting sign-in sheet (app/meeting_signin_sheet.py) and
unlike the announcement flyer (app/print_publisher.py), this is a
normal multi-page document (a big session could have more attendees
than fit on one page), not constrained to a single page.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from weasyprint import HTML

from app.pdf_utils import file_to_data_uri

PAGE_CSS = """
@page {
    size: A4;
    margin: 2.2cm 1.5cm 2.2cm 1.5cm;
    @top-center { content: element(header); }
    @bottom-left { content: element(footer); }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt; color: #6b7280;
    }
}
body { font-family: 'DejaVu Sans', sans-serif; color: #1f2937; font-size: 10pt; }
#header { position: running(header); text-align: center; border-bottom: 2px solid #2f6f3e; padding-bottom: 8px; }
#header img { max-height: 50px; margin-bottom: 4px; }
#header .club-name { font-size: 13pt; font-weight: bold; color: #2f6f3e; }
#footer { position: running(footer); font-size: 8pt; color: #6b7280; border-top: 1px solid #d1d5db; padding-top: 6px; }
h1 { font-size: 15pt; margin-top: 0.4cm; margin-bottom: 0.1cm; color: #1f2937; }
.subtitle { font-size: 10pt; color: #4b5563; margin-bottom: 0.5cm; }
table { width: 100%; border-collapse: collapse; }
thead { display: table-header-group; } /* repeats on every page */
th { text-align: left; font-size: 8.5pt; text-transform: uppercase; color: #4b5563; border-bottom: 2px solid #2f6f3e; padding: 6px 6px; }
td { padding: 7px 6px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
td.parcel-col { font-weight: bold; white-space: nowrap; width: 2.4cm; }
td.member-col { width: 4.2cm; }
td.hours-col { width: 2cm; white-space: nowrap; }
td.tasks-col { width: 5cm; }
td.signature-col { border-bottom: 1px solid #9ca3af; }
"""


@dataclass
class AttendeeRow:
    parcel: str
    member_name: str
    hours: str
    tasks: str


def _build_html(headline: str, subtitle: str, club_name: str, logo_data_uri: Optional[str], rows: List[AttendeeRow]) -> str:
    logo_block = f'<img src="{logo_data_uri}">' if logo_data_uri else ""

    rows_html = "".join(
        f'<tr><td class="parcel-col">{r.parcel}</td>'
        f'<td class="member-col">{r.member_name}</td>'
        f'<td class="hours-col">{r.hours}</td>'
        f'<td class="tasks-col">{r.tasks}</td>'
        f'<td class="signature-col"></td></tr>'
        for r in rows
    )

    return f"""
    <html>
    <head><meta charset="utf-8"><style>{PAGE_CSS}</style></head>
    <body>
        <div id="header">
            {logo_block}
            <div class="club-name">{club_name}</div>
        </div>
        <div id="footer">{club_name}</div>
        <h1>{headline}</h1>
        <div class="subtitle">{subtitle}</div>
        <table>
            <thead>
                <tr>
                    <th>Parcel</th>
                    <th>Member</th>
                    <th>Hours</th>
                    <th>Tasks assigned</th>
                    <th>Signature</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """


def render_session_attendee_sheet_pdf(
    headline: str, subtitle: str, club_name: str, logo_path: Optional[Path],
    rows: List[AttendeeRow],
) -> bytes:
    """rows should already be sorted the way the caller wants them to
    appear -- this function doesn't re-sort."""
    logo_data_uri = file_to_data_uri(logo_path, "image/png")
    html_doc = _build_html(headline, subtitle, club_name, logo_data_uri, rows)
    return HTML(string=html_doc).write_pdf()
