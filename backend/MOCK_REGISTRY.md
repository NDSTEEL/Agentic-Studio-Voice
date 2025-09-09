# Mock Registry - Technical Debt Tracker

## Purpose
Track all mocked components that need real implementations before production.

**Total Mocks:** 26 items across 11 tasks
**Latest Update:** T012 - Added knowledge base services (3 new mocks)

## Mocks to Replace

### T006: Tenant Management API - 6 mocks documented
**File:** `tests/unit/test_tenant_management.py`

- [ ] **TenantService.create_tenant** (line 257)
  - **Why mocked:** No test database available in unit tests
  - **Task to fix:** Create integration tests with test database setup
  - **Impact:** Creates fake tenant data, bypasses real database validation

- [ ] **TenantService.get_tenant** (line 288)  
  - **Why mocked:** No test database available in unit tests
  - **Task to fix:** Create integration tests with test database setup
  - **Impact:** Returns fake tenant data, bypasses real database queries

- [ ] **TenantService.get_tenant (404 case)** (line 317)
  - **Why mocked:** No test database available in unit tests  
  - **Task to fix:** Create integration tests with test database setup
  - **Impact:** Simulates missing tenant, doesn't test real database behavior

- [ ] **TenantService.update_tenant** (line 334)
  - **Why mocked:** No test database available in unit tests
  - **Task to fix:** Create integration tests with test database setup
  - **Impact:** Updates fake tenant data, bypasses real database transactions

- [ ] **TenantService.list_tenants** (line 366)
  - **Why mocked:** No test database available in unit tests
  - **Task to fix:** Create integration tests with test database setup
  - **Impact:** Returns fake tenant list, bypasses real pagination logic

- [ ] **Authentication middleware** (line 409)
  - **Why mocked:** Authentication middleware not yet implemented in T006
  - **Task to fix:** Implement authentication middleware and update test
  - **Impact:** Bypasses security, allows unauthenticated requests

### Integration Test Requirements
- [ ] Create `docker-compose.test.yml` with test PostgreSQL database
- [ ] Add integration test suite in `tests/integration/`
- [ ] Test real database transactions, rollbacks, constraints
- [ ] Test authentication middleware with real JWT tokens
- [ ] Test error cases with real database failures

### T007: Basic Frontend Setup - 7 mocks documented
**Files:** Multiple frontend files in `../frontend/src/`

- [ ] **React entry point** (`src/main.tsx`)
  - **Why mocked:** Next.js uses different entry point structure
  - **Task to fix:** Remove Vite-style entry point, use Next.js App Router properly
  - **Impact:** Creates unnecessary React entry point that conflicts with Next.js

- [ ] **React App component** (`src/App.tsx`)
  - **Why mocked:** Next.js uses file-based routing, not React Router
  - **Task to fix:** Remove React Router, use Next.js App Router file structure
  - **Impact:** Adds unnecessary routing layer on top of Next.js

- [ ] **API base configuration** (`src/services/api.ts`)
  - **Why mocked:** No real backend API integration configured
  - **Task to fix:** Connect to real backend API, add proper error handling
  - **Impact:** API calls fail gracefully but don't connect to real services

- [ ] **Mock auth token handling** (`src/services/api.ts`)
  - **Why mocked:** Authentication system not yet implemented
  - **Task to fix:** Implement real JWT/session authentication flow
  - **Impact:** All requests bypass authentication security

- [ ] **Mock logout flow** (`src/services/api.ts`)
  - **Why mocked:** Authentication system not yet implemented
  - **Task to fix:** Implement real logout with session cleanup
  - **Impact:** Security risk - improper session termination

- [ ] **Tenant service API calls** (`src/services/tenantService.ts`)
  - **Why mocked:** Backend API endpoints not fully connected
  - **Task to fix:** Connect to real backend tenant management endpoints
  - **Impact:** CRUD operations return mock data instead of real database results

- [ ] **Vite configuration** (`vite.config.ts`)
  - **Why mocked:** Project uses Next.js, not Vite
  - **Task to fix:** Remove Vite config, rely on Next.js build system
  - **Impact:** Confusing build configuration that doesn't match project structure

## T012: Knowledge Categories Schema - New Mocks (3 items)

- [ ] **Web Crawler Service** (`src/services/web_crawler_service.py`)
  - **Why mocked:** Real web scraping requires HTTP clients, HTML parsers, rate limiting
  - **Task to fix:** Implement with aiohttp, BeautifulSoup, sitemap.xml parsing
  - **Impact:** Cannot actually crawl business websites for knowledge extraction

- [ ] **Content Extraction Service** (`src/services/content_extraction_service.py`)
  - **Why mocked:** AI-powered content extraction requires LLM integration (OpenAI/Claude)
  - **Task to fix:** Integrate with OpenAI API or local LLM for real NLP processing
  - **Impact:** Knowledge categorization uses simple keyword matching instead of AI

- [ ] **Knowledge Base Management** (`src/services/knowledge_base_service.py`)
  - **Why mocked:** Database operations, compression, and incremental updates need real persistence
  - **Task to fix:** Connect to PostgreSQL, implement real compression algorithms
  - **Impact:** Knowledge base operations are in-memory only, no actual storage

### T008: Authentication UI - 6 mocks documented  
**Files:** Multiple authentication files in `../frontend/src/`

- [ ] **Authentication service API calls** (`src/services/authService.ts`)
  - **Why mocked:** Backend authentication endpoints not fully implemented
  - **Task to fix:** Connect to real backend auth API with proper JWT handling
  - **Impact:** Login/register return mock users, bypass real authentication security

- [ ] **Mock login/register responses** (`src/services/authService.ts`)
  - **Why mocked:** No real backend user validation or database integration
  - **Task to fix:** Implement real user validation, password hashing, database storage
  - **Impact:** Any email/password combination accepted, no real user accounts created

- [ ] **Mock current user endpoint** (`src/services/authService.ts`)
  - **Why mocked:** No real user session management or JWT verification
  - **Task to fix:** Implement real JWT verification and user session management
  - **Impact:** Always returns mock user data, doesn't verify real authentication state

- [ ] **Token storage security** (`src/utils/tokenStorage.ts`)
  - **Why mocked:** Using localStorage instead of secure httpOnly cookies
  - **Task to fix:** Implement secure token storage with httpOnly cookies and CSRF protection
  - **Impact:** Security risk - tokens accessible to JavaScript, vulnerable to XSS

- [ ] **Auth context state management** (`src/contexts/AuthContext.tsx`)
  - **Why mocked:** Simplified authentication state without proper error handling
  - **Task to fix:** Add comprehensive error handling, token refresh, and logout cleanup
  - **Impact:** Basic auth state management without robust error recovery

- [ ] **Next.js middleware JWT verification** (`middleware.ts`)
  - **Why mocked:** Mock token validation instead of real JWT signature verification
  - **Task to fix:** Implement proper JWT signature verification with backend secret
  - **Impact:** Security risk - any token format accepted, no real verification

### T009: Docker Development Environment - 2 mocks documented
**Files:** Docker configuration files

- [ ] **Development Dockerfiles** (`backend/Dockerfile.dev`, `frontend/Dockerfile.dev`)
  - **Why mocked:** Development-focused containers, not production optimized
  - **Task to fix:** Create separate production Dockerfiles with multi-stage builds and security hardening
  - **Impact:** Development containers include debugging tools, run as non-root for dev convenience

- [ ] **Environment configuration** (`.env.docker`, `backend/.env.example`)
  - **Why mocked:** Uses development credentials and localhost configurations
  - **Task to fix:** Implement proper secret management, environment-specific configurations
  - **Impact:** Development secrets exposed, not suitable for production deployment

### T010: CI/CD Pipeline Setup - 0 mocks documented
**Files:** GitHub Actions workflow and configuration files

- ✅ **No mocks created** - T010 implemented real CI/CD infrastructure
  - **Created:** GitHub Actions workflows, Dependabot configuration, linting/formatting setup
  - **Real implementation:** Complete automated testing and quality checks pipeline
  - **Impact:** Production-ready CI/CD system with security scanning and automated dependency updates

### T011: Voice Agent Model & API - 2 mocks documented
**Files:** Multiple voice agent components and API endpoints

- [ ] **Authentication middleware** (`src/api/dependencies/auth.py`)
  - **Why mocked:** JWT token validation not fully implemented yet
  - **Task to fix:** Implement real JWT signature verification and user session validation
  - **Impact:** All API requests bypass proper authentication - security risk in production

- [ ] **Database session** (`src/database/connection.py:get_db_session`)
  - **Why mocked:** Returns None instead of real database connection for testing
  - **Task to fix:** Connect to real PostgreSQL database with proper session management
  - **Impact:** All voice agent CRUD operations use mocked data - no persistent storage

### T00X: [Future Tasks]
*Mocks from future tasks will be documented here*

## Safe Mocks (Keep)
- ✅ External APIs (Twilio, ElevenLabs) for unit tests
- ✅ DateTime.now() for consistent testing  
- ✅ Random generators for deterministic tests
- ✅ UUID generation for predictable test data

## Production Readiness Checklist
Before deploying to production, verify:
- [ ] All database mocks replaced with integration tests
- [ ] Authentication middleware implemented and tested
- [ ] Real database error handling tested
- [ ] Transaction rollback behavior verified
- [ ] Performance tested with real database connections