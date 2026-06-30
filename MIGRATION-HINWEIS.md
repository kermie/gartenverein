# Migration auf Alembic – Hinweis für bestehende Installationen

Du hast bereits eine laufende Datenbank mit Testdaten (erstellt über das alte
`Base.metadata.create_all()`). Ab dieser Version übernimmt **Alembic** die
Schemaverwaltung. Damit deine Daten erhalten bleiben, brauchst du **einen
einmaligen manuellen Schritt**, bevor der Container neu gebaut wird.

## Einmaliger Schritt (nur beim Umstieg)

1. Neue Dateien einspielen (siehe unten), aber **noch nicht** `docker compose up` mit dem neuen Entrypoint laufen lassen.

2. Container wie gewohnt mit dem ALTEN Setup hochfahren (damit die DB läuft):
   ```bash
   docker compose up -d db
   ```

3. Alembic im `web`-Container (oder lokal mit gleicher DATABASE_URL) initial "stempeln" – das markiert die Migration `0001_initial` als bereits angewendet, OHNE die Tabellen neu zu erstellen:
   ```bash
   docker compose run --rm web alembic stamp head
   ```

4. Danach normal starten:
   ```bash
   docker compose up -d
   ```

Ab jetzt prüft der Container bei jedem Start automatisch, ob neue Migrationen
anstehen (`alembic upgrade head` läuft im `docker-entrypoint.sh`), und führt
nur das aus, was seit `0001_initial` neu hinzugekommen ist.

## Bei einer komplett neuen / leeren Installation

Kein manueller Schritt nötig – `alembic upgrade head` erstellt beim ersten
Start automatisch alle Tabellen aus der `0001_initial`-Migration.

## Neue Migration erstellen (zukünftig, bei Modelländerungen)

```bash
docker compose run --rm web alembic revision --autogenerate -m "Kurze Beschreibung"
```

Alembic vergleicht dann automatisch `app/models.py` mit dem aktuellen
DB-Stand und schlägt die nötigen `CREATE`/`ALTER`-Statements vor. Die
generierte Datei in `migrations/versions/` IMMER vor dem Anwenden prüfen.
