# Voice Agent Platform - Verified Requirements Only
## Based on User-Approved Specifications & Research

---

## 🎯 PROJECT OVERVIEW

### **Platform Mission** (User-Specified)
Autonomous voice agent platform that creates, deploys, and manages voice agents automatically from business data input. Users provide business URL/information → System delivers live voice agent with phone number in under 3 minutes.

### **Core Innovation** (User-Confirmed)
- **18 Canonical Knowledge Nodes** for comprehensive business data extraction
- **Phone-First Deployment** strategy with ElevenLabs + Twilio integration
- **Multi-tenant SaaS** with white label capabilities
- **HITL Validation** with smart questioning and progressive disclosure
- **Template Compilation System** (specifications pending from user)

---

## 🏗️ VERIFIED ARCHITECTURE

### **Google ADK Framework** (User-Confirmed)
Platform will be built using Google Agent Development Kit (ADK) for multi-agent orchestration.

### **Research-Approved ADK Agent Structure**
Based on approved subagent research findings:

**5 Specialized ADK Agents:**
1. **Orchestrator Agent** - Coordinates entire workflow, manages tenant context
2. **Business Classification Agent** - Industry detection and classification
3. **Knowledge Extraction Agent** - Multi-source data extraction with confidence scoring
4. **Validation Agent** - HITL validation workflow management
5. **Deployment Agent** - ElevenLabs voice agent creation and Twilio integration

### **Research-Approved Supporting Concepts:**
- Multi-tenant data isolation with row-level security
- Real-time progress updates to UI
- Industry classification using commercial APIs with ML fallbacks
- Multi-layer confidence scoring for extracted data

---

## 📊 KNOWLEDGE BASE ARCHITECTURE

### **18 Canonical Knowledge Nodes** (User-Specified)
```yaml
1. company_profile: # Name, locations, hours, mission
2. offerings_catalog: # Products/services with specifications
3. pricing_and_terms: # Prices, discounts, payment terms
4. policies_and_procedures: # Returns, warranties, boundaries
5. operational_knowledge: # SOPs, workflows, decision trees
6. communication_assets: # FAQs, templates, scripts
7. voice_and_verbal: # Pronunciations, variations, lexicon
8. customer_intelligence: # Common questions, pain points
9. competitive_intelligence: # Differentiators, positioning
10. compliance_and_legal: # Regulations, disclaimers
11. technical_specifications: # Integrations, APIs
12. media_and_resources: # Documents, images, links
13. organizational_knowledge: # Team structure, escalation
14. historical_intelligence: # Past issues, patterns
15. metrics_and_goals: # KPIs, SLAs
16. seasonal_and_temporal: # Holidays, events
17. metadata_and_control: # Versions, provenance
18. relationships_and_dependencies: # Cross-references
```

### **Research-Approved Industry-Specific Prioritization**
Different industries require different node priorities:
- **Restaurant**: Focus on profile, menu, pricing, operations, voice
- **Legal**: Emphasize profile, policies, operations, compliance, organization
- **Medical**: Priority on profile, policies, operations, compliance, organization

### **Research-Approved KB Architecture** 
- **Main KB**: Complete business repository with all 18 nodes
- **Agent KB**: Optimized subset for voice agents (5-10 nodes typical)
- Version controlled with change tracking and source attribution

---

## 🔄 HIGH-LEVEL WORKFLOW

### **User-Confirmed Process Flow**
1. **Business Discovery**: User provides business URL or name
2. **Industry Classification**: Automatic industry detection and template loading
3. **Multi-Source Data Extraction**: Web crawling, document parsing, API calls
4. **Confidence Scoring**: Multi-layer algorithm for data validation
5. **HITL Validation**: Progressive disclosure UI for user review and gap filling
6. **Knowledge Compilation**: Create Main KB and Agent KB subset
7. **Phone Number Selection**: User chooses from available numbers
8. **Template Compilation**: Merge user instructions with Agent KB
9. **Single-Shot Deployment**: Complete ElevenLabs configuration and Twilio routing
10. **Go Live**: Agent activation with monitoring

---

## 🎨 WHITE LABEL CAPABILITIES

### **Multi-Tenant Hierarchy** (User-Confirmed)
1. **Platform Super Admin**: Manages entire platform
2. **White Label Master**: Custom branded instances for partners  
3. **Organization Master**: Primary account holder per tenant
4. **Team Users**: Create and manage voice agents
5. **View-Only Users**: Analytics and reporting access

### **White Label Features** (User-Specified)
- Custom domain and branding
- Logo, color scheme, and UI themes
- Custom terms of service and email templates
- Revenue sharing models (60-80% platform margin target)

---

## 💰 BILLING & MONETIZATION

### **User-Confirmed Pricing Tiers**
- **Starter**: $49/month (5 agents, 1000 minutes)
- **Professional**: $149/month (25 agents, 5000 minutes)  
- **Enterprise**: $499/month (unlimited agents, 20000 minutes)
- **White Label**: Custom pricing + revenue share

### **User-Specified Cost Structure**
- Google Cloud: $0.007 per agent interaction
- ElevenLabs: $0.18 per 1K characters
- Twilio: $1.15/month per number + $0.0085/minute
- Target platform margin: 60-80%

---

## 🚀 DEPLOYMENT REQUIREMENTS

### **External Integrations** (User-Confirmed)
- **ElevenLabs**: Enterprise API account for voice agent creation
- **Twilio**: Phone number management and routing
- **Google Cloud Platform**: For ADK deployment and supporting services
- **Payment Processing**: For billing system
- **Commercial APIs**: For industry classification (research-approved)

### **Research-Approved Technology Requirements**
- PostgreSQL for multi-tenant database with row-level security
- Redis for caching and session management
- Real-time communication system for progress updates
- Multi-source data extraction capabilities
- Confidence scoring algorithms for data validation

---

## ✅ SUCCESS CRITERIA

### **User-Confirmed Performance Targets**
- **Agent creation time**: <3 minutes from business input to live agent
- **Multi-tenant isolation**: Complete data separation between tenants
- **External API reliability**: Robust integration with fallback mechanisms
- **Pricing model validation**: 60-80% platform margins achieved
- **White label functionality**: Complete branding customization

---

## 🎯 PENDING ITEMS

### **Awaiting User Input**
1. **Smart Template System Document**: How template compilation actually works
2. **Final Architecture Confirmation**: Approval of research-based 5-agent structure
3. **Development Starting Point**: Which component to build first
4. **Template Dependency Resolution**: How to proceed without template specifications

---

**This document contains ONLY user-specified requirements and research findings that were explicitly approved. All unauthorized technical implementation details have been removed.**