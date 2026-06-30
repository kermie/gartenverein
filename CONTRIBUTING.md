# Mitwirken an der Gartenverein-Verwaltung

Danke für dein Interesse an diesem Projekt! Es ist als Open-Source-Software
für Kleingärtnervereine gedacht – generisch genug, um über den
ursprünglichen Verein hinaus nützlich zu sein.

## Lizenz und was das für dich bedeutet

Dieses Projekt steht unter der **GNU Affero General Public License v3.0
(AGPL-3.0)**. Kurz zusammengefasst:

- Du darfst den Code frei nutzen, verändern und weiterverbreiten.
- Wenn du eine modifizierte Version **als Netzwerkdienst** (z.B. SaaS für
  andere Vereine) betreibst, musst du den Quellcode deiner Version
  öffentlich zugänglich machen – auch ohne klassische Weitergabe.
- Abgeleitete Werke müssen ebenfalls unter AGPL-3.0 stehen (Copyleft).

Mit deinem Beitrag (Pull Request) erklärst du dich einverstanden, dass
dein Code unter denselben Bedingungen (AGPL-3.0) lizenziert wird.

## Wie du mitwirken kannst

1. **Issues**: Fehler gefunden oder eine Idee? Lege ein Issue an, bevor du
   größere Änderungen beginnst – so vermeiden wir doppelte Arbeit.
2. **Fork & Branch**: Erstelle einen Fork, arbeite in einem
   Feature-Branch (`git checkout -b feature/meine-aenderung`).
3. **Pull Request**: Beschreibe kurz, was sich ändert und warum.

## Entwicklungsumgebung

```bash
git clone <dein-fork-url>
cd gartenverein
cp .env.example .env
docker compose build web
docker compose run --rm --entrypoint alembic web upgrade head
docker compose up -d
```

App läuft dann unter http://localhost:8000, API-Doku unter
http://localhost:8000/api/docs.

## Code-Konventionen

- **Sprache**: Variablennamen, Funktionsnamen und UI-Texte sind auf
  Deutsch (Domänensprache des Projekts: Mitglied, Parzelle, Verein...).
  Code-Kommentare ebenfalls Deutsch.
- **Generizität**: Neue Felder/Funktionen sollten, wo sinnvoll, nicht nur
  für den Ursprungsverein passen, sondern für Kleingärtnervereine
  allgemein (z.B. konfigurierbare Flächentypen statt hartcodierter
  A/B/C-Logik, falls andere Vereine andere Kategorien brauchen).
- **Migrationen**: Jede Modelländerung in `app/models.py` braucht eine
  begleitende Alembic-Migration:
  ```bash
  docker compose run --rm web alembic revision --autogenerate -m "Kurzbeschreibung"
  ```
  Migration immer manuell prüfen, bevor sie committet wird – Autogenerate
  übersieht gelegentlich Dinge (z.B. Umbenennungen werden als
  Drop+Create erkannt).
- **API-Schemas**: Neue/geänderte Modelle sollten passende
  Pydantic-Schemas in `app/schemas.py` bekommen, damit sie über die
  REST-API verfügbar sind.

## Was uns besonders hilft

- Tests (aktuell noch nicht vorhanden – ein guter erster Beitrag!)
- Übersetzung der UI ins Englische (i18n-Grundgerüst existiert noch nicht)
- Dokumentation für weitere Deployment-Szenarien
- Barrierefreiheit (a11y) der Templates

Bei Fragen: Issue aufmachen, wir schauen drauf.
