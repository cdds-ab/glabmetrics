# GitLab Statistics Analyzer - Neue Caching-Funktionalität

## 🚀 Drastisch verbesserte Performance!

Das Tool wurde um eine **JSON-basierte Zwischenspeicherung** erweitert. Die erste Analyse dauert wie gewohnt lange, aber nachfolgende Report-Generierungen sind **blitzschnell**.

## 📋 Neue Verwendung:

### Erste Datensammlung (einmalig langsam):
```bash
# Sammelt Daten von GitLab API und speichert sie in gitlab_data.json
pdm run gitlab-stats https://gitlab.example.com token123 --refresh-data
```

### Schnelle Report-Generierung (aus Cache):
```bash
# Verwendet gecachte Daten - dauert nur Sekunden!
pdm run gitlab-stats https://gitlab.example.com token123

# Alternativer Output-Name
pdm run gitlab-stats https://gitlab.example.com token123 --output weekly_report.html
```

### Daten aktualisieren:
```bash
# Holt frische Daten von GitLab (z.B. wöchentlich)
pdm run gitlab-stats https://gitlab.example.com token123 --refresh-data
```

### Eigene Cache-Datei:
```bash
# Verschiedene Cache-Dateien für verschiedene Zwecke
pdm run gitlab-stats https://gitlab.example.com token123 --data-file monthly_data.json --refresh-data
pdm run gitlab-stats https://gitlab.example.com token123 --data-file monthly_data.json --output monthly_report.html
```

## ⚡ Performance-Verbesserung:

- **Erste Sammlung**: 5-10 Minuten (wie vorher)
- **Report aus Cache**: 5-10 Sekunden! 🚀
- **Cache-Datei**: ~1-5MB (je nach Anzahl Repositories)

## 🔄 Empfohlener Workflow:

1. **Einmalig**: `--refresh-data` für initiale Datensammlung
2. **Täglich**: Schnelle Reports aus Cache für verschiedene Zwecke
3. **Wöchentlich**: `--refresh-data` für aktuelle Daten
4. **Bei Bedarf**: Verschiedene Cache-Dateien für verschiedene Analysen

## 💡 Zusätzliche Features:

- **Altersanzeige**: Das Tool zeigt das Alter der gecachten Daten an
- **Automatische Warnung**: Bei veralteten Daten wird zur Aktualisierung geraten
- **Fehlerbehandlung**: Klare Meldungen bei fehlenden Cache-Dateien

## 🎯 Ideal für Consultants:

- **Kundenmeeting**: Schnell aktuellen Report generieren
- **Verschiedene Formate**: Mehrere Reports aus denselben Daten
- **Archivierung**: Cache-Dateien für historische Vergleiche aufbewahren