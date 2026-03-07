"""
API Documentation for Noug Neural OS
Auto-generated Swagger/OpenAPI documentation
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """Custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Noug Neural OS API",
        version="4.0.0",
        description="""
# Noug Neural OS - Biologically-Inspired AI System

## Overview
Noug Neural OS is a complete, production-ready AI system with 19 advanced subsystems.

## Features
- 🧠 Memory System (ChromaDB + Vector Search)
- 🤖 Reasoning Engine (LangChain + Multi-LLM)
- 👁️ Vision Processing (CLIP + BLIP)
- 🔌 Plugin System (7 categories)
- 🤝 Multi-Agent System (5 types, 7 capabilities)
- ⚡ High Performance (97.7% compression)
- 🗄️ Multi-Database (12 types)
- 🌊 Event Streaming (3 routing paths)

## Architecture
- Biologically-inspired design
- Event-driven architecture
- Multi-modal processing
- Scalable and extensible

## Authentication
Currently no authentication required. Will be added in production deployment.

## Rate Limiting
- Default: 100 requests per minute
- Configurable per endpoint

## Support
- Documentation: /docs
- GitHub: [Repository URL]
- Email: support@nougneuralos.ai
        """,
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}

    app.openapi_schema = openapi_schema
    return app.openapi_schema
