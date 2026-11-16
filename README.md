# Relay — Real-Time Chat Platform

[![CI](https://github.com/PerepaMoorty/relay-chat/actions/workflows/ci.yml/badge.svg)](https://github.com/PerepaMoorty/relay-chat/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/socket.io-4.7.5-black.svg)](https://socket.io/)

> **Relay** is a zero-configuration, real-time chat platform engineered on Flask and Socket.IO. It provides duplex WebSocket messaging, presence tracking, direct messages, read receipts, file sharing, and moderation over a monolithic architecture.

![Relay Interface](docs/demos/screenshot.png)

---

## Features by Epic

- **E1: Connection & Session:** Persistent bi-directional WebSocket connection, automatic client reconnection, and presence grace period.
- **E2: Identity & Authentication:** User registration, login with salted scrypt hashing, session cookies, and session invalidation on logout.
- **E3: Messaging Engine:** Instant messaging in public `#general`, direct 1:1 private chats, live in-place message editing, soft-delete, and cursor pagination.
- **E4: Presence & Interaction:** Online member roster, ephemeral join/leave notifications, live typing indicators, read receipts, and sync catch-up.
- **E5: Channel Management:** Custom group room creation (public or invite-only), room directories, and member departure.
- **E6: File Sharing:** Media and document sharing up to 10 MB with MIME checking, inline image previews, and members-only downloads.
- **E7: Message Search:** Scoped full-text message search across accessible rooms.
- **E8: Moderation & Administration:** Member reporting, administrative message deletion, time-bound user muting, account bans, and append-only audit logging.

---

## Quick Start

### 1. One-Click Automated Demo

We provide one-click demo scripts that automatically initialize a virtual environment, install dependencies, seed test users and channels, and launch the server:

- **Windows:**
  ```cmd
  run-demo.bat
  ```

- **macOS / Linux:**
  ```bash
  chmod +x run-demo.sh
  ./run-demo.sh
  ```

Once started, navigate your browser to: **`http://localhost:5000`**

---

### 2. Manual Setup

If you prefer to configure the environment manually:

#### Prerequisites
- Python 3.11+
- Git

#### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PerepaMoorty/relay-chat.git
   cd relay-chat
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Seed demo data:**
   ```bash
   flask --app run seed-demo
   ```

5. **Start the Relay server:**
   ```bash
   python run.py
   ```
   Open `http://localhost:5000` in your web browser.

---

## Demo Accounts

The `seed-demo` command populates the database with standard testing credentials:

| Username | Password | Role | Description |
|---|---|---|---|
| `alice` | `password123` | User | Standard demo participant |
| `bob` | `password123` | User | Standard demo participant |
| `carol` | `password123` | User | Standard demo participant |
| `admin` | `admin123` | Admin | System administrator with moderation console |

To create a new administrator account via CLI:
```bash
flask --app run create-admin <username> <password>
```

---

## Local Area Network (LAN) Usage

Relay binds to `0.0.0.0:5000` by default, allowing peer devices on the same Wi-Fi or LAN subnet to connect seamlessly:

1. Determine your host computer's local IP address:
   - **Windows:** Run `ipconfig` (look for *IPv4 Address*, e.g., `192.168.1.45`).
   - **macOS / Linux:** Run `ifconfig` or `ip a`.
2. Allow incoming connections on port 5000 if prompted by your operating system firewall.
3. Other devices on the same network can access the application by navigating to:
   ```
   http://<YOUR_LOCAL_IP>:5000
   ```
4. If testing across origins or custom domain bindings, specify `CORS_ORIGINS` in your `.env` file (e.g. `CORS_ORIGINS=http://192.168.1.45:5000`).

---

## Testing & Quality Assurance

Run the automated test suite and code style linters locally:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pytest test suite
pytest

# Run linter checks
ruff check .
```

---

## Project Structure

```
relay-chat/
├── .github/              # CI workflows and PR/issue templates
├── docs/                 # Software engineering specifications & records
│   ├── srs.md            # Software Requirements Specification (SRS v2.0)
│   ├── architecture.md   # Software Architecture Document (SAD v1.0)
│   ├── features.md       # MoSCoW Feature Breakdown
│   ├── diagrams/         # System architecture and use-case diagrams
│   └── demos/            # Demonstration scripts and screenshots
├── relay/                # Application package
│   ├── api/              # REST Blueprints (auth, rooms, files, search, admin)
│   ├── events/           # Flask-SocketIO event handlers and ack decorators
│   ├── models/           # SQLAlchemy database schemas
│   ├── services/         # Core business and domain logic
│   ├── static/           # Front-end ES modules, styles, and assets
│   └── templates/        # Jinja HTML entry page
├── instance/             # SQLite database and uploaded attachments (git-ignored)
├── run.py                # Server execution entry point
├── run-demo.bat          # One-click Windows startup script
├── run-demo.sh           # One-click Unix startup script
└── requirements.txt      # Production runtime dependencies
```

---

## Documentation Links

- **[SRS v2.0 & Traceability Matrix (RTM)](docs/srs.md)**
- **[Software Architecture Document (SAD)](docs/architecture.md)**
- **[Features Specification (MoSCoW)](docs/features.md)**
- **[Demonstration Guide & Video Notes](docs/demos/README.md)**

---

## Team & Project Details

**Course:** UE24CS341A Software Engineering, Section E, Team 8  
**Repository:** [https://github.com/PerepaMoorty/relay-chat](https://github.com/PerepaMoorty/relay-chat)

| Member | SRN | Role | Primary Responsibilities |
|---|---|---|---|
| **Lakshmi Narasimha Moorty Perepa** | PES2UG24CS248 | Developer 1 (Backend) & Repo Owner | Server architecture, models, services, APIs, PR reviews & merges |
| **Malepati Viswajith** | PES2UG24CS259 | Developer 2 (Frontend) & QA Owner | Single-page UI/UX, Socket.IO client, automated & manual testing |
| **Medha Singh** | PES2UG24CS274 | Scrum Master | Agile board management, CI workflow, sprint notes & releases |
| **Naivadh Shrivastava** | PES2UG24CS297 | Product Owner | Backlog order, SRS v2.0 & RTM, acceptance sign-off, README & demos |
