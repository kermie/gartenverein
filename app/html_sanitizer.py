"""
Sanitisiert HTML aus eingehenden Ticket-E-Mails, damit es sicher im
Browser gerendert werden kann.

WARUM DAS WICHTIG IST: Der Inhalt kommt von einem beliebigen externen
Absender an die Ticket-Postfach-Adresse -- jeder kann dorthin eine E-Mail
schicken. Das ist ein klassischer Fall für gespeichertes XSS, wenn der
HTML-Inhalt ungefiltert gerendert würde (z.B. <script>, <img onerror=...>,
javascript:-Links, verstecktes Tracking). Nichts aus dieser Quelle wird
jemals ungefiltert mit "|safe" ausgegeben.

Zwei Sicherheitsebenen:
1. Beim Einlesen der E-Mail (app/ticket_mailer.py) wird HIER bereits
   bereinigt, bevor irgendetwas in der Datenbank landet.
2. Der Jinja-Filter `sanitize_html` (siehe app/templating.py) bereinigt
   zusätzlich beim Rendern erneut -- günstig und harmlos bei bereits
   sauberem HTML, aber ein zweites Sicherheitsnetz, falls durch einen
   zukünftigen Code-Pfad ungeprüfter Inhalt in ein Template gelangen
   sollte.
"""
import re

import bleach

# <script>/<style> müssen VOLLSTÄNDIG entfernt werden (Tag UND Inhalt) --
# bleach.clean() entfernt bei nicht erlaubten Tags nur die Tags selbst und
# behält den Text dazwischen (richtig für z.B. ein gestripptes <div>, aber
# falsch für <script>/<style>, deren Inhalt kein für Menschen lesbarer
# Text ist). Deshalb hier vorab per Regex komplett entfernen.
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)

# Bewusst KEINE Bilder erlaubt: verhindert sowohl Tracking-Pixel (Absender
# erfährt sonst, wann/ob die Nachricht geöffnet wurde) als auch den
# klassischen <img onerror=...>-Trick als zusätzliche Angriffsfläche.
# Bewusst KEIN class/style-Attribut erlaubt: verhindert CSS-basierte
# Tricks (z.B. unsichtbarer Text, nachgeahmte UI-Elemente) und macht die
# Darstellung konsistent mit dem Rest der Seite.
ALLOWED_TAGS = [
    "p", "br", "b", "i", "u", "strong", "em", "a",
    "ul", "ol", "li", "blockquote", "span", "div",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "td", "th",
    "hr", "pre", "code",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_email_html(html: str) -> str:
    """Bereinigt HTML aus einer eingehenden Ticket-E-Mail für sicheres
    Rendern. Leerer/None-Input ergibt leeren String."""
    if not html:
        return ""

    html = _SCRIPT_STYLE_RE.sub("", html)

    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )

    # Externe Links in neuem Tab öffnen, ohne dass das Ziel über
    # window.opener auf die Ticketübersicht zugreifen kann -- der Inhalt
    # stammt von einem nicht vertrauenswürdigen Absender.
    cleaned = re.sub(
        r'<a\s+href="([^"]*)"([^>]*)>',
        r'<a href="\1" target="_blank" rel="noopener noreferrer"\2>',
        cleaned,
    )
    return cleaned
