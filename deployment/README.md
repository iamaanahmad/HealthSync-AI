# HealthSync Agentverse Deployment

This directory contains all the scripts and tools needed to deploy HealthSync agents to Agentverse with full ASI:One integration for the ASI Alliance Hackathon.

## Overview

The deployment process consists of several phases:
1. **Agent Registration** - Register all agents on Agentverse with proper manifests
2. **Chat Protocol Setup** - Enable Chat Protocol for ASI:One compatibility
3. **Health Monitoring** - Setup continuous health monitoring and alerting
4. **ASI:One Verification** - Verify agents are discoverable through ASI:One interface
5. **Final Validation** - Comprehensive validation of all requirements

## Files

### Core Deployment Scripts

- **`complete_deployment.py`** - Main orchestrator for the entire deployment process
- **`deploy_to_agentverse.py`** - Handles agent registration and Agentverse deployment
- **`register_agents.py`** - Simplified agent registration script
- **`agentverse_registration.py`** - Core registration manager with API integration

### Monitoring and Verification

- **`agent_monitor.py`** - Health monitoring and status tracking system
- **`verify_asi_one_integration.py`** - ASI:One integration verification
- **`test_deployment.py`** - Test suite for deployment validation

### Documentation

- **`README.md`** - This file
- Generated reports in JSON format after deployment

## Quick Start

### 1. Complete Deployment (Recommended)

Run the complete deployment process:

```bash
python deployment/complete_deployment.py
```

This will:
- Validate all prerequisites
- Register agents on Agentverse
- Setup Chat Protocol integration
- Configure health monitoring
- Verify ASI:One compatibility
- Generate comprehensive reports

### 2. Individual Steps

If you prefer to run individual steps:

```bash
# Test deployment readiness
python deployment/test_deployment.py

# Register agents only
python deployment/register_agents.py

# Verify ASI:One integration
python deployment/verify_asi_one_integration.py

# Monitor agent health
python deployment/agent_monitor.py --demo
```

## Prerequisites

### 1. Agent Manifests

Ensure all agent manifests are properly configured in `agents/manifests/`:
- `patient_consent_manifest.json`
- `data_custodian_manifest.json`
- `research_query_manifest.json`
- `privacy_manifest.json`
- `metta_integration_manifest.json`

Each manifest must include:
```json
{
  "badges": ["Innovation Lab", "ASI Alliance Hackathon"],
  "chat_protocol_enabled": true,
  "agentverse_compatible": true
}
```

### 2. Agent Implementations

All agent implementations must be present in their respective directories:
- `agents/patient_consent/agent.py`
- `agents/data_custodian/agent.py`
- `agents/research_query/agent.py`
- `agents/privacy/agent.py`
- `agents/metta_integration/agent.py`

### 3. Dependencies

Install required dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configuration

Update `config.py` with appropriate settings:
- Agent ports and endpoints
- Agentverse API configuration
- Health monitoring settings

## Deployment Process Details

### Phase 1: Pre-deployment Checks

- Validates agent manifests exist and are properly formatted
- Checks agent implementations are present
- Verifies configuration settings
- Confirms all dependencies are installed

### Phase 2: Agent Registration

- Registers each agent on Agentverse with proper manifests
- Configures Chat Protocol integration
- Sets up agent discovery endpoints
- Generates agent IDs and URLs

### Phase 3: ASI:One Verification

- Verifies Chat Protocol is properly enabled
- Checks agent discovery through Agentverse
- Validates required badges are present
- Tests ASI:One URL accessibility

### Phase 4: Health Monitoring

- Sets up HTTP health check endpoints for each agent
- Configures continuous monitoring system
- Implements alerting for agent failures
- Provides real-time status dashboard

### Phase 5: Final Validation

- Comprehensive validation of all requirements
- Checks hackathon compliance criteria
- Generates final readiness report
- Provides troubleshooting guidance

## Health Check Endpoints

Each agent exposes HTTP endpoints for monitoring:

- **Health Check**: `http://localhost:{port+1000}/health`
- **Agent Info**: `http://localhost:{port+1000}/info`
- **Status**: `http://localhost:{port+1000}/status`
- **Metrics**: `http://localhost:{port+1000}/metrics`

Example for Patient Consent Agent (port 8001):
- Health: `http://localhost:9001/health`
- Status: `http://localhost:9001/status`

## ASI:One Integration

### Chat Protocol

All agents are configured with Chat Protocol support for ASI:One compatibility:
- Natural language message processing
- Session management
- Structured response formatting
- Error handling and acknowledgments

### Agent Discovery

Agents are discoverable through ASI:One interface at:
- **ASI:One Chat**: `https://asi.one/chat/{agent_id}`
- **ASI:One Agent**: `https://asi.one/agents/{agent_id}`

### Required Badges

All agents include required hackathon badges:
- **Innovation Lab** - For categorization
- **ASI Alliance Hackathon** - For hackathon identification

## Monitoring and Alerting

### Health Monitoring

The system provides continuous health monitoring with:
- Real-time agent status tracking
- Response time monitoring
- Error rate calculation
- Uptime percentage tracking

### Alert Conditions

Alerts are triggered for:
- Consecutive health check failures (≥3)
- High error rates (>10%)
- Extended downtime
- Communication failures

### Monitoring Dashboard

Access the monitoring dashboard through:
- Agent status endpoints
- Health check URLs
- Generated monitoring reports

## Troubleshooting

### Common Issues

1. **Agent Registration Fails**
   - Check network connectivity
   - Verify Agentverse API credentials
   - Validate agent manifest format

2. **Chat Protocol Not Working**
   - Ensure `chat_protocol_enabled: true` in manifests
   - Check agent Chat Protocol implementation
   - Verify ASI:One compatibility settings

3. **Health Checks Failing**
   - Confirm agents are running
   - Check port availability
   - Verify HTTP endpoint configuration

4. **ASI:One Discovery Issues**
   - Validate agent registration on Agentverse
   - Check badge configuration
   - Verify agent metadata

### Getting Help

1. Run the test suite: `python deployment/test_deployment.py`
2. Check generated reports in `deployment/` directory
3. Review agent logs in `logs/` directory
4. Verify configuration in `config.py`

## Generated Reports

After deployment, several reports are generated:

- **`complete_deployment_report.json`** - Comprehensive deployment status
- **`agentverse_registration_report.json`** - Registration details
- **`asi_one_verification_report.json`** - ASI:One compliance status
- **`agent_monitoring_report.json`** - Health monitoring results
- **`final_deployment_report.json`** - Final validation and readiness

## Hackathon Compliance

The deployment ensures full compliance with ASI Alliance Hackathon requirements:

✅ **uAgents Framework** - All agents built with uAgents  
✅ **Agentverse Registration** - Agents registered with proper manifests  
✅ **Chat Protocol** - ASI:One compatibility enabled  
✅ **MeTTa Integration** - Knowledge graph reasoning implemented  
✅ **Innovation Lab** - Proper categorization and badges  

## Next Steps

After successful deployment:

1. **Test Agent Interactions** - Verify multi-agent workflows
2. **Demo Preparation** - Prepare demonstration scenarios
3. **Performance Testing** - Test under load conditions
4. **Documentation** - Update project documentation
5. **Video Creation** - Record demonstration video

## Support

For deployment issues or questions:
- Check the troubleshooting section above
- Review generated error reports
- Examine agent logs for detailed error information
- Verify all prerequisites are met