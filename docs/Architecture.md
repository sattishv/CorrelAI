
# CorrelAI Architecture

Version: v0.1.0

Status: Frozen

---

# Vision

CorrelAI is an AI-assisted Performance Engineering Platform capable of analyzing:

- HAR
- JMX
- JTL
- Postman Collections
- Browser Traces
- Future Formats

using a common Intermediate Representation (IR).

---

# Design Principles

1. Framework Agnostic
2. Tool Agnostic
3. Container First
4. Plugin Architecture
5. AI Assisted (not AI dependent)
6. Stateless Services
7. REST-first Backend

---

# High Level Architecture

                React UI

                    │

                    ▼

            FastAPI Backend

                    │

                    ▼

          Intermediate Representation

                    │

        ┌───────────┼────────────┐

        ▼           ▼            ▼

   HAR Parser   JMX Parser   Replay Parser

        │           │            │

        └───────────┼────────────┘

                    ▼

          Correlation Engine

                    ▼

          Recommendation Engine

                    ▼

               Report Engine

                    ▼

                 AI Engine

---

# Repository Structure

CorrelAI

backend

frontend

docs

examples

scripts

docker

---

# Backend

backend/app

api

core

models

ir

parsers

analyzers

plugins

services

reports

utils

---

# Intermediate Representation

Every parser converts source artifacts into the IR.

HAR

↓

IR

JMX

↓

IR

JTL

↓

IR

The analyzers only understand IR.

---

# Container Strategy

Frontend

React

↓

Backend

FastAPI

↓

Optional Worker

↓

Storage

Every service is independently containerized.

---

# Configuration

Everything comes from environment variables.

No hardcoded paths.

No machine specific configuration.

---

# Logging

stdout

stderr

Future:

JSON Logs

OpenTelemetry

---

# Plugin Model

Core knows nothing about

ASP.NET

Spring

Node

React

Angular

Salesforce

SAP

Plugins detect framework specific patterns.

---

# Roadmap

v0.1

Core Engine

v0.2

Correlation Engine

v0.3

Replay Engine

v0.4

AI Assistant

v1.0

Community Release