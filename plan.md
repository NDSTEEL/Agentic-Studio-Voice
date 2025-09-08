# Voice Agent Platform - Technical Implementation Plan

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI        │    │  PostgreSQL     │
│   Frontend       │◄──►│   Backend        │◄──►│  Database       │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   WebSocket     │    │  External APIs   │
│   Real-time     │    │  ElevenLabs      │
│   Updates       │    │  Twilio          │
└─────────────────┘    └──────────────────┘
```

### Multi-Tenant Data Model
- Row-level security (RLS) for complete tenant isolation
- Tenant ID embedded in all database operations
- JWT tokens carry tenant context
- API endpoints validate tenant access automatically

## Technology Stack

### Backend (FastAPI)
- **Framework**: FastAPI 0.104+ with Python 3.11+
- **Database ORM**: SQLAlchemy 2.0+ with async support
- **Authentication**: JWT with PyJWT for multi-tenant tokens
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Validation**: Pydantic v2 for request/response validation
- **Background Tasks**: Celery with Redis for async processing
- **Testing**: pytest with pytest-asyncio for async test support

### Database (PostgreSQL)
- **Version**: PostgreSQL 15+ with Row-Level Security
- **Migration**: Alembic for database schema management
- **Connection Pooling**: asyncpg for high-performance async connections
- **Multi-tenancy**: RLS policies for automatic tenant isolation
- **Backup**: Automated daily backups with point-in-time recovery

### Frontend (Next.js)
- **Framework**: Next.js 14+ with App Router
- **TypeScript**: Full TypeScript implementation
- **Styling**: Tailwind CSS for responsive design
- **State Management**: Zustand for lightweight global state
- **Real-time**: Socket.IO client for WebSocket connections
- **Testing**: Vitest + React Testing Library for component tests

### DevOps & Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Development**: Docker Compose for local development stack
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Monitoring**: Structured logging with correlation IDs
- **Environment**: Separate dev/staging/production configurations

## Project Structure

```
Agentic-Studio-Voice/
├── backend/
│   ├── src/
│   │   ├── api/                 # API route modules
│   │   │   ├── tenants.py      # Tenant management endpoints
│   │   │   ├── agents.py       # Voice agent CRUD operations
│   │   │   ├── phone_numbers.py# Phone number provisioning
│   │   │   ├── analytics.py    # Analytics and reporting
│   │   │   └── webhooks.py     # External service webhooks
│   │   ├── models/             # SQLAlchemy database models
│   │   │   ├── tenant.py       # Tenant model with RLS
│   │   │   ├── agent.py        # Voice agent configuration
│   │   │   ├── knowledge.py    # 18-category knowledge system
│   │   │   └── analytics.py    # Call and performance metrics
│   │   ├── services/           # Business logic services
│   │   │   ├── agent_creator.py# Sub-3-minute agent creation
│   │   │   ├── knowledge_extractor.py # Web crawling & AI processing
│   │   │   ├── voice_service.py# ElevenLabs integration
│   │   │   └── phone_service.py# Twilio integration
│   │   ├── auth/               # Authentication & authorization
│   │   │   ├── jwt_handler.py  # JWT token management
│   │   │   ├── tenant_context.py# Multi-tenant context
│   │   │   └── permissions.py  # Role-based access control
│   │   ├── database/           # Database configuration
│   │   │   ├── connection.py   # Async connection management
│   │   │   ├── migrations/     # Alembic migration files
│   │   │   └── rls_policies.py # Row-level security setup
│   │   └── main.py             # FastAPI application entry
│   ├── tests/                  # Comprehensive test suite
│   │   ├── unit/               # Unit tests for each module
│   │   ├── integration/        # API integration tests
│   │   ├── contract/           # API contract tests
│   │   ├── fixtures/           # Reusable test fixtures
│   │   └── conftest.py         # pytest configuration
│   ├── docker/                 # Docker configurations
│   │   ├── Dockerfile          # Production container image
│   │   └── docker-compose.yml  # Development stack
│   ├── requirements.txt        # Python dependencies
│   └── pytest.ini             # pytest configuration
├── frontend/
│   ├── app/                    # Next.js app directory
│   │   ├── (dashboard)/        # Dashboard route group
│   │   │   ├── agents/         # Voice agent management
│   │   │   ├── analytics/      # Analytics and reporting
│   │   │   └── settings/       # Tenant configuration
│   │   ├── api/                # Next.js API routes
│   │   ├── auth/               # Authentication pages
│   │   └── onboarding/         # New user onboarding
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Base UI components
│   │   ├── dashboard/          # Dashboard-specific components
│   │   ├── agents/             # Voice agent components
│   │   └── analytics/          # Analytics visualization
│   ├── lib/                    # Utility libraries
│   │   ├── api.ts              # API client configuration
│   │   ├── websocket.ts        # WebSocket connection management
│   │   └── auth.ts             # Frontend authentication
│   ├── tests/                  # Frontend test suite
│   │   ├── components/         # Component tests
│   │   ├── pages/              # Page tests
│   │   └── integration/        # End-to-end tests
│   ├── package.json            # Node.js dependencies
│   ├── tailwind.config.js      # Tailwind CSS configuration
│   └── next.config.js          # Next.js configuration
├── docs/                       # Project documentation
│   ├── api/                    # API documentation
│   ├── deployment/             # Deployment guides
│   └── development/            # Development setup
├── docker-compose.yml          # Full stack development
├── .github/workflows/          # CI/CD pipelines
└── README.md                   # Project overview
```

## Development Workflow (TDD Approach)

### Test-Driven Development Process
1. **Write Failing Test**: Create test that captures desired functionality
2. **Run Test Suite**: Confirm new test fails (red)
3. **Implement Minimum Code**: Write simplest code to make test pass
4. **Run Test Suite**: Confirm test passes (green)
5. **Refactor**: Improve code while maintaining test pass
6. **Repeat**: Continue cycle for each feature

### Testing Strategy

#### Backend Testing (pytest)
```python
# Test structure example
tests/
├── unit/
│   ├── test_tenant_service.py      # Unit tests for tenant operations
│   ├── test_agent_creator.py       # Unit tests for agent creation logic
│   ├── test_knowledge_extractor.py # Unit tests for web crawling
│   └── test_auth_middleware.py     # Unit tests for authentication
├── integration/
│   ├── test_api_tenants.py         # API integration tests
│   ├── test_api_agents.py          # API integration tests
│   └── test_external_apis.py       # External service integration
└── contract/
    ├── test_api_contracts.py       # API contract validation
    └── test_webhook_contracts.py   # Webhook contract tests
```

#### Frontend Testing (Vitest + React Testing Library)
```typescript
// Test structure example
tests/
├── components/
│   ├── AgentCreationForm.test.tsx  # Component unit tests
│   ├── DashboardLayout.test.tsx    # Layout component tests
│   └── AnalyticsDashboard.test.tsx # Analytics component tests
├── pages/
│   ├── Dashboard.test.tsx          # Page integration tests
│   └── AgentManagement.test.tsx    # Page functionality tests
└── integration/
    ├── agent-creation.test.ts      # End-to-end user flows
    └── authentication.test.ts      # Authentication flow tests
```

### Test Coverage Requirements
- **Minimum Coverage**: 80% across all modules
- **Critical Paths**: 95% coverage for authentication, multi-tenancy, and agent creation
- **Integration Tests**: Cover all API endpoints and external service integrations
- **Contract Tests**: Validate API contracts and external service expectations

## Database Design

### Multi-Tenant Schema with Row-Level Security

```sql
-- Core tenant table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on all tenant-isolated tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Voice agents with tenant isolation
CREATE TABLE voice_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE,
    elevenlabs_voice_id VARCHAR(100),
    knowledge_categories JSONB NOT NULL, -- 18-category structure
    configuration JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their tenant's data
CREATE POLICY tenant_isolation ON voice_agents
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### 18 Knowledge Categories Schema
```sql
-- Knowledge base with structured categories
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL, -- One of 18 categories
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_category CHECK (category IN (
        'business_information', 'products_services', 'support_faq',
        'company_history', 'policies', 'processes_procedures',
        'events_news', 'technical_specs', 'pricing_billing',
        'inventory_stock', 'legal_compliance', 'partnerships',
        'marketing_promotions', 'training_education', 'quality_standards',
        'feedback_reviews', 'emergency_contact', 'custom_business_logic'
    ))
);

ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
```

## External API Integration

### ElevenLabs Voice Service
```python
# Voice service implementation pattern
class VoiceService:
    async def create_voice_agent(self, tenant_id: UUID, agent_config: AgentConfig):
        # 1. Generate voice model from business data
        voice_model = await self._create_voice_model(agent_config)
        
        # 2. Configure response templates for 18 categories
        response_templates = await self._generate_response_templates(agent_config)
        
        # 3. Deploy voice agent to ElevenLabs
        deployment = await self._deploy_voice_agent(voice_model, response_templates)
        
        return deployment
```

### Twilio Phone Service
```python
# Phone service implementation pattern  
class PhoneService:
    async def provision_phone_number(self, tenant_id: UUID, preferences: PhonePreferences):
        # 1. Search available numbers based on preferences
        available_numbers = await self._search_available_numbers(preferences)
        
        # 2. Provision selected number
        phone_number = await self._provision_number(available_numbers[0])
        
        # 3. Configure call routing to voice agent
        await self._configure_call_routing(phone_number, tenant_id)
        
        return phone_number
```

## Real-time Progress Updates

### WebSocket Implementation
```python
# WebSocket manager for real-time updates
class ProgressManager:
    async def broadcast_agent_creation_progress(self, tenant_id: UUID, progress: ProgressUpdate):
        # Send progress update to specific tenant's WebSocket connections
        await self._broadcast_to_tenant(tenant_id, {
            "type": "agent_creation_progress",
            "progress": progress.dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
```

### Sub-3-Minute Agent Creation Pipeline
```python
# Agent creation workflow with progress tracking
async def create_voice_agent_pipeline(tenant_id: UUID, business_url: str):
    progress_manager = ProgressManager()
    
    # Step 1: Web crawling (30 seconds)
    await progress_manager.update(tenant_id, "crawling_website", 10)
    website_data = await crawl_business_website(business_url)
    
    # Step 2: Knowledge extraction (60 seconds)
    await progress_manager.update(tenant_id, "extracting_knowledge", 35)
    knowledge_categories = await extract_18_categories(website_data)
    
    # Step 3: Voice agent generation (45 seconds)
    await progress_manager.update(tenant_id, "generating_agent", 65)
    voice_agent = await generate_voice_agent(knowledge_categories)
    
    # Step 4: Phone number provisioning (30 seconds)
    await progress_manager.update(tenant_id, "provisioning_phone", 85)
    phone_number = await provision_phone_number(tenant_id)
    
    # Step 5: Deployment (15 seconds)
    await progress_manager.update(tenant_id, "deploying_agent", 95)
    deployment = await deploy_voice_agent(voice_agent, phone_number)
    
    await progress_manager.complete(tenant_id, deployment)
    return deployment
```

## Deployment Strategy

### Docker Configuration
```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as backend-base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM backend-base as backend-production
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Development Stack
```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: voice_agents
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://dev:devpassword@postgres:5432/voice_agents
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
    command: npm run dev

volumes:
  postgres_data:
```

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: test_voice_agents
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests with coverage
        run: |
          cd backend  
          pytest --cov=src --cov-report=xml --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

## Security Considerations

### Multi-Tenant Security
- Row-level security (RLS) for automatic tenant isolation
- JWT tokens with embedded tenant context
- API middleware validates tenant access on every request
- Database policies prevent cross-tenant data access

### API Security
- Rate limiting per tenant to prevent abuse
- Input validation with Pydantic models
- SQL injection prevention with parameterized queries
- CORS configuration for frontend-backend communication

### External Service Security  
- API keys stored in environment variables
- Webhook signature validation for Twilio callbacks
- TLS encryption for all external API communication
- Audit logging for all external service interactions

## Performance Optimization

### Database Performance
- Connection pooling for efficient resource utilization
- Database indexes on frequently queried columns
- Query optimization with SQLAlchemy query analysis
- Async database operations to prevent blocking

### API Performance
- Response caching for frequently requested data
- Background task processing for long-running operations
- Pagination for large data sets
- Database connection sharing across requests

### Frontend Performance
- Code splitting for reduced initial bundle size
- Image optimization and lazy loading
- WebSocket connection management for real-time updates
- Client-side caching with React Query

This technical plan provides a comprehensive foundation for building the voice agent platform with TDD methodology, ensuring robust testing coverage and maintainable code architecture.