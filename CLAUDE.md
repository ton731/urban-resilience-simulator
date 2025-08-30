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

**Note**: This repository is currently in the initial documentation phase. The codebase structure outlined in the technical documentation has not yet been implemented.

### Existing Files
- `README.md` - Basic project identifier
- `docs/prd.md` - Complete Product Requirements Document (in Traditional Chinese)
- `docs/tech.md` - Technical architecture and project structure specification (in Traditional Chinese)
- `.gitignore` - Standard Python gitignore with additional tools (Ruff, Cursor, Marimo, etc.)

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

The project documentation is written in Traditional Chinese, reflecting the Taiwan context for urban resilience planning. The target users are primarily government disaster response units, urban planning departments, and infrastructure management agencies in Chinese-speaking regions.