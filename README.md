# Fly-Ticket-Project (BookingSoft) ✈️🌍

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20TailwindCSS-61DAFB?logo=react)](Fly-Software/frontend)
[![Django](https://img.shields.io/badge/Backend-Django%205%20%2B%20DRF-092E20?logo=django)](Fly-Software/backend)
[![Docker](https://img.shields.io/badge/Containers-Docker%20%26%20Docker%20Compose-2496ED?logo=docker)](Fly-Software/docker-compose.yml)
[![Duffel API](https://img.shields.io/badge/Integration-Duffel%20Flights%20API-FF4B4B)](https://duffel.com)
[![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF?logo=stripe)](https://stripe.com)

**Fly-Ticket-Project (BookingSoft)** ist eine moderne, skalierbare Flugbuchungs- und Reservierungsplattform. Sie kombiniert ein performantes **React SPA Frontend (Vite & TailwindCSS)** mit einem robusten **Django REST Framework (DRF) Backend**, vollständiger **Duffel API** Flug-Integration, **Stripe** Zahlungsabwicklung und asynchronen Hintergrund-Workern (**django-q2**).

---

## 📑 Inhaltsverzeichnis

- [Architektur & Features](#-architektur--features)
- [Projektstruktur](#-projektstruktur)
- [Schnellstart mit Docker (Empfohlen)](#-schnellstart-mit-docker-empfohlen)
- [Lokale Entwicklung ohne Docker](#-lokale-entwicklung-ohne-docker)
- [Dienste & Endpunkte](#-dienste--endpunkte)
- [Sicherheit & Umgebungsvariablen](#-sicherheit--umgebungsvariablen)
- [Dokumentation](#-dokumentation)

---

## 🚀 Architektur & Features

### 1. Frontend (React + Vite + TailwindCSS)
- **Moderne UI / UX**: Dynamisches Glassmorphism-Design mit Farbverläufen und responsiven Tailwind-Komponenten.
- **Echtzeit-Flughafen- & Städtesuche**: Autocomplete-Suche (`AirportAutocomplete.jsx`) mit direkter IATA-Code-Auflösung via Duffel Places API und lokalen Fallbacks.
- **Interaktive Filter**: Preisbereichs-Schieberegler, Fluggesellschaft-Filter, Tageszeit-Auswahl (Morgen, Nachmittag, Abend, Nacht), Zwischenstopps und Sortierung (Günstigste, Schnellste, Früheste).
- **Checkout & Zahlungen**: Integriertes Stripe Elements für sichere Kreditkartenzahlungen sowie ein flexibler **Cash-Hold-Workflow** (Barzahlung bei Buchungsagenten).
- **Kunden- & Agentenbereich**:
  - Kunden-Dashboard (`MyOrders.jsx`) zur Einsicht aller Buchungen und Zahlungsfristen.
  - Agenten-Dashboard (`AgentDashboard.jsx`) zur Verwaltung und Bestätigung ausstehender Barzahlungen.

### 2. Backend (Django REST Framework)
- **Duffel API Client**: Asynchroner HTTPX-Client (`duffel_client.py`) für Flugsuche, Angebotsabruf und Ticket-Erstellung.
- **Transaktionssicheres State-Machine-Modell**: Strenge Auftragsstatus-Übergänge (`PENDING_PAYMENT`, `HOLD_PENDING_CASH`, `CONFIRMED`, `EXPIRED`) mit Zeilensperren (`select_for_update()`) gegen Race Conditions.
- **Asynchroner Worker (django-q2)**: Automatisches Ablaufen unbezahlter Cash-Holds via Cron-Job und asynchroner E-Mail-Versand.
- **API-Dokumentation**: Vollständig typisierte OpenAPI 3 / Swagger-Spezifikation via `drf-spectacular`.

---

## 📂 Projektstruktur

```text
Fly Ticket Project/
├── duffel-booking-platform-tech-brief.pdf   # Duffel Plattform-Spezifikation
├── README.md                                # Projekt-Hauptdokumentation
├── .gitignore                               # Globaler Ausschluss vertraulicher Daten
└── Fly-Software/
    ├── docker-compose.yml                   # Multi-Container-Orchestrierung
    ├── DOCKER.md                            # Detaillierte Docker-Anleitung
    ├── .env.example                         # Umgebungsvariablen-Vorlage
    ├── Documentation/                       # Architektur- & Setup-Guides
    │   ├── backend_implementation.md
    │   ├── frontend_implementation.md
    │   └── project_run_guide.md
    ├── backend/                             # Django 5 REST Backend
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── bookingsoft/                     # Django Core & Settings
    │   ├── flights/                         # Flugsuche, Buchungen & State Machine
    │   ├── payments/                        # Stripe & Cash-Hold Logik
    │   ├── accounts/                        # Custom User & RBAC (Customer, Agent, Admin)
    │   └── services/                        # Duffel & Stripe Clients
    └── frontend/                            # React SPA (Vite)
        ├── Dockerfile
        ├── nginx.conf                       # Nginx Reverse Proxy
        ├── package.json
        ├── tailwind.config.js
        └── src/                             # React-Komponenten & Pages
```

---

## 🐳 Schnellstart mit Docker (Empfohlen)

Die gesamte Plattform lässt sich über Docker Compose mit einem einzigen Befehl starten:

```bash
cd Fly-Software

# 1. Umgebungsvariablen aus der Vorlage erstellen
cp .env.example .env

# 2. Container im Hintergrund bauen und starten
docker compose up -d --build
```

Container stoppen:
```bash
docker compose down
```

---

## 💻 Lokale Entwicklung ohne Docker

### 1. Backend starten
```powershell
cd Fly-Software\backend

# Virtuelle Umgebung aktivieren (oder neu anlegen mit: python -m venv .venv)
.\.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r requirements.txt

# Migrationen ausführen & Server starten
python manage.py migrate
python manage.py runserver
```

### 2. Background Worker starten (in separatem Terminal)
```powershell
cd Fly-Software\backend
.\.venv\Scripts\Activate.ps1
python manage.py qcluster
```

### 3. Frontend starten (in separatem Terminal)
```powershell
cd Fly-Software\frontend
npm install
npm run dev
```

---

## 🌐 Dienste & Endpunkte

| Dienst | URL | Beschreibung |
|---|---|---|
| **Frontend Web App** | `http://localhost:5173` | React Single Page Application |
| **Backend REST API** | `http://localhost:8000/api/v1/` | Django REST Framework API Endpunkte |
| **Swagger UI (OpenAPI 3)** | `http://localhost:8000/api/docs/` | Interaktive API-Dokumentation |
| **Django Admin** | `http://localhost:8000/admin/` | Administrationsbereich für Buchungen & Benutzer |

---

## 🔒 Sicherheit & Umgebungsvariablen

- Alle sicherheitskritischen Schlüssel (Duffel API Token, Stripe API Keys, Django Secret Key) werden über Umgebungsvariablen (`.env`) geladen.
- Vertrauliche `.env`-Dateien und lokale SQLite-Datenbanken (`*.sqlite3`) sind in `.gitignore` eingetragen und werden **niemals** in das Versionskontrollsystem hochgeladen.
- Für neue Umgebungen dient `Fly-Software/.env.example` als Vorlage.

---

## 📖 Weiterführende Dokumentation

- [Docker Guide (DOCKER.md)](Fly-Software/DOCKER.md)
- [Backend Architektur & State Machine](Fly-Software/Documentation/backend_implementation.md)
- [Frontend Architektur & Komponenten](Fly-Software/Documentation/frontend_implementation.md)
- [Schritt-für-Schritt Ausführungsleitfaden](Fly-Software/Documentation/project_run_guide.md)
