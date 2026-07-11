# Automatisierte Tests

## Philosophie

**Kein Anspruch auf 100% Testabdeckung.** Das wäre für ein Projekt dieser
Größe ein eigenes Fass ohne Boden. Stattdessen:

1. **Ein "Happy Path"-Test pro Modul** – die grundlegende Funktionalität
   funktioniert (anlegen, abrufen, verknüpfen).
2. **Gezielte Tests für die Stellen mit dem höchsten Regressionsrisiko** –
   also genau die Logik, die schon mal Kopfzerbrechen bereitet hat oder
   bei der ein stiller Fehler besonders schlimm wäre:
   - Vier-Augen-Prinzip bei Einkaufswünschen (Selbstfreigabe-Sperre,
     Doppel-Freigabe-Sperre, Veto-Ablehnung)
   - Zählerstand-Monotonie-Prüfung (darf nicht sinken)
   - Pflichtstunden-Gruppenbefreiung (`any()` statt `all()` bei Parzellen)
   - Versicherungskosten-Berechnung (Grund- + Zusatzbeträge)

## Warum echtes PostgreSQL, nicht SQLite

Mehrere Bugs in diesem Projekt traten **ausschließlich mit PostgreSQL**
auf (z.B. die Enum-Großschreibungs-Problematik, siehe
[Architektur-Entscheidungen](./architektur-entscheidungen.md)). Ein
Testlauf gegen SQLite hätte solche Bugs unsichtbar gemacht, statt sie zu
fangen – SQLite ist in vielen Dingen (Typsystem, Enum-Handling,
Constraint-Durchsetzung) großzügiger als PostgreSQL. Tests laufen daher
gegen eine echte, aber komplett wegwerfbare PostgreSQL-Instanz.

## Ausführen

```bash
./run_tests.sh
```

Das Skript kapselt den kompletten Ablauf: startet eine isolierte
Test-Datenbank (`tmpfs`, verschwindet beim Stoppen), installiert
Test-Abhängigkeiten, führt `pytest` aus, räumt danach auf – auch wenn
Tests fehlschlagen.

Die Test-Datenbank läuft nur mit `docker compose --profile test`, taucht
also bei normalem `docker compose up` nicht auf und stört den laufenden
Betrieb nie.

## Automatisch bei jedem Push

`.github/workflows/tests.yml` führt dieselbe Test-Suite bei jedem Push
und Pull Request auf GitHub aus (eigene, isolierte PostgreSQL-Instanz als
GitHub-Actions-Service, kein Docker-Compose nötig auf CI-Seite). Ein
fehlgeschlagener Test ist dort direkt im Pull Request sichtbar, bevor
etwas nach `main` gemerged wird.

## Wie die Testdatenbank funktioniert

`tests/conftest.py` setzt `DATABASE_URL` auf die Testdatenbank, **bevor**
irgendein Teil der App importiert wird. Das ist wichtig: Python cached
Modul-Importe, und `app/database.py` erstellt die Datenbankverbindung
beim ersten Import aus `settings.database_url` – würde die App vorher
schon einmal mit der Produktions-URL importiert, würden auch interne
Mechanismen (die Modul-Flags-Middleware, die Admin-Anlegen-Logik beim
Start) die falsche Datenbank verwenden. Weil wir die Umgebungsvariable
ganz am Anfang von `conftest.py` setzen, funktioniert das automatisch
richtig, ohne dass wir jede einzelne Stelle im Code eigens überschreiben
müssten.

Vor jedem einzelnen Test werden alle Tabellen geleert (nicht: verschachtelte
Transaktionen mit Rollback). Das ist bewusst die einfachere Lösung: die
Anwendung committet an vielen Stellen selbst mittendrin (z.B. nach jeder
Freigabe eines Einkaufswunsches) – das würde mit reinen
Test-Transaktionen, die am Ende zurückgerollt werden, zu Konflikten
führen. Tabellen leeren ist weniger elegant, aber robust und leicht
nachvollziehbar.

## Bekannte Grenzen (bewusst nicht automatisiert getestet)

- **IMAP-Abruf und SMTP-Versand** (`app/ticket_mailer.py`,
  `app/email_service.py`): erfordern einen echten Mailserver. Diese Pfade
  werden weiterhin manuell getestet (siehe die frühere Diagnose-Sitzung
  mit dem direkten `imaplib`-Testskript). Ein Mocking dieser externen
  Systeme wäre möglich, wurde aber als nicht lohnenswert für den
  aktuellen Projektumfang eingeschätzt – die Fehleranfälligkeit liegt
  eher an echten Netzwerk-/Konfigurationsproblemen als an der eigenen
  Logik, die bereits getestet ist (Threading-Zuordnung, Ticket-Erzeugung).
- **Externe Spam-Prüf-API** (`app/spam_filter.py`, `_externe_pruefung()`):
  gleicher Grund – nur relevant, wenn ein Verein tatsächlich einen
  externen Dienst konfiguriert, was aktuell niemand tut.
- **E-Mail-Versand allgemein** (Einladungen, Zuweisungsbenachrichtigungen):
  `sende_email()` schlägt in der Testumgebung mangels SMTP-Konfiguration
  einfach fehl (gibt `False` zurück) – das ist beabsichtigtes, bereits
  vom Code abgefangenes Verhalten, kein Testfehler.

## Neues Modul? Neue Tests nicht vergessen

Beim Bau eines neuen Moduls (siehe auch die Checkliste in
[docs/README.md](./README.md)) gehört ab sofort auch eine
`tests/test_<modul>.py`-Datei mit mindestens einem Happy-Path-Test dazu –
genau wie Doku und API-Endpunkte inzwischen selbstverständlich sind.
