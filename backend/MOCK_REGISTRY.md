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