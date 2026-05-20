# 🔐 IAM-API-V2

> **Production-grade Identity & Access Management API** — containerized, secured, and deployed to the cloud with a fully automated CI/CD pipeline.

A stateless authentication and authorization service built with **FastAPI** and **PostgreSQL**, featuring **JWT-based authentication**, **bcrypt password hashing**, and **Role-Based Access Control (RBAC)**. Engineered for production from the ground up: containerized with Docker, automatically built and published via GitHub Actions, and deployed on **AWS EC2**.

---

## 🏷️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![AWS EC2](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonec2&logoColor=white)

---

## 🏗️ Architecture Overview

The system is designed around a clean, automated pipeline from local development to cloud production.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER MACHINE                           │
│                                                                     │
│   FastAPI App  ──►  docker-compose up  ──►  Live-Reload Dev Server  │
│       +                                         (port 8000)         │
│   PostgreSQL                                                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  git push → main
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB ACTIONS (CI/CD)                      │
│                                                                     │
│   1. Checkout code                                                  │
│   2. Authenticate with Docker Hub (via Repository Secrets)          │
│   3. Build flattened production image                               │
│   4. Push image → Docker Hub Registry                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  Image published
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS EC2 (Ubuntu)                            │
│                                                                     │
│   docker-compose pull  ──►  docker-compose up -d                   │
│                                                                     │
│   Container Port 8000  ──►  Host Port 80  ──►  Public Internet     │
│   (Bypasses DPI/Firewall port blocking via HTTP port mapping)       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔒 Security

- **bcrypt Password Hashing** — User passwords are never stored in plaintext. All credentials are hashed using `bcrypt` before persistence.
- **JWT Stateless Authentication** — Issues cryptographically signed JSON Web Tokens (SHA-256) upon successful login, enabling stateless, scalable session management.
- **Role-Based Access Control (RBAC)** — Granular authorization middleware using FastAPI's `Depends` injection system, cleanly separating `user` and `admin` endpoint access.
- **Duplicate Registration Protection** — Gracefully handles `UniqueViolation` database errors to prevent duplicate account creation and avoid information leakage.

### ⚙️ DevOps & Infrastructure

- **Fully Containerized** — Both the API and the PostgreSQL database run as isolated Docker containers, ensuring environment parity between development and production.
- **Automated CI/CD Pipeline** — Every push to `main` triggers a GitHub Actions workflow that builds and publishes a fresh production image to Docker Hub — zero manual steps.
- **Cloud-Deployed** — Running on an AWS EC2 instance (Ubuntu), pulled directly from Docker Hub and orchestrated with Docker Compose.
- **Firewall-Aware Networking** — Container port `8000` is mapped to public port `80` to bypass aggressive DPI and cloud firewall restrictions, ensuring reliable public access.

---

## 🚀 Local Quickstart

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) installed
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Chinkhuselts/iam-api-v2.git
cd iam-api-v2
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (never commit this file):

```env
# Database
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=iam_db

# JWT
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Start All Services

```bash
docker-compose up --build
```

This command spins up two containers:
- **`api`** — FastAPI application with live-reload via volume mapping
- **`db`** — PostgreSQL 15 database

### 4. Access the API

| Interface        | URL                                    |
|------------------|----------------------------------------|
| Interactive Docs | `http://localhost:8000/docs`           |
| ReDoc            | `http://localhost:8000/redoc`          |
| Health Check     | `http://localhost:8000/`              |

### Tear Down

```bash
docker-compose down -v   # -v removes named volumes (clears database)
```

---

## ⚡ CI/CD Pipeline

Automated delivery is handled by **GitHub Actions**, defined in `.github/workflows/`.

**Trigger:** Any push to the `main` branch.

**Pipeline Steps:**

1. **Checkout** — Pulls the latest source code into the runner environment.
2. **Authenticate** — Logs into Docker Hub using `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` stored as encrypted **Repository Secrets** (credentials never exposed in code).
3. **Build** — Constructs a flattened, optimized production Docker image from the `Dockerfile`, minimizing layer count and final image size.
4. **Push** — Publishes the tagged image to the Docker Hub registry, making it immediately available for deployment.

```
[ Push to main ] ──► [ Login to Docker Hub ] ──► [ docker build ] ──► [ docker push ]
```

No manual build steps. No manual deployments. Every merge to `main` is a deployable artifact.

---

## ☁️ Production Deployment

The API is hosted on an **AWS EC2 instance** running Ubuntu Linux.

### Infrastructure Setup

- **EC2 Instance** — Ubuntu server with Docker and Docker Compose installed.
- **Networking** — The application container's internal port `8000` is mapped to the server's public port `80`, bypassing aggressive DPI (Deep Packet Inspection) and firewall restrictions that commonly block non-standard ports on cloud infrastructure.
- **Image Source** — The production `docker-compose.yml` pulls the latest image directly from **Docker Hub**, ensuring the deployed version always matches the latest passing CI build.

### Deploy / Update

SSH into the EC2 instance and run:

```bash
# Pull the latest image from Docker Hub
docker-compose pull

# Restart services with zero-downtime container replacement
docker-compose up -d
```

---

## 📁 Project Structure

```
iam-api-v2/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD pipeline definitions
├── app/                    # FastAPI application source code
│   ├── main.py             # Application entrypoint & router registration
│   ├── models/             # Pydantic schemas & database models
│   ├── routes/             # API endpoint definitions
│   ├── auth/               # JWT creation, verification & RBAC middleware
│   └── database.py         # PostgreSQL connection & session management
├── Dockerfile              # Production image definition (flattened build)
├── docker-compose.yml      # Local development multi-container environment
└── requirements.txt        # Python dependencies
```

---

## 👤 Author

**Chinkhusel Tsolmonbaatar**

[![GitHub](https://img.shields.io/badge/GitHub-Chinkhuselts-181717?style=flat-square&logo=github)](https://github.com/Chinkhuselts)

---

*Built as a portfolio project demonstrating cloud infrastructure, DevSecOps, and backend engineering practices.*
