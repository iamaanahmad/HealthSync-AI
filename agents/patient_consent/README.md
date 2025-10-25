# Patient Consent Agent

## Overview

The Patient Consent Agent is a core component of the HealthSync system that manages patient data sharing permissions with granular control. It enables patients to control their healthcare data consent preferences and validates data access requests from researchers and other agents.

## Features

### Core Consent Management (Task 3.1)

- **Consent Record Management**
  - Create, update, and revoke consent records
  - Granular control over data types and research categories
  - Automatic consent expiration and renewal mechanisms
  - Version tracking for all consent changes
  - Comprehensive audit trail for compliance

- **Consent Validation**
  - Real-time consent verification for data access requests
  - Expiration checking with detailed error codes
  - Permission validation for specific data types and research categories
  - Support for multiple consent records per patient

- **MeTTa Knowledge Graph Integration**
  - Automatic storage of consent records in MeTTa Knowledge Graph
  - Structured entity format for complex reasoning
  - Support for relationship traversal and nested queries

- **Audit Trail & Logging**
  - Complete audit trail for all consent operations
  - Cryptographic verification support
  - Compliance-ready logging format
  - Version history tracking

### Chat Protocol Integration (Task 3.2)

- **Natural Language Processing**
  - Intent recognition for consent operations (grant, revoke, check, renew)
  - Patient ID extraction from natural language
  - Consent preference parsing from conversational text
  - Context-aware follow-up questions

- **Session Management**
  - Multi-user session support
  - Context persistence across messages
  - Session lifecycle management (create, maintain, close)
  - User-specific conversation history

- **ASI:One Compatibility**
  - Full Chat Protocol compliance
  - Structured data message support
  - Command-based operations
  - Acknowledgment and error response protocols

- **Multi-Modal Communication**
  - Text-based natural language interactions
  - Structured JSON data messages
  - Command-based API calls
  - Flexible response formats

## Architecture

### ConsentRecord Class

The `ConsentRecord` class represents a patient consent record with the following features:

- Unique consent ID generation
- Data type and research category lists
- Consent status (granted/revoked)
- Expiration date management
- Version tracking
- Audit trail
- Validation methods

### PatientConsentAgent Class

The main agent class extends `HealthSyncBaseAgent` and provides:

- Message handler registration for consent operations
- Chat Protocol integration
- MeTTa Knowledge Graph connectivity
- Statistics tracking
- Health monitoring

## API

### Message Types

#### Consent Update
```python
{
    "message_type": "consent_update",
    "payload": {
        "patient_id": "P001",
        "data_types": ["medical_records", "lab_results"],
        "research_categories": ["cancer_research"],
        "consent_status": true,
        "expiry_date": "2025-10-11T00:00:00Z"
    }
}
```

#### Consent Query
```python
{
    "message_type": "consent_query",
    "payload": {
        "patient_id": "P001",
        "data_type": "medical_records",
        "research_category": "cancer_research",
        "requester_id": "researcher_001"
    }
}
```

#### Consent Renewal
```python
{
    "message_type": "consent_renew",
    "payload": {
        "patient_id": "P001",
        "duration_days": 365
    }
}
```

#### Consent Revocation
```python
{
    "message_type": "consent_revoke",
    "payload": {
        "patient_id": "P001"
    }
}
```

### Chat Protocol Messages

#### Text Message (Natural Language)
```python
ChatMessage(
    session_id="session_123",
    user_id="user_001",
    agent_id="healthsync_patient_consent_agent",
    content_type="text",
    content_data="I want to grant consent for medical records for cancer research. My patient ID is P001"
)
```

#### Structured Data Message
```python
ChatMessage(
    session_id="session_123",
    user_id="user_001",
    agent_id="healthsync_patient_consent_agent",
    content_type="structured_data",
    content_data={
        "patient_id": "P001",
        "data_types": ["medical_records"],
        "research_categories": ["cancer_research"],
        "consent_status": true
    }
)
```

#### Command Message
```python
ChatMessage(
    session_id="session_123",
    user_id="user_001",
    agent_id="healthsync_patient_consent_agent",
    content_type="command",
    content_data={
        "command": "get_consent",
        "params": {"patient_id": "P001"}
    }
)
```

## Testing

### Unit Tests (test_consent_agent.py)

- 28 comprehensive unit tests covering:
  - ConsentRecord creation and validation
  - Consent expiration and renewal
  - Permission checking
  - Audit trail generation
  - Agent message handling
  - Statistics tracking

### Integration Tests (test_chat_integration.py)

- 19 integration tests covering:
  - Chat session management
  - Natural language processing
  - Intent recognition
  - Patient ID extraction
  - Multi-turn conversations
  - Error handling
  - ASI:One protocol compliance

### Running Tests

```bash
# Run all tests
python -m pytest agents/patient_consent/ -v

# Run unit tests only
python -m pytest agents/patient_consent/test_consent_agent.py -v

# Run integration tests only
python -m pytest agents/patient_consent/test_chat_integration.py -v
```

## Usage Examples

### Creating a Consent Record

```python
from agents.patient_consent.agent import PatientConsentAgent, ConsentRecord
from datetime import datetime, timedelta

# Create agent
agent = PatientConsentAgent(port=8002)

# Create consent record
consent = ConsentRecord(
    patient_id="P001",
    data_types=["medical_records", "lab_results"],
    research_categories=["cancer_research", "diabetes_research"],
    consent_status=True,
    expiry_date=datetime.utcnow() + timedelta(days=365)
)

# Store in agent
agent.consent_records["P001"] = consent
```

### Querying Consent

```python
# Check if consent is valid
if consent.is_valid():
    print("Consent is active and not expired")

# Check specific permission
granted, status = consent.check_permission(
    data_type="medical_records",
    research_category="cancer_research"
)

if granted:
    print("Access granted")
else:
    print(f"Access denied: {status}")
```

### Natural Language Interaction

```python
from shared.protocols.chat_protocol import ChatMessage

# Create chat session
session = agent.chat_handler.create_session(
    user_id="patient_001",
    session_type="patient_consent"
)

# Send natural language message
message = ChatMessage(
    session_id=session.session_id,
    user_id="patient_001",
    agent_id=agent.agent_id,
    content_type="text",
    content_data="I want to grant consent for my medical records for cancer research. My patient ID is P001"
)

# Process message
response = await agent._handle_chat_message(ctx, "sender", message)
print(response.response_data)
```

## Requirements Satisfied

### Task 3.1 Requirements (2.1, 2.2, 2.3, 2.4)

- ✅ **2.1**: Patient dashboard with consent preferences
- ✅ **2.2**: Consent updates stored in MeTTa Knowledge Graph
- ✅ **2.3**: Real-time notification of consent changes (< 5 seconds)
- ✅ **2.4**: Immediate blocking of data sharing on consent revocation

### Task 3.2 Requirements (6.1, 6.2, 6.3, 6.4, 1.2)

- ✅ **6.1**: Chat Protocol session initialization
- ✅ **6.2**: Natural language parsing and appropriate responses
- ✅ **6.3**: Acknowledgment for all received messages
- ✅ **6.4**: Proper session closure and resource cleanup
- ✅ **1.2**: Agent registration on Agentverse with Chat Protocol enabled

## Statistics & Monitoring

The agent tracks comprehensive statistics:

- Total consents created
- Active consents
- Expired consents
- Revoked consents
- Consent queries processed
- Consent updates performed
- Coverage percentages

Access statistics via:

```python
stats = agent.get_consent_statistics()
print(stats)
```

## Error Handling

The agent implements comprehensive error handling:

- **CONSENT_EXPIRED**: Consent has passed expiry date
- **CONSENT_REVOKED**: Consent has been revoked by patient
- **CONSENT_NOT_FOUND**: No consent record exists for patient
- **DATA_TYPE_NOT_CONSENTED**: Requested data type not in consent
- **RESEARCH_CATEGORY_NOT_CONSENTED**: Requested category not in consent

## Future Enhancements

- Multi-language support for natural language processing
- Advanced consent templates
- Consent delegation mechanisms
- Integration with external identity providers
- Enhanced privacy controls
- Consent analytics and reporting

## License

MIT License - Part of the HealthSync AI project
