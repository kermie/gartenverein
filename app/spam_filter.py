"""
Spam-Filter für das Ticketsystem (Etappe 3).

Zwei Ebenen, kombiniert:
1. Eingebaute Heuristiken (Domain-/Schlüsselwort-Sperrliste, Link-Anzahl) –
   funktionieren sofort, ohne externen Dienst, konfigurierbar unter
   /admin/einstellungen.
2. Optionale externe API (z.B. Akismet, ein selbst gehosteter Filter) –
   nur aktiv, wenn eine URL konfiguriert ist. Schlägt der externe Aufruf
   fehl, wird stillschweigend auf die Heuristiken zurückgefallen; ein
   Ausfall des externen Diensts darf niemals die Ticketerstellung blockieren.

Der finale Score ist das Maximum aus Heuristik- und externem Score.
Ist der Score >= Schwellenwert, gilt die Nachricht als Spam-Verdacht.
"""
import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Vereinseinstellung
from app.crypto_utils import entschluesseln

logger = logging.getLogger(__name__)

_STANDARD_SCHWELLENWERT = 0.5


@dataclass
class SpamPruefungsErgebnis:
    ist_spam_verdacht: bool
    score: Optional[float] = None
    begruendung: Optional[str] = None


def _liste_aus_kommagetrennt(wert: Optional[str]) -> List[str]:
    if not wert:
        return []
    return [teil.strip().lower() for teil in wert.split(",") if teil.strip()]


async def _lade_konfiguration(db: AsyncSession) -> dict:
    schluessel_liste = [
        "spam_domain_blocklist", "spam_keyword_blocklist", "spam_schwellenwert",
        "spam_api_url", "spam_api_key",
    ]
    result = await db.execute(
        select(Vereinseinstellung).where(Vereinseinstellung.schluessel.in_(schluessel_liste))
    )
    gespeichert = {e.schluessel: e.wert for e in result.scalars().all() if e.wert}

    try:
        schwellenwert = float(gespeichert.get("spam_schwellenwert", _STANDARD_SCHWELLENWERT))
    except ValueError:
        schwellenwert = _STANDARD_SCHWELLENWERT

    return {
        "domain_blocklist": _liste_aus_kommagetrennt(gespeichert.get("spam_domain_blocklist")),
        "keyword_blocklist": _liste_aus_kommagetrennt(gespeichert.get("spam_keyword_blocklist")),
        "schwellenwert": schwellenwert,
        "api_url": gespeichert.get("spam_api_url", ""),
        "api_key": entschluesseln(gespeichert.get("spam_api_key")) or "",
    }


def _heuristik_score(
    absender_email: str, betreff: str, inhalt: str,
    domain_blocklist: List[str], keyword_blocklist: List[str],
) -> Tuple[float, List[str]]:
    """Berechnet einen Score 0.0–1.0 aus einfachen, nachvollziehbaren Regeln."""
    score = 0.0
    gruende: List[str] = []

    absender_domain = absender_email.rsplit("@", 1)[-1].lower() if "@" in absender_email else ""
    if absender_domain and any(domain == absender_domain for domain in domain_blocklist):
        score += 0.6
        gruende.append(f"Absender-Domain '{absender_domain}' auf Sperrliste")

    text_gesamt = f"{betreff} {inhalt}".lower()
    gefundene_keywords = [kw for kw in keyword_blocklist if kw in text_gesamt]
    if gefundene_keywords:
        score += min(0.5, 0.2 * len(gefundene_keywords))
        gruende.append(f"Schlüsselwörter gefunden: {', '.join(gefundene_keywords[:5])}")

    anzahl_links = len(re.findall(r"https?://", inhalt or "", flags=re.IGNORECASE))
    if anzahl_links > 3:
        score += 0.2
        gruende.append(f"{anzahl_links} Links im Text (auffällig viele)")

    return min(score, 1.0), gruende


async def _externe_pruefung(
    konfig: dict, absender_email: str, betreff: str, inhalt: str
) -> Optional[float]:
    """
    Ruft einen optionalen externen Spam-Prüfdienst auf. Erwartet eine JSON-
    Antwort der Form {"spam_score": 0.0-1.0} – so kann jeder Dienst
    angebunden werden, der diesen einfachen Vertrag über einen kleinen
    Adapter (z.B. eine kleine Cloud-Function) erfüllt. Gibt None zurück,
    wenn keine externe API konfiguriert ist oder der Aufruf fehlschlägt.
    """
    if not konfig["api_url"]:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"Authorization": f"Bearer {konfig['api_key']}"} if konfig["api_key"] else {}
            response = await client.post(
                konfig["api_url"],
                json={"absender_email": absender_email, "betreff": betreff, "inhalt": inhalt},
                headers=headers,
            )
            response.raise_for_status()
            daten = response.json()
            score = float(daten.get("spam_score", 0.0))
            return max(0.0, min(score, 1.0))
    except Exception as e:
        logger.warning(f"Externe Spam-Pruefung fehlgeschlagen, nutze nur Heuristiken: {e}")
        return None


async def pruefe_auf_spam(
    absender_email: str, betreff: str, inhalt: str, db: AsyncSession
) -> SpamPruefungsErgebnis:
    """
    Prüft eine eingehende Nachricht auf Spam-Verdacht. Kombiniert
    eingebaute Heuristiken mit einer optionalen externen API (Maximum
    beider Scores). Ein Ausfall der externen API blockiert die Prüfung nie.
    """
    konfig = await _lade_konfiguration(db)

    heuristik_score, gruende = _heuristik_score(
        absender_email, betreff, inhalt,
        konfig["domain_blocklist"], konfig["keyword_blocklist"],
    )

    externer_score = await _externe_pruefung(konfig, absender_email, betreff, inhalt)
    if externer_score is not None and externer_score > heuristik_score:
        finaler_score = externer_score
        gruende.append(f"Externe Pruefung: Score {externer_score:.2f}")
    else:
        finaler_score = heuristik_score

    ist_verdacht = finaler_score >= konfig["schwellenwert"]

    return SpamPruefungsErgebnis(
        ist_spam_verdacht=ist_verdacht,
        score=round(finaler_score, 2),
        begruendung="; ".join(gruende) if gruende else None,
    )
