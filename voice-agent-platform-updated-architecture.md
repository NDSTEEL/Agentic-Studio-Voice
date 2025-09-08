# Voice Agent Platform - Updated Architecture with FastAPI MCP
## Final Implementation Plan

---

## 🎯 **SIMPLIFIED ARCHITECTURE**

### **Core Stack with FastAPI MCP Integration**
```yaml
Agent Layer:
  - Google ADK (Python) - 5 specialized agents
  - Vertex AI Agent Engine - managed runtime

Communication Layer:
  - FastAPI MCP - standardized ADK ↔ backend bridge
  - MCP Protocol - tool interfaces and context management
  - WebSocket - real-time progress (built into MCP)

Backend Services:
  - FastAPI - web API with MCP tools
  - PostgreSQL - multi-tenant database
  - Redis - session caching

Frontend:
  - Next.js - user dashboard  
  - React - HITL validation UI
  - WebSocket client - real-time updates

External APIs:
  - ElevenLabs - voice agents (via MCP tools)
  - Twilio - phone numbers (via MCP tools)
  - Industry APIs - classification (via MCP tools)
```

---

## 🏗️ **ADK AGENTS WITH MCP INTEGRATION**

### **Agent Architecture**
```python
# 5 ADK Agents calling FastAPI MCP tools
agents = {
    "orchestrator": LlmAgent(
        name="orchestrator", 
        tools=[mcp_progress_tracker, mcp_workflow_manager]
    ),
    "classifier": LlmAgent(
        name="classifier",
        tools=[mcp_industry_detector, mcp_template_loader]
    ), 
    "extractor": LlmAgent(
        name="extractor",
        tools=[mcp_web_scraper, mcp_kb_storage]
    ),
    "validator": LlmAgent(
        name="validator", 
        tools=[mcp_hitl_interface, mcp_gap_detector]
    ),
    "deployer": LlmAgent(
        name="deployer",
        tools=[mcp_elevenlabs_creator, mcp_twilio_manager]
    )
}
```

### **MCP Tools (FastAPI Backend)**
```python
# Standardized tool interfaces
@mcp_tool
async def extract_business_data(url: str, tenant_id: str) -> dict:
    # Web scraping + 18 node extraction
    # Multi-tenant database storage
    return extracted_nodes

@mcp_tool  
async def create_elevenlabs_agent(kb_data: dict, template: dict) -> str:
    # ElevenLabs API integration
    # Agent configuration compilation
    return agent_id

@mcp_tool
async def provision_phone_number(area_code: str, tenant_id: str) -> str:
    # Twilio API integration
    # Multi-tenant number assignment
    return phone_number

@mcp_tool
async def broadcast_progress(workflow_id: str, stage: str, progress: int):
    # Real-time WebSocket updates
    # Tenant-specific progress tracking
    await websocket_manager.broadcast_to_tenant(tenant_id, progress_data)
```

---

## 📊 **DATABASE SCHEMA (Unchanged)**

```sql
-- Multi-tenant foundation
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    white_label_config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge base with versioning
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY,
    kb_id UUID REFERENCES main_knowledge_bases(id),
    node_type INTEGER CHECK (node_type BETWEEN 1 AND 18),
    node_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Voice agents
CREATE TABLE voice_agents (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    elevenlabs_agent_id VARCHAR(255),
    phone_number VARCHAR(20),
    status VARCHAR(20) DEFAULT 'building'
);

-- Row-level security for multi-tenancy
ALTER TABLE knowledge_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;
```

---

## 🔄 **WORKFLOW WITH MCP INTEGRATION**

### **Complete Agent Creation Flow**
```python
# ADK Orchestrator coordinates via MCP tools
async def create_voice_agent_workflow(business_url: str, tenant_id: str):
    
    # Step 1: Industry classification
    industry_data = await mcp_client.call("detect_industry", {
        "url": business_url,
        "tenant_id": tenant_id
    })
    
    # Step 2: Knowledge extraction  
    knowledge_nodes = await mcp_client.call("extract_business_data", {
        "url": business_url,
        "industry": industry_data.type,
        "tenant_id": tenant_id
    })
    
    # Step 3: HITL validation
    validation_url = await mcp_client.call("create_validation_interface", {
        "extracted_data": knowledge_nodes,
        "tenant_id": tenant_id
    })
    # User interaction happens in Next.js frontend
    
    # Step 4: Phone number provisioning
    phone_number = await mcp_client.call("provision_phone_number", {
        "tenant_id": tenant_id,
        "preferences": user_phone_preferences
    })
    
    # Step 5: Voice agent deployment
    agent_id = await mcp_client.call("create_elevenlabs_agent", {
        "kb_data": validated_knowledge,
        "phone_number": phone_number,
        "tenant_id": tenant_id
    })
    
    # Step 6: Activation
    await mcp_client.call("activate_voice_agent", {
        "agent_id": agent_id,
        "phone_number": phone_number
    })
    
    return {"agent_id": agent_id, "phone_number": phone_number}
```

---

## 🚀 **DEVELOPMENT SEQUENCE (Updated)**

### **Phase 1: MCP Foundation (Week 1)**
1. **Setup FastAPI MCP** in Agentic-Studio-Voice repository
2. **Define MCP tools** for all external integrations
3. **Database schema** with multi-tenant setup  
4. **Basic ADK agent** calling MCP tools

### **Phase 2: Core MCP Tools (Week 2)**
1. **Web scraping MCP tool** - business data extraction
2. **Database MCP tools** - knowledge node storage/retrieval
3. **Progress tracking MCP tool** - real-time WebSocket updates
4. **Industry classification MCP tool** - business categorization

### **Phase 3: External API MCP Tools (Week 3)**
1. **ElevenLabs MCP tool** - voice agent creation
2. **Twilio MCP tool** - phone number management  
3. **Template compilation MCP tool** - agent configuration
4. **End-to-end testing** via MCP protocol

### **Phase 4: UI and Integration (Week 4)**
1. **Next.js frontend** connecting to MCP WebSocket tools
2. **HITL validation interface** using MCP validation tools
3. **Agent management dashboard** via MCP agent tools
4. **Production deployment** with CI/CD workflows

---

## ⚡ **KEY ADVANTAGES OF MCP INTEGRATION**

### **Simplified Development:**
```yaml
Before MCP:
  - Custom ADK bridges: 1 week
  - Custom WebSocket handling: 3 days  
  - Custom tool interfaces: 1 week
  - Error handling/retry: 3 days
  Total: 2.5 weeks

With FastAPI MCP:  
  - MCP tool definitions: 3 days
  - Integration setup: 1 day
  Total: 1 week

Time Saved: 1.5 weeks
```

### **Better Architecture:**
- **Standardized communication** between ADK agents and backend
- **Built-in context management** for multi-tenant operations
- **Automatic error handling** and retry mechanisms  
- **Type-safe tool interfaces** with documentation
- **Real-time capabilities** built into MCP protocol

---

## 📋 **SUCCESS CRITERIA (Unchanged)**

- **Sub-3-minute agent creation** from URL to live phone number
- **Multi-tenant data isolation** with row-level security  
- **Real-time progress updates** via MCP WebSocket tools
- **18 knowledge nodes** extracted and stored per agent
- **External API integration** via standardized MCP tools
- **Scalable architecture** supporting thousands of tenants

---

## 🔧 **IMMEDIATE NEXT STEPS**

1. **Set up FastAPI MCP** in GitHub repository
2. **Install Spec Kit** for automated requirements management
3. **Create MCP tool stubs** for all major integrations  
4. **Build first ADK agent** using MCP protocol
5. **Test MCP communication** end-to-end

**Ready to start building with this simplified, MCP-powered architecture!**