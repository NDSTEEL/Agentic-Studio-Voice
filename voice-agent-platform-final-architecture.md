# Voice Agent Platform - Final Architecture Plan
## Full-Featured Implementation Using Google ADK

---

## 🎯 CONFIRMED DECISIONS

### **Complete Tech Stack**
```yaml
Core Platform:
  Framework: Google ADK (Python)
  Agent Runtime: Vertex AI Agent Engine
  LLM: Gemini 2.0 Flash
  
Backend Services:
  API Layer: FastAPI (auto-generated from ADK)
  Database: PostgreSQL with row-level security
  Caching: Redis (session management)
  
Frontend Application:
  Framework: Next.js with TypeScript
  UI Components: React with Tailwind CSS
  Real-time: WebSocket client (ADK built-in server)
  
Infrastructure:
  Hosting: Google Cloud Platform
  Agent Deployment: Vertex AI Agent Engine
  Database: Cloud SQL PostgreSQL
  Caching: Cloud Memorystore Redis
```

### **ADK Agent Architecture** (5 Agents)
```python
# Agent Communication via ADK Agent2Agent protocol
agents = {
    "orchestrator": LlmAgent(name="orchestrator", tools=[coordinate_workflow]),
    "classifier": LlmAgent(name="classifier", tools=[industry_classification]),
    "extractor": LlmAgent(name="extractor", tools=[web_scraper, db_writer]),
    "validator": LlmAgent(name="validator", tools=[hitl_interface, gap_detector]),
    "deployer": LlmAgent(name="deployer", tools=[elevenlabs_api, twilio_api])
}

# Workflow coordination
workflow = SequentialWorkflow([
    agents["classifier"],
    agents["extractor"], 
    agents["validator"],
    agents["deployer"]
], orchestrator=agents["orchestrator"])
```

### **Database Schema with Versioning**
```sql
-- Multi-tenant foundation
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    white_label_config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge base with version control
CREATE TABLE main_knowledge_bases (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    business_name VARCHAR(255),
    industry_type VARCHAR(100),
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'building',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 18 knowledge nodes with versioning
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY,
    kb_id UUID REFERENCES main_knowledge_bases(id),
    node_type INTEGER CHECK (node_type BETWEEN 1 AND 18),
    node_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    data_sources JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_verified TIMESTAMP
);

-- Voice agents
CREATE TABLE voice_agents (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    kb_id UUID REFERENCES main_knowledge_bases(id),
    name VARCHAR(255),
    elevenlabs_agent_id VARCHAR(255),
    phone_number VARCHAR(20),
    twilio_phone_sid VARCHAR(255),
    template_config JSONB,
    user_instructions JSONB,
    status VARCHAR(20) DEFAULT 'building',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Row-level security for multi-tenancy
ALTER TABLE knowledge_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_kb ON knowledge_nodes 
    USING (kb_id IN (SELECT id FROM main_knowledge_bases WHERE tenant_id = current_setting('app.current_tenant')::UUID));
    
CREATE POLICY tenant_isolation_agents ON voice_agents 
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### **Real-Time Progress System**
```python
# ADK built-in WebSocket support
from google.adk import Agent, WebSocketHandler

class ProgressBroadcaster:
    def __init__(self):
        self.ws_handler = WebSocketHandler()
    
    async def broadcast_progress(self, tenant_id: str, workflow_id: str, 
                               stage: str, progress: int, details: dict = None):
        progress_data = {
            'workflow_id': workflow_id,
            'stage': stage,
            'progress': progress,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        
        # Broadcast to tenant-specific WebSocket connections
        await self.ws_handler.broadcast_to_tenant(tenant_id, progress_data)

# Progress stages for 3-minute workflow
WORKFLOW_STAGES = [
    {'name': 'business_classification', 'duration': 15},    # 15 seconds
    {'name': 'data_extraction', 'duration': 60},           # 1 minute  
    {'name': 'confidence_scoring', 'duration': 30},        # 30 seconds
    {'name': 'knowledge_compilation', 'duration': 30},     # 30 seconds
    {'name': 'hitl_validation', 'duration': 0},           # User dependent
    {'name': 'phone_provisioning', 'duration': 15},       # 15 seconds
    {'name': 'agent_deployment', 'duration': 20},         # 20 seconds
    {'name': 'activation', 'duration': 10}                # 10 seconds
]
# Total automated time: ~3 minutes
```

### **Template System (Placeholder)**
```python
# Simple template structure until full system designed
class AgentTemplate:
    def __init__(self, industry_type: str = "general"):
        self.template = {
            "system_prompt": self._get_system_prompt(industry_type),
            "safety_rules": self._get_safety_rules(),
            "knowledge_context": "{agent_kb_data}",  # Populated from 18 nodes
            "user_instructions": "{user_custom_instructions}",
            "voice_settings": self._get_voice_defaults(industry_type)
        }
    
    def compile(self, kb_data: dict, user_instructions: str) -> str:
        """Compile template with actual data"""
        return self.template["system_prompt"].format(
            business_name=kb_data.get("company_profile", {}).get("name", ""),
            knowledge_context=self._format_kb_for_agent(kb_data),
            user_instructions=user_instructions
        )
    
    def _get_system_prompt(self, industry: str) -> str:
        base = "You are a professional voice assistant for {business_name}."
        industry_specific = {
            "restaurant": "You help with reservations, menu questions, and orders.",
            "legal": "You provide general information but never legal advice.", 
            "medical": "You help with appointments but never medical advice."
        }
        return f"{base} {industry_specific.get(industry, '')}"
```

### **Inter-Agent Communication Flow**
```python
# ADK Agent2Agent workflow
async def create_voice_agent_workflow(business_url: str, tenant_id: str):
    
    # Step 1: Orchestrator starts workflow
    orchestrator = agents["orchestrator"]
    workflow_id = await orchestrator.start_workflow(business_url, tenant_id)
    
    # Step 2: Classification agent detects industry
    classification = await agents["classifier"].classify_business(business_url)
    await orchestrator.update_progress(workflow_id, "business_classification", 10)
    
    # Step 3: Extraction agent scrapes data
    extracted_data = await agents["extractor"].extract_knowledge(
        business_url, classification.industry_type
    )
    await orchestrator.update_progress(workflow_id, "data_extraction", 50)
    
    # Step 4: Validator creates HITL interface
    validation_ui = await agents["validator"].create_validation_interface(
        extracted_data, classification.industry_type
    )
    await orchestrator.update_progress(workflow_id, "hitl_validation", 70)
    
    # Step 5: User completes validation (external)
    # ... user interaction happens in Next.js frontend ...
    
    # Step 6: Deployer creates voice agent
    voice_agent = await agents["deployer"].create_elevenlabs_agent(
        validated_data, phone_number, template
    )
    await orchestrator.update_progress(workflow_id, "agent_deployment", 90)
    
    # Step 7: Activation and monitoring
    await agents["deployer"].activate_agent(voice_agent.id)
    await orchestrator.update_progress(workflow_id, "activation", 100)
    
    return voice_agent
```

## 🚀 DEVELOPMENT SEQUENCE

### **Phase 1: Foundation (Week 1)**
1. **ADK Environment Setup** - Development environment + basic agent
2. **Database Schema** - Create all tables with versioning
3. **FastAPI Integration** - Connect ADK agents to web API
4. **WebSocket Setup** - Real-time progress broadcasting

### **Phase 2: Core Agents (Week 2)**
1. **Orchestrator Agent** - Workflow coordination and progress tracking
2. **Classification Agent** - Industry detection (start with hardcoded)
3. **Extraction Agent** - Web scraping + database storage
4. **Template System** - Basic placeholder implementation

### **Phase 3: User Interface (Week 3)**
1. **Next.js Frontend** - Dashboard with real-time progress
2. **HITL Validation UI** - Progressive disclosure interface
3. **Agent Management** - Create, edit, monitor voice agents
4. **Multi-tenant Authentication** - User management system

### **Phase 4: External Integrations (Week 4)**
1. **ElevenLabs Integration** - Voice agent creation API
2. **Twilio Integration** - Phone number management
3. **End-to-end Testing** - Full workflow validation
4. **Production Deployment** - Vertex AI Agent Engine setup

## ✅ SUCCESS CRITERIA

- **Sub-3-minute agent creation** from URL to live phone number
- **Real-time progress updates** during workflow execution  
- **Multi-tenant data isolation** with row-level security
- **Version-controlled knowledge base** with change tracking
- **ADK agent communication** via Agent2Agent protocol
- **Scalable WebSocket** progress broadcasting
- **Template placeholder system** ready for your design

---

**This plan implements the full-featured system using ADK's built-in capabilities rather than artificial simplifications. Ready for your serious question!**