# Mock Registry - Technical Debt Tracker

## Purpose
Track all mocked components that need real implementations before production.

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