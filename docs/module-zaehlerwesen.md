# Modul: Zählerwesen (Wasser & Strom)

Verwaltet Wasser- und Stromzähler über **eine gemeinsame Codebasis** –
das prägnanteste Beispiel im Projekt dafür, wie strukturell ähnliche
Anforderungen generalisiert statt dupliziert werden.

Modul-Flags: `wasser` und `strom` (unabhängig voneinander abschaltbar)

## Datenmodell

```
zaehlpunkte  – Ein Zählpunkt: Hauptzähler, Parzelle, oder Vereinsanschluss.
               Hat ein "medium" (WASSER/STROM) und einen "typ".
zaehler      – Der physische Zähler an einem Zaehlpunkt (Nummer, Eichfrist,
               Ein-/Ausbaudatum, Anfangsstand)
zaehlerstaende – Jährliche Ablesungen eines Zählers
```

Eine Parzelle kann sowohl einen Wasser- als auch einen Strom-Zaehlpunkt
haben – zwei Zeilen in derselben Tabelle, unterschieden über `medium`.

## Wichtige Entscheidung: Router-Factory statt Duplikation

Wasser und Strom sind strukturell identisch: Hauptzähler + Verteilzähler,
jährliche Ablesung, Verbrauchsberechnung, Plausibilitätsprüfung. Der
einzige Unterschied ist Einheit (m³ vs. kWh), Nachkommastellen (1 vs. 0)
und Anzeigetexte.

Statt zwei separate Router-Dateien zu pflegen, gibt es **eine**
Fabrikfunktion `erstelle_zaehler_router()` in `app/routers/zaehlerwesen.py`,
die einen vollständig konfigurierten Router für **ein** Medium erzeugt.
`main.py` instanziiert sie zweimal:

```python
wasser_router = erstelle_zaehler_router(
    medium=ZaehlerMedium.WASSER, url_prefix="/wasser", modul_name="wasser",
    medium_label="Wasser", einheit="m³", icon="bi-droplet", dezimalstellen=1,
)
strom_router = erstelle_zaehler_router(
    medium=ZaehlerMedium.STROM, url_prefix="/strom", modul_name="strom",
    medium_label="Strom", einheit="kWh", icon="bi-lightning-charge", dezimalstellen=0,
)
```

Ein Bugfix oder eine neue Funktion muss dadurch nur **einmal** geschrieben
werden. Die Templates (`app/templates/zaehlerwesen/`) sind ebenfalls
gemeinsam genutzt – sie erhalten `einheit`, `medium_label`, `icon` etc. als
Variablen statt die Werte hart zu kodieren.

Falls künftig ein drittes Medium dazukommt (Gas?), reicht ein weiterer
Aufruf von `erstelle_zaehler_router()` mit passender Konfiguration.

## Plausibilitätsprüfungen

**Monotonie pro Zähler** (hart, blockierend): Ein neuer Zählerstand darf
nicht kleiner sein als der vorherige Stand *derselben* Nummer – sowohl
rückwärts (nicht kleiner als der Vorwert) als auch vorwärts (nicht größer
als ein bereits erfasster späterer Wert, falls vorhanden). Siehe
`pruefe_monotonie()` in `app/zaehler_utils.py`.

**Gesamt-Plausibilität** (Warnung, nicht blockierend): Die Summe aus
Parzellen- und Vereinsverbrauch darf den Hauptzähler-Verbrauch nicht
übersteigen. Wird als Warnbanner angezeigt, nicht als Fehler – weil
Ablesungen zeitversetzt eingetragen werden und ein zwischenzeitlich
"unvollständiger" Datenstand kein Fehler ist, sondern normal.

## Zähler-Tausch und Historie

Wird ein Zähler getauscht (z.B. alle 6 Jahre bei Wasser, Eichfrist), wird
der alte **nicht gelöscht**, sondern deaktiviert (`ist_aktiv = false`,
`ausgebaut_am` gesetzt). Der neue Zähler bekommt eine eigene Zeile mit
neuer Nummer und eigenem Anfangsstand. Der Verbrauch wird dadurch korrekt
getrennt berechnet – kein Vermischen von altem und neuem Zählerstand.

## Bekannte Fallstricke

- **Jinja2 kann kein Python-`.format()`**: `"%.{}f"|format(stellen)|format(wert)`
  funktioniert nicht (Jinjas `format`-Filter nutzt den alten `%`-Operator).
  Lösung: ein eigener Jinja-Filter `fmt`, registriert direkt am
  `Jinja2Templates`-Objekt in `zaehlerwesen.py`:
  ```python
  templates.env.filters["fmt"] = lambda wert, stellen: f"{float(wert):.{stellen}f}"
  ```
- **MissingGreenlet beim Neuanlegen**: Wird eine Datenbankzeile per
  `db.add()` + `commit()` neu angelegt (statt per Query geladen), sind
  ihre Beziehungen (`relationship`-Felder) nicht eager geladen. Ein
  späterer Zugriff darauf löst einen synchronen Lazy-Load aus, der mit dem
  asynchronen Datenbanktreiber zu `MissingGreenlet` führt. Lösung: nach dem
  Anlegen die Zeile explizit mit `selectinload(...)` neu laden (siehe
  `_get_or_create_pv()` im Versicherungsmodul für ein Beispiel dieses
  Musters).
