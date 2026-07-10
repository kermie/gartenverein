"""
Hilfsfunktionen für das Versicherungsmodul: Kostenberechnung und
Haushalts-Erkennung (gleiche Adresse = automatisch mitversichert).
"""
from decimal import Decimal
from typing import List, Optional

from app.models import Mitglied, MitgliedParzelle, ParzelleVersicherung, VersicherungsKonfiguration


def _adresse_normalisiert(mitglied: Mitglied) -> tuple:
    """Normalisierte Adresse für den Haushaltsvergleich (whitespace/case-tolerant)."""
    return (
        (mitglied.strasse or "").strip().lower(),
        (mitglied.plz or "").strip().lower(),
        (mitglied.ort or "").strip().lower(),
    )


def hauptpaechter_von(zuordnungen: List[MitgliedParzelle]) -> Optional[Mitglied]:
    """Ermittelt den Hauptpächter einer Parzelle (oder den ersten Pächter als Fallback)."""
    aktuelle = [z for z in zuordnungen if z.zuordnung_bis is None]
    if not aktuelle:
        return None
    haupt = next((z for z in aktuelle if z.ist_hauptpaechter), aktuelle[0])
    return haupt.mitglied


def haushalts_gruppierung(zuordnungen: List[MitgliedParzelle]) -> dict:
    """
    Teilt die aktuellen Pächter einer Parzelle in "im Haushalt des
    Hauptpächters" (gleiche Adresse) und "außerhalb" auf.

    Rückgabe: {"haushalt": [Mitglied, ...], "extern": [Mitglied, ...]}
    Eine leere Adresse (alle Felder leer) zählt NICHT als Übereinstimmung,
    um Falsch-Zuordnungen bei fehlenden Adressdaten zu vermeiden.
    """
    aktuelle = [z for z in zuordnungen if z.zuordnung_bis is None]
    hauptpaechter = hauptpaechter_von(zuordnungen)

    if not hauptpaechter:
        return {"haushalt": [], "extern": []}

    haupt_adresse = _adresse_normalisiert(hauptpaechter)
    ist_leer = haupt_adresse == ("", "", "")

    haushalt = []
    extern = []

    for z in aktuelle:
        m = z.mitglied
        if m.id == hauptpaechter.id:
            haushalt.append(m)
            continue
        if not ist_leer and _adresse_normalisiert(m) == haupt_adresse:
            haushalt.append(m)
        else:
            extern.append(m)

    return {"haushalt": haushalt, "extern": extern}


def berechne_versicherungskosten(
    pv: ParzelleVersicherung, konfiguration: Optional[VersicherungsKonfiguration]
) -> dict:
    """
    Berechnet die Versicherungskosten einer Parzelle für ein Jahr.
    Gibt ein Dict mit sach_kosten, unfall_kosten, gesamt zurück.
    """
    sach_kosten = Decimal("0")
    if pv.hat_sachversicherung and pv.sach_paket:
        sach_kosten = Decimal(str(pv.sach_paket.betrag_eur))

    unfall_kosten = Decimal("0")
    if pv.hat_unfallversicherung and konfiguration:
        grund = Decimal(str(konfiguration.unfall_grundbetrag_eur))
        zusatz = Decimal(str(konfiguration.unfall_zusatzbetrag_eur))
        anzahl_zusatz = len(pv.zusatzpersonen)
        unfall_kosten = grund + (zusatz * anzahl_zusatz)

    return {
        "sach_kosten": sach_kosten,
        "unfall_kosten": unfall_kosten,
        "gesamt": sach_kosten + unfall_kosten,
    }
