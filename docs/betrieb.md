# Betrieb

Praktische Befehle und Fehlerbehebung für den laufenden Betrieb.

## Docker-Grundbefehle

```bash
# Container bauen (nötig nach Änderungen an requirements.txt oder Dockerfile)
docker compose build web

# Container starten
docker compose up -d

# Container neu starten (reicht bei reinen Python-Code-/Template-Änderungen,
# da uvicorn im --reload-Modus läuft)
docker compose restart web

# Logs ansehen
docker compose logs web --tail=30

# Status prüfen
docker compose ps
```

## Datenbankmigrationen

```bash
# Migrationen anwenden (läuft auch automatisch beim Containerstart)
docker compose run --rm --entrypoint alembic web upgrade head

# Neue Migration nach Modelländerung erzeugen
docker compose run --rm web alembic revision --autogenerate -m "Kurzbeschreibung"

# Aktuellen Stand prüfen
docker compose run --rm --entrypoint alembic web current

# Alle "Köpfe" prüfen (bei "Multiple head revisions"-Fehler)
docker compose run --rm --entrypoint alembic web heads
```

**Wichtig:** Revisionsnamen (`revision: str = "..."`) müssen unter 32
Zeichen bleiben – die `alembic_version`-Tabelle hat eine `VARCHAR(32)`-Spalte.

**Bei "Multiple head revisions"-Fehler:** Meist entstanden durch zwei
parallel erstellte Migrationen mit demselben `down_revision`. Lösung: eine
der beiden Migrationsdateien löschen, ggf. den `alembic_version`-Eintrag in
der DB direkt korrigieren:
```bash
docker compose exec db psql -U gartenverein -c "UPDATE alembic_version SET version_num = '<korrekte_revision>' WHERE version_num = '<falsche_revision>';"
```

## SMTP-Einrichtung

SMTP-Zugangsdaten können unter `/admin/einstellungen` eingetragen werden
(Datenbank hat Vorrang) oder per `.env`-Datei (Fallback, falls DB-Werte
fehlen):

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=...
SMTP_FROM=verein@example.com
SMTP_TLS=true
```

Das SMTP-Passwort wird in der Datenbank verschlüsselt gespeichert (siehe
[Architektur-Entscheidungen](./architektur-entscheidungen.md)). Ein
SMTP-Server kann bedenkenlos eingetragen werden, auch während die App noch
unter `localhost` läuft – der Versand ist eine ausgehende Verbindung vom
Container zum Mailserver, unabhängig davon, wie die App selbst erreichbar ist.

## Erster Login

Beim allerersten Start (leere `benutzer`-Tabelle) wird automatisch ein
Admin-Konto angelegt:

- E-Mail: `admin@gartenverein.local`
- Passwort: `admin1234`

Bitte sofort nach dem ersten Login ändern.

## Häufige Fehlerbilder

| Symptom | Wahrscheinliche Ursache |
|---|---|
| `invalid input value for enum` | Enum-Wert in Python ≠ Enum-Wert in DB (Groß-/Kleinschreibung) |
| `MultipleResultsFound` | `scalar_one_or_none()` bei einer Abfrage verwendet, die mehrere Treffer liefern kann |
| `MissingGreenlet` beim Start/Neustart | `scalar_one_or_none()` auf einer Tabelle mit mehreren Zeilen (z.B. Benutzer-Zähl-Check) |
| `MissingGreenlet` bei einzelner Seite | Lazy-Load auf frisch angelegtem Objekt ohne eager-geladene Beziehungen |
| CSV-Import: alle Zeilen "Fehler" | Trennzeichen-Mismatch (Excel speichert ggf. mit Komma statt Semikolon) |
| Docker: root-Dateien im Projektordner | Container lief als root; `UID`/`GID` in `.env` setzen (siehe `docker-compose.yml`) |
