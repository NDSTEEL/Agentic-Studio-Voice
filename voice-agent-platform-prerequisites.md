# Voice Agent Platform - Project Prerequisites

## Google Cloud Setup

### Required Google Cloud Services
- **Google Cloud Project** with billing enabled
- **Vertex AI API** enabled
- **Cloud Storage** bucket for data persistence
- **Cloud Run** for agent deployment
- **Cloud SQL** (PostgreSQL) for application data
- **Cloud Memorystore** (Redis) for caching and sessions

### Authentication Setup
```bash
# Install and configure gcloud CLI
curl https://sdk.cloud.google.com | bash
gcloud init
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Service Account Creation
```bash
# Create service account for ADK agents
gcloud iam service-accounts create voice-agent-platform \
    --display-name="Voice Agent Platform Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:voice-agent-platform@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download service account key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=voice-agent-platform@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## External API Accounts Required

### ElevenLabs
- **Enterprise Account** required for agent creation API
- **API Key** with agent management permissions
- **Voice Library** access for custom voices
- **Minimum Credits** for voice generation testing

### Twilio
- **Twilio Account** with phone number provisioning
- **Account SID** and **Auth Token**
- **Phone Number Pool** budget allocated
- **Webhook URL** capability for call routing

### Business Data APIs
- **Google Places API** key with business search quota
- **Google My Business API** (if available)
- **Facebook Graph API** token for business pages
- **Yelp Fusion API** key for business data

## Development Environment

### Python Environment
```bash
# Python 3.11 or higher required
python --version  # Verify >= 3.11
pip install --upgrade pip
pip install google-adk
pip install fastapi uvicorn
pip install sqlalchemy alembic
pip install redis celery
```

### Node.js Environment (for web interface)
```bash
# Node.js 18+ required
node --version  # Verify >= 18
npm install -g pnpm
```

### Database Setup
```bash
# PostgreSQL 15+ for main database
# Redis 7+ for caching and sessions
# Neo4j Community Edition for knowledge graph (optional)
```

## Local Development Tools

### Required Software
- **Docker Desktop** for containerization
- **Git** for version control
- **VS Code** with Python and TypeScript extensions
- **Postman** or **Insomnia** for API testing

### Environment Variables Template
```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS="./service-account-key.json"
GOOGLE_CLOUD_PROJECT="your-project-id"

# ElevenLabs
ELEVENLABS_API_KEY="your-elevenlabs-api-key"
ELEVENLABS_BASE_URL="https://api.elevenlabs.io/v1"

# Twilio
TWILIO_ACCOUNT_SID="your-twilio-account-sid"
TWILIO_AUTH_TOKEN="your-twilio-auth-token"

# Business APIs
GOOGLE_PLACES_API_KEY="your-google-places-key"
FACEBOOK_ACCESS_TOKEN="your-facebook-token"
YELP_API_KEY="your-yelp-api-key"

# Database
DATABASE_URL="postgresql://username:password@localhost:5432/voice_agents"
REDIS_URL="redis://localhost:6379/0"

# Application
SECRET_KEY="your-secret-key"
ENVIRONMENT="development"
DEBUG=true
```

## Project Structure Requirements

### Directory Layout
```
voice-agent-platform/
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Local development services
├── agents/                        # ADK agents
├── tools/                         # ADK tools
├── database/                      # Database schemas and migrations
├── web/                          # Next.js frontend
├── tests/                        # Test suites
├── docs/                         # Documentation
└── scripts/                      # Deployment and utility scripts
```

## Testing Prerequisites

### Test Data Requirements
- **Sample business listings** for discovery testing
- **Mock API responses** for external service testing
- **Test phone numbers** for Twilio integration
- **Voice samples** for ElevenLabs testing

### Testing Tools
```bash
pip install pytest pytest-asyncio
pip install httpx  # For API testing
pip install factory-boy  # For test data generation
```

## Database Schema Prerequisites

### Required Tables Structure
- **Users** - Authentication and account management
- **Agents** - Voice agent configurations and metadata
- **Phone Numbers** - Twilio number assignments and status
- **Calls** - Call logs, recordings, and transcripts
- **Business Data** - Discovered business information
- **Analytics** - Metrics and performance data
- **Billing** - Usage tracking and payments

## Security Requirements

### SSL/TLS Certificates
- **Domain ownership** for webhook endpoints
- **SSL certificate** for production deployment
- **Webhook security** tokens configured

### API Security
- **Rate limiting** configuration
- **API key rotation** strategy
- **Input validation** schemas
- **CORS policy** configuration

## Monitoring and Observability

### Required Monitoring Stack
- **Cloud Monitoring** for infrastructure metrics
- **Cloud Logging** for application logs
- **Error Reporting** for exception tracking
- **Performance monitoring** for API response times

## Pre-Development Checklist

- [ ] Google Cloud project created and billing enabled
- [ ] All required APIs enabled in Google Cloud Console
- [ ] Service account created with proper permissions
- [ ] ElevenLabs Enterprise account and API key obtained
- [ ] Twilio account with phone number provisioning capability
- [ ] Business API keys (Google Places, Facebook, Yelp) obtained
- [ ] Development environment (Python 3.11+, Node.js 18+) installed
- [ ] Database services (PostgreSQL, Redis) running locally
- [ ] Environment variables configured
- [ ] SSL certificates obtained for production domain
- [ ] Monitoring and logging configured
- [ ] Test data and mock services prepared

## Cost Considerations

### Google Cloud Monthly Estimates
- **Vertex AI API calls**: $0.002 per request
- **Cloud Run**: $0.40 per vCPU-second
- **Cloud SQL**: $25+ per month for small instance
- **Cloud Storage**: $0.023 per GB per month

### External API Costs
- **ElevenLabs**: $0.18-0.30 per 1K characters
- **Twilio**: $1.15 per phone number + $0.0085 per minute
- **Google Places API**: $2-17 per 1K requests
- **Business API usage**: Variable by provider

### Infrastructure Scaling
- **Development**: $50-100/month
- **Production**: $200-500/month (depending on usage)
- **Enterprise Scale**: $1000+/month