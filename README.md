# Nexus AI Framework

<p align="center">
  <strong>Multi-Agent Collaborative Orchestration & Self-Evolution Framework</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-integration-layers">Layers</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</p>

---

## Overview

Nexus AI is a production-grade **multi-agent orchestration framework** that enables intelligent collaboration, self-evolution, and secure code execution among autonomous AI agents. Built on the **"Three Provinces Six Ministries" (三省六部)** architectural pattern inspired by ancient Chinese governance, it provides:

- **Dynamic Agent Scheduling** — Priority-based task dispatch, swarm self-organization, load-aware routing
- **Hippocampus Memory System** — Three-tier storage (working/short-term/long-term) with active forgetting and cross-domain association
- **Personality-Driven Interaction** — Historical persona vectors (Zhou Yu / Lu Xun), thought-atom injection, emotional accumulation analysis
- **Streaming Report Generation** — Character-by-character streaming output, multi-modal input support
- **Cost-Optimized LLM Routing** — Group-based model routing with budget circuit-breaker, 30-50% API cost reduction
- **Adversarial Self-Play Training** — Red-team / blue-team code-level confrontation in sandboxed environments
- **Cultivation Gamification Layer** — Agent progression system with 25 cultivation realms, experience points, skill markets, and tournament leaderboards

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5%2B-3178C6)](https://www.typescriptlang.org/)

---

## Features

### Core Capabilities

| Module | Description |
|--------|-------------|
| **Agent Scheduler** | Dynamic team formation, priority preemption, WLC load balancing |
| **Memory System** | Hippocampus-inspired 3-tier memory with vector retrieval and active forgetting |
| **Personality Engine** | Historical persona embeddings, emotion tracking, dialogue style adaptation |
| **Report Generator** | Streaming multi-section reports with chart rendering and export |
| **LLM Router** | Group-based model selection, budget-aware circuit breaker, cost optimization |
| **Security Kernel** | Adversarial self-play, sandbox execution, audit trail, auto-recovery |

### Integration Layers (42 Layers)

The framework includes **42 deeply integrated modules** covering every aspect of multi-agent systems:

```
Foundation (L1-L10)    → Data closed-loop, GUI automation, video gen, multimodal, streaming fix
Intelligence (L11-L20) → Deep fusion dashboard, dual-scenario diff, quant mastery, tri-realm tech
Growth (L21-L30)       → User conversion, ops guardian, risk defense, SEO ecosystem, sandbox exec
Evolution (L31-L42)     → Claude Code core, code execution deep integration, cultivation fusion,
                          red-blue adversarial training
```

### Cultivation System (Gamification)

Agents progress through **25 cultivation realms** (炼气→筑基→金丹→元婴→化神→...→大成), earning:
- **Experience Points (EXP)** from task completion, analysis, code execution
- **Skill Points** for purchasing agent abilities from the Talent Market
- **Security Titles** through adversarial challenge participation
- **Tournament Rankings** in periodic red-blue competitions

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Redis (optional, for working memory)
- PostgreSQL or SQLite (for persistence)

### Installation

```bash
# Clone the repository
git clone https://github.com/立成玉1207/Nexus-AI.git
cd Nexus-AI

# Backend - create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Frontend - install Node dependencies
npm install
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings:
# - DATABASE_URL=sqlite:///./app.db
# - REDIS_URL=redis://localhost:6379
# - LLM_API_KEY=your-api-key
# - SECRET_KEY=your-secret-key
```

### Running

```bash
# Start backend server (FastAPI on port 8000)
cd backend
python main.py

# In another terminal, start frontend dev server (Vite on port 5173)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) to access the dashboard.

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d --build
```

---

## Architecture

### Three Provinces Six Ministries (三省六部)

```
                    ┌─────────────────────┐
                    │  尚书省 Shangshu     │
                    │  Task Scheduling     │
                    │  Load Balancing      │
                    └────────┬────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌──────────┐     ┌──────────────┐   ┌──────────────┐
   │户部 HuBu  │     │工部 GongBu   │   │兵部 BingBu   │
   │Economy &  │     │Code Gen &    │   │Sandbox Exec  │
   │Points    │     │Debug         │   │& Security    │
   └──────────┘     └──────────────┘   └──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
   ┌──────────┐     ┌──────────────┐   ┌──────────────┐
   │吏部 LiBu  │     │礼部 Libu     │   │刑部 XingBu   │
   │Memory &  │     │Personality & │   │Audit &       │
   │Knowledge │     │Interaction   │   │Compliance    │
   └──────────┘     └──────────────┘   └──────────────┘
                             │
                    ┌────────▼────────────┐
                    │  兵部 BingBu        │
                    │  Code Execution      │
                    │  Sandbox (L38-L42)   │
                    └─────────────────────┘
```

### Service Topology

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │    │  Gatekeeper  │    │  Backend    │
│  (React+TS) │───▶│  (API GW)   │───▶│  (FastAPI)  │
│  :5173     │    │  :8080      │    │  :8000      │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                                │
                    ┌─────────────────────────────┼──────────────────┐
                    ▼                             ▼                  ▼
           ┌──────────────┐             ┌─────────────┐   ┌──────────────┐
           │  Heartbeat   │             │   Snapshot   │   │ Worry Eraser  │
           │  Monitor     │             │  Backup/Restore│  │  Safety Filter│
           └──────────────┘             └─────────────┘   └──────────────┘
```

---

## Project Structure

```
Nexus-AI/
├── app/                        # Core application domain models
│   ├── core/                   # Business logic (bus, config, security)
│   ├── models/                 # Data models (agent, task, user)
│   ├── schemas/                # Pydantic schemas
│   ├── workflow/               # DAG workflow engine
│   └── ai_agents/              # Agent definitions
│
├── backend/                    # Main backend service (FastAPI)
│   ├── agents/                 # Agent implementations (100+ agents)
│   │   ├── business/           # Business intelligence agents
│   │   ├── compliance/        # Audit & compliance agents
│   │   ├── counterstrike/      # Defense & counter-strike agents
│   │   ├── five_end/           # Five-end ecosystem coordination
│   │   ├── living/             # Living agent system
│   │   ├── memory/             # Memory & immunity agents
│   │   └── security/           # Security kernel agents
│   ├── routers/                # API route handlers (120+ endpoints)
│   ├── services/               # Business services layer
│   ├── integration/            # ★ 42 Integration Layers (L1-L42)
│   │   ├── infrastructure_adapters.py
│   │   ├── data_closed_loop_layer.py
│   │   ├── gui_automation_layer.py
│   │   ├── multimodal_integration_layer.py
│   │   ├── streaming_fix_layer.py
│   │   ├── deep_fusion_dashboard_layer.py
│   │   ├── professional_dialogue_layer.py
│   │   ├── dual_scenario_differentiation_layer.py
│   │   ├── fusion_quant_mastery_layer.py
│   │   ├── trirealm_advanced_tech.py
│   │   ├── user_conversion_layer.py
│   │   ├── operations_guardian_layer.py
│   │   ├── risk_awareness_defense_layer.py
│   │   ├── seo_content_ecosystem_layer.py
│   │   ├── sandbox_execution_layer.py       # L38
│   │   ├── claude_code_core_layer.py         # L39
│   │   ├── code_execution_deep_integration_layer.py  # L40
│   │   ├── cultivation_deep_fusion_layer.py  # L41
│   │   └── red_blue_adversarial_layer.py     # L42
│   ├── cultivation/            # ★ Cultivation system (gamification)
│   │   ├── cultivation_models.py   # 751 SQLAlchemy ORM models
│   │   ├── cultivation_complete_system.py
│   │   ├── formation_array.py     # Formation patterns
│   │   └── demon_body_externalqi.py
│   ├── hippocampus/            # Memory system (hippocampus architecture)
│   ├── personality/            # Personality engine
│   ├── alchemy/                # Self-play & evolution engine
│   ├── migrations/             # Database migration scripts
│   └── main.py                 # Application entry point
│
├── src/                        # Frontend source (React + TypeScript)
│   ├── components/            # 81 UI components
│   ├── pages/                  # 86 page components
│   ├── api/                    # API client functions
│   ├── hooks/                  # React hooks
│   ├── stores/                 # State management
│   ├── styles/                 # CSS / brand styles
│   └── i18n/                   # Internationalization
│
├── frontend/                   # Legacy frontend (Vite build)
├── gatekeeper/                 # API gateway service
├── heartbeat/                  # Health monitoring service
├── snapshot/                   # Backup & snapshot service
├── worry_eraser/               # Content safety filter
├── backup_gateway/             # Backup gateway service
├── config/                     # Configuration files
├── public/                     # Static assets (favicon, sitemap, robots)
├── proto/                      # Protocol buffer definitions
├── scripts/                    # Utility & deployment scripts
├── tests/                      # Test suite
├── Dockerfile                  # Container definition
├── docker-compose.yml         # Multi-service orchestration
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── .gitignore                  # Git ignore rules
├── PATENTS.md                  # Patent portfolio (34 patents)
├── CONTRIBUTING.md             # Contribution guidelines
└── README.md                   # This file
```

---

## Integration Layers Detail

| Layer | Name | Key Modules | Tests |
|-------|------|-------------|-------|
| L38 | Sandbox Execution | LightweightSandbox, DangerousCommandDetector, SecurityPrecheckEngine | 18 |
| L39 | Claude Code Core | TaskDecomposer, ToolRegistry, StaticCodeScanner, SecurityConfirmationEngine | 26 |
| L40 | Code Execution Deep Integration | BingbuAsyncExecutor, GongbuCodeGenPro, ZhongshuTaskDecomposerV2, UserRiskProfiler | 27 |
| L41 | Cultivation Deep Fusion | RealmStyleAdapter, CultivationTaskEngine, MarketRealmGate, AgentResonance, PointsExchange | 21 |
| L42 | Red-Blue Adversarial | RedTeamAttackGenerator, BlueTeamDefenseGenerator, SelfPlayTrainingController, CultivationAdversarialFusion | 30 |

**Total: 751 SQLAlchemy ORM models across 52 parts**

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115+
- **Language**: Python 3.10+
- **ORM**: SQLAlchemy (751 models)
- **Database**: PostgreSQL / SQLite
- **Cache**: Redis (optional)
- **Task Queue**: Celery
- **Auth**: JWT + RBAC

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Build Tool**: Vite
- **State Management**: Zustand
- **Styling**: CSS + Tailwind-ready
- **Charts**: Custom SVG-based visualization

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **API Gateway**: Custom (Gatekeeper)
- **Monitoring**: Prometheus + custom health checks
- **Protocol**: gRPC (agent communication), WebSocket (real-time)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone your fork
git clone https://github.com/<your-username>/Nexus-AI.git
cd Nexus-AI
git checkout -b feature/your-feature-name

# Make your changes
# Run tests
pytest tests/

# Commit and push
git commit -m "Add: your feature description"
git push origin feature/your-feature-name
# Open Pull Request
```

### Code Style

- Python: `black` + `isort` formatting
- TypeScript: ESLint + Prettier
- All new integration layers must include test suite (target: >90% pass rate)
- New ORM models follow existing Part N naming convention

---

## Patent Portfolio

This project is backed by **34 planned invention patents** covering:

| Category | Patents | Key Areas |
|----------|---------|-----------|
| Agent Scheduling & Collaboration | 5 | Dynamic teaming, swarm self-organization, priority dispatch |
| Memory & Knowledge Enhancement | 5 | Tiered storage, active forgetting, cross-domain association |
| Personality & Interaction | 4 | Historical persona, thought-atom injection, emotional analysis |
| Report Generation & Streaming | 3 | Streaming output, progressive charts, multi-modal input |
| Cost Optimization & Routing | 2 | Group model routing, budget circuit breaker |
| Security & Self-Evolution | 4 | Self-play training, RL-based learning, attack recognition |
| Operations & High Availability | 4 | Config insurance, auto-rollback, health monitoring, distributed tracing |
| Ecosystem & Commercialization | 4 | Talent market, bond synergy quantification, five-end ecology |
| Testing & Data Analysis | 3 | Automated testing, behavior analytics, admin dashboard |

> See [PATENTS.md](PATENTS.md) for the full patent list.

---

## License

Copyright (c) 2026 Chengyu Li (李成玉)

Licensed under the **Apache License, Version 2.0** (the "License").

You may not use this file except in compliance with the License.
You may obtain a copy of the License at:

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.

---

## Acknowledgments

- **Open Source Community**: Built upon FastAPI, React, SQLAlchemy, Redis, and many other excellent open-source projects
- **Research Inspiration**: MiroFish群体智能引擎, HEAS分层进化仿真, VirtualEnv物理仿真, GAMMS图仿真框架
- **Cultivation Metaphor**: Inspired by Chinese xianxia (cultivation) literature for gamification design

---

<p align="center">
  <b>Nexus AI Framework</b> — Where Multi-Agent Intelligence Meets Production-Grade Engineering<br>
  <sub>Made with dedication by Chengyu Li and contributors</sub>
</p>
