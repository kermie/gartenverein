#!/bin/bash
set -e

echo "Warte auf Datenbank..."
until python -c "
import asyncio
import asyncpg
import os
import sys
from urllib.parse import urlparse

url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')

async def check():
    try:
        conn = await asyncpg.connect(url)
        await conn.close()
        return True
    except Exception:
        return False

sys.exit(0 if asyncio.run(check()) else 1)
"; do
  sleep 1
done
echo "Datenbank erreichbar."

echo "Führe Datenbankmigrationen aus..."
# Hinweis: Bei einer bereits existierenden Datenbank (vor Alembic-Einführung)
# muss EINMALIG manuell "alembic stamp head" statt "upgrade head" laufen,
# siehe MIGRATION-HINWEIS.md
alembic upgrade head

echo "Starte Anwendung..."
exec "$@"
