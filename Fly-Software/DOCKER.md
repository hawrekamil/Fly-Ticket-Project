# Docker Anleitung für BookingSoft (Fly-Software)

Dieses Projekt ist vollständig containerisiert und kann mit Docker & Docker Compose ausgeführt werden.

---

## 🚀 Schnellstart

Navigiere in das `Fly-Software` Verzeichnis:

```bash
cd "Fly-Software"
```

### 1. Container im Hintergrund starten
```bash
docker compose up -d
```

### 2. Container stoppen
```bash
docker compose down
```

### 3. Container neu bauen (z. B. nach Code-Änderungen)
```bash
docker compose up -d --build
```

---

## 🌐 Verfügbare Adressen

| Dienst | URL | Beschreibung |
|---|---|---|
| **Frontend Web App** | [http://localhost:5173](http://localhost:5173) | Modernes React + Vite + Tailwind UI |
| **Backend REST API** | [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/) | Django REST Framework API |
| **API Dokumentation (Swagger)** | [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) | Interaktive OpenAPI / Swagger-UI |
| **Django Admin** | [http://localhost:8000/admin/](http://localhost:8000/admin/) | Django Administrationsbereich |

*Hinweis: Der Frontend-Container nutzt einen integrierten Nginx Reverse Proxy. API-Aufrufe (`/api/`, `/admin/`, `/static/`) werden automatisch an das Backend weitergeleitet.*

---

## 🛠️ Nützliche Docker-Befehle

### Status der Container anzeigen
```bash
docker compose ps
```

### Live-Logs einsehen
```bash
# Alle Logs
docker compose logs -f

# Nur Backend-Logs
docker compose logs -f backend

# Nur Frontend-Logs
docker compose logs -f frontend

# Nur Background-Worker-Logs
docker compose logs -f worker
```

### Django Superuser (Admin) erstellen
```bash
docker compose exec backend python manage.py createsuperuser
```

### Django Shell öffnen
```bash
docker compose exec backend python manage.py shell
```

### Datenbank & Persistenz
Die SQLite-Datenbank (`db.sqlite3`) sowie Medien-Uploads sind als Host-Volumes angebunden (`./backend/db.sqlite3` und `./backend/media`). Alle Daten, Flug-Caches und Benutzer bleiben auch bei Neustart oder Neuerstellung der Container dauerhaft erhalten.
