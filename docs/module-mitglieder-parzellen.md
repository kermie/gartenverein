# Modul: Mitglieder & Parzellen (Core)

Das Kernmodul – immer aktiv, kann nicht abgeschaltet werden (im Gegensatz
zu den optionalen Modulen wie Pflichtstunden oder Wasser/Strom).

## Datenmodell

```
mitglieder            – Vereinsmitglieder (Stammdaten)
mitglied_telefon       – n Telefonnummern pro Mitglied
mitglied_email         – n E-Mail-Adressen pro Mitglied
parzellen              – Gartenparzellen
mitglied_parzelle       – m:n Zuordnung Mitglied ↔ Parzelle
aenderungshistorie      – generisches Audit-Log (siehe unten)
```

## Wichtige Entscheidungen

**m:n-Zuordnung von Anfang an.** Ein Mitglied kann mehrere Parzellen haben
(Doppelgärten), eine Parzelle kann mehrere Mitglieder haben (Ehepaare,
Familien). Die Zuordnungstabelle `mitglied_parzelle` trägt zusätzlich
`ist_hauptpaechter` (bool) und `zuordnung_von`/`zuordnung_bis` (Datumsfelder).

**Pächter-Historie statt Löschen.** Wird ein Pachtverhältnis beendet, wird
`zuordnung_bis` gesetzt statt die Zeile zu löschen. So bleibt nachvollziehbar,
wer wann welche Parzelle hatte – wichtig für Rückfragen Jahre später.
Nimmt ein Mitglied dieselbe Parzelle später erneut, wird die bestehende
(beendete) Zuordnung reaktiviert statt eine zweite Zeile anzulegen (es gibt
eine `UniqueConstraint` auf `mitglied_id, parzelle_id`).

**Aktive vs. inaktive Mitglieder.** Ein Mitglied gilt als aktiv, wenn
`deleted_at IS NULL` und (`mitglied_bis IS NULL` oder `mitglied_bis` in der
Zukunft liegt). Die zentrale Helper-Funktion `aktives_mitglied_filter()` in
`app/database.py` kapselt das – wird überall verwendet, wo nur aktive
Mitglieder relevant sind (Dropdowns, Auswertungen, Zuordnungen). Die
Mitgliederliste selbst zeigt standardmäßig nur Aktive, mit einer Checkbox
"Inaktive anzeigen" für die Historie (z.B. verstorbene Mitglieder).

**Änderungshistorie (Aenderungshistorie).** Ein generisches Audit-Log
(`app/aenderungstracker.py`), das Feldänderungen an beliebigen Entitäten
protokolliert (aktuell für Parzellen genutzt: Fläche, Status, Gartennummer
etc.). Statt für jede Tabelle eine eigene Historie-Tabelle zu bauen, gibt
es eine gemeinsame `aenderungshistorie`-Tabelle mit `entitaet_typ`,
`entitaet_id`, `feldname`, `alter_wert`, `neuer_wert`. Verwendung:

```python
tracker = AenderungsTracker(parzelle, "Parzelle", ["gartennummer", "flaeche_qm", "status"])
# ... Felder ändern ...
await tracker.commit(db, benutzer.id)
```

**CSV-Import mit automatischer Trennzeichen-Erkennung.** Frühe Version
erwartete hart Semikolon als Trennzeichen – das brach, sobald jemand die
Export-Datei in Excel öffnete und neu speicherte (Excel wechselt je nach
Spracheinstellung zu Komma). Jetzt wird `csv.Sniffer()` genutzt, um das
Trennzeichen zu erkennen, mit Semikolon als Fallback.

## Bekannte Fallstricke

- `zeile.get("Spalte", "")` schützt NICHT vor `None`-Werten, wenn eine
  CSV-Zeile weniger Felder hat als die Kopfzeile (Python füllt dann mit
  `None`, der Default greift nur bei komplett fehlendem Schlüssel). Immer
  `(zeile.get("Spalte") or "")` verwenden.
- `scalar_one_or_none()` wirft einen Fehler, sobald mehr als eine Zeile
  zurückkommt – für Duplikat-*Erkennung* (wo mehrere Treffer erwartet
  werden können) ist `.scalars().first()` die richtige Wahl.
