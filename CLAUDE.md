# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Urban Resilience Simulation Platform (城市韌性模擬平台) - a digital twin simulation platform designed to quantify and visualize the cascading impacts of natural disasters (initially focusing on typhoon damage) on urban infrastructure and emergency response capabilities.

## Project Architecture

The project follows a complete frontend-backend separation architecture:

### Planned Structure
- **Backend**: Python FastAPI providing high-performance API services for all core computations
- **Frontend**: React.js creating highly interactive, data-driven visualization interface

### Core Modules (As Per Technical Specification)
1. **World Synthesizer** (世界合成器) - Procedural generation of virtual city environments
2. **Simulation Engine** (模擬引擎) - Core computation unit handling disaster simulation and network analysis  
3. **Impact Analysis Module** (衝擊分析模組) - Transforms simulation results into meaningful high-level indicators
4. **Visualization & Control Interface** (視覺化與控制介面) - Interactive frontend for user interaction

## Current State

### ✅ Implemented Features

**WS-1.1: Procedural Map Generation** - **COMPLETED**
- Full backend implementation of procedural 2D map generation
- Random but logical road networks with main roads and secondary roads
- Graph data structure using NetworkX for efficient pathfinding
- Configurable generation parameters
- FastAPI endpoint: `POST /api/v1/world/generate`

### Existing Files
- `README.md` - Basic project identifier
- `docs/prd.md` - Complete Product Requirements Document (in Traditional Chinese)
- `docs/tech.md` - Technical architecture and project structure specification (in Traditional Chinese)
- `backend/` - FastAPI backend with WS-1.1 implementation
- `.gitignore` - Standard Python gitignore with additional tools (Ruff, Cursor, Marimo, etc.)

## Development Commands

### Backend Development

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Start development server with hot reload
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test WS-1.1 map generation directly
cd backend && python demo_ws11.py

# Run tests (when implemented)
cd backend && pytest tests/
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Approach

When implementing this project, follow the technical architecture specified in `docs/tech.md`:

### Backend Implementation (`backend/`)
- Use FastAPI for API endpoints
- Implement the four core modules as separate packages
- Use Pydantic for data validation schemas
- Maintain clean separation between API routes and business logic

### Frontend Implementation (`frontend/`)
- React.js with component-based architecture
- Separate concerns: components (UI), containers (logic), services (external integrations)  
- Use Leaflet.js for map visualization (encapsulated in `mapService.js`)
- Implement state management with Zustand
- Custom hooks for API interactions and reusable logic

### Key Design Principles
- High cohesion, low coupling between modules
- Structured data interfaces between components
- Extensibility for future features (real map data import, dynamic weather models, etc.)

## Language Context
- Please write a test script to demo the input/output of the new-added feature if necessary after your implementation.
- Don't write READMEs after implementation.
- Backend is already deployed on http://0.0.0.0:8000 . If you need to test it, don't deploy it yourself, use this deployed endpoint
- Don't run python scripts by your own.
- Don't pip install python packages by your own, please ask me to do it, since I need to activate conda env and you will run into some problem if you do it yourself.