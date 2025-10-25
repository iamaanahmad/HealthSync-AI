# Consent Validation and Data Access Control Implementation

## Overview

This document describes the implementation of consent validation and data access control for the Data Custodian Agent in the HealthSync system. This implementation fulfills task 4.2 of the project specification.

## Implementation Components

### 1. Consent Checking Logic

The Data Custodian Agent implements comprehensive consent checking through the `_verify_patient_consents()` method:

**Key Features:**
- Queries the Patient Consent Agent for each patient in a dataset
- Validates consent for each requested data type
- Checks consent for the specific research category
- Tracks consent failures with detailed reasons
- Calculates consent rate and determines if threshold is met (≥50%)

**Implementation Details:**
```python
async def _verify_patient_consents(self, ctx: Context, dataset_id: str,
                                  data_criteria: Dict[str, Any],
                                  requester_id: str) -> Dict[str, Any]
```

**Returns:**
- `all_consents_valid`: Boolean indicating if consent threshold is met
- `consented_patient_ids`: List of patients who have granted consent
- `consented_count`: Number of patients with valid consent
- `total_count`: Total number of patients in dataset
- `consent_rate`: Percentage of patients with valid consent
- `consent_failures`: List of consent failures with reasons

### 2. Data Request Validation

The `DataAccessAPI` class provides comprehensive request validation:

**Validation Checks:**
- Ethical approval verification
- Research purpose validation (minimum 10 characters)
- Data criteria validation
- Data type validation against available types
- Request structure validation

**Implementation:**
```python
def validate_request(self, request_id: str) -> Tuple[bool, str]
```

### 3. Data Provenance Tracking

The `DataProvenanceTracker` class maintains comprehensive audit trails:

**Tracked Information:**
- Access ID (unique identifier)
- Request ID and requester ID
- Patient IDs accessed
- Data types accessed
- Purpose of access
- Timestamp of access
- Cryptographic hash for verification

**Key Methods:**
- `record_access()`: Records a data access event
- `get_patient_provenance()`: Retrieves provenance for a specific patient
- `get_access_history()`: Retrieves access history with optional filters

**Cryptographic Verification:**
```python
def _generate_access_hash(self, request_id: str, patient_ids: List[str]) -> str:
    """Generate SHA-256 hash for access verification."""
    data_str = f"{request_id}:{'|'.join(sorted(patient_ids))}:{timestamp}"
    return hashlib.sha256(data_str.encode()).hexdigest()
```

### 4. Multi-Agent Communication

The Data Custodian Agent communicates with the Patient Consent Agent through standardized message protocols:

**Communication Flow:**
1. Data Custodian receives data request
2. Validates request structure and criteria
3. Searches for matching datasets
4. For each patient in dataset:
   - Sends `CONSENT_QUERY` message to Patient Consent Agent
   - Receives consent verification response
   - Tracks consent status
5. Aggregates consent results
6. Approves or denies request based on consent threshold

**Message Protocol:**
```python
async def _query_consent_agent(self, ctx: Context, 
                               query_payload: Dict[str, Any]) -> Dict[str, Any]
```

**Audit Logging:**
- Logs consent query sent
- Logs consent response received
- Tracks message IDs for correlation
- Records all consent verification details

### 5. Access Control Workflow

The complete data access workflow with consent validation:

```
1. Researcher submits data request
   ↓
2. Data Custodian validates request structure
   ↓
3. Search for matching datasets
   ↓
4. For each patient in dataset:
   - Query Patient Consent Agent
   - Verify consent for data types
   - Verify consent for research category
   ↓
5. Calculate consent rate
   ↓
6. If consent rate ≥ 50%:
   - Approve request
   - Retrieve consented patient records
   - Record access in provenance tracker
   - Log audit trail
   - Return anonymized data
   Else:
   - Deny request
   - Log denial reason
   - Return consent details
```

## Statistics Tracking

The agent tracks comprehensive statistics:

- `total_requests`: Total data requests received
- `approved_requests`: Requests approved after consent validation
- `denied_requests`: Requests denied due to consent or validation issues
- `consent_checks`: Total number of consent queries performed
- `data_accesses`: Successful data access operations
- `total_records_shared`: Total patient records shared

## Integration Tests

Comprehensive integration tests verify all aspects of consent validation:

### Test Coverage

1. **test_data_request_validation_success**: Validates successful request processing
2. **test_data_request_validation_failure**: Tests request validation failures
3. **test_consent_verification_insufficient_consents**: Tests denial due to insufficient consents
4. **test_consent_verification_partial_consents**: Tests approval with partial consents (>50%)
5. **test_consent_query_error_handling**: Tests error handling in consent queries
6. **test_multi_data_type_consent_validation**: Tests consent for multiple data types
7. **test_consent_verification_audit_logging**: Verifies audit logging
8. **test_data_access_with_consent_expiry_check**: Tests expired consent handling
9. **test_consent_verification_statistics**: Verifies statistics tracking
10. **test_data_provenance_tracking**: Tests provenance tracking
11. **test_provenance_tracking_with_consent_info**: Tests provenance with consent details
12. **test_access_logs**: Tests access log retrieval
13. **test_dataset_discovery**: Tests dataset discovery
14. **test_dataset_summary**: Tests dataset summary retrieval
15. **test_no_matching_datasets**: Tests handling of no matching datasets
16. **test_health_check**: Tests health check functionality
17. **test_statistics_tracking**: Tests statistics updates
18. **test_agent_initialization**: Tests agent initialization

### Test Results

All 18 tests pass successfully, demonstrating:
- ✅ Consent validation logic works correctly
- ✅ Data request validation is comprehensive
- ✅ Provenance tracking captures all access events
- ✅ Multi-agent communication is properly implemented
- ✅ Error handling is robust
- ✅ Audit logging is complete
- ✅ Statistics are accurately tracked

## Security Features

### 1. Consent Enforcement
- No data access without valid consent
- Consent checked for each data type
- Consent checked for research category
- Expired consents are rejected

### 2. Audit Trail
- All consent queries logged
- All data access events recorded
- Cryptographic hashes for verification
- Immutable access history

### 3. Data Minimization
- Only consented patients' data is retrieved
- Only requested data types are included
- Data filtered based on consent permissions

### 4. Access Control
- Ethical approval required
- Research purpose validation
- Request validation before processing
- Consent threshold enforcement (≥50%)

## Requirements Fulfilled

This implementation fulfills the following requirements from the specification:

### Requirement 2.3: Consent Change Notification
- ✅ Consent is verified in real-time for each data request
- ✅ Consent changes are reflected immediately in access decisions

### Requirement 4.1: Multi-Agent Collaboration
- ✅ Data Custodian collaborates with Patient Consent Agent
- ✅ Standardized message protocols used
- ✅ Acknowledgments and error handling implemented

### Requirement 4.2: Standardized Message Protocols
- ✅ Uses `MessageTypes.CONSENT_QUERY` for consent verification
- ✅ Structured message payloads with validation
- ✅ Response handling with error cases

### Requirement 4.4: Audit Logging
- ✅ All consent queries logged
- ✅ All data access events recorded
- ✅ Provenance tracking with cryptographic verification
- ✅ Access history retrievable with filters

## Usage Examples

### Example 1: Successful Data Request with Consent

```python
# Create data request
request_payload = {
    "requester_id": "RESEARCHER-001",
    "data_criteria": {
        "data_types": ["demographics", "diagnoses"],
        "research_category": "cardiovascular_research"
    },
    "research_purpose": "Study cardiovascular disease patterns",
    "ethical_approval": "IRB-2024-001"
}

# Process request (consent will be verified automatically)
result = await agent._handle_data_request(ctx, sender, msg)

# Result includes:
# - status: "approved"
# - access_granted: True
# - records: [patient data]
# - consent_verification: {consent details}
```

### Example 2: Request Denied Due to Insufficient Consent

```python
# If <50% of patients have consented:
result = {
    "status": "denied",
    "access_granted": False,
    "denial_reason": "Insufficient patient consents",
    "consent_details": {
        "consented_patients": 3,
        "total_patients": 10,
        "consent_rate": 0.3
    }
}
```

### Example 3: Retrieve Access Logs

```python
# Get access logs for a specific requester
logs = agent.data_api.get_access_logs(requester_id="RESEARCHER-001")

# Each log entry includes:
# - access_id
# - request_id
# - requester_id
# - patient_ids
# - data_types
# - timestamp
# - access_hash (for verification)
```

### Example 4: Check Data Provenance

```python
# Get provenance for a specific patient
provenance = agent.data_api.get_provenance(patient_id="PAT-001")

# Provenance includes:
# - patient_id
# - access_events: [
#     {
#       "access_id": "...",
#       "requester_id": "...",
#       "data_types": [...],
#       "timestamp": "..."
#     }
#   ]
```

## Future Enhancements

Potential improvements for production deployment:

1. **Real-time Consent Updates**: Implement WebSocket connections for real-time consent change notifications
2. **Consent Caching**: Add caching layer for frequently accessed consent records
3. **Batch Consent Queries**: Optimize by batching multiple consent queries
4. **Consent Prediction**: Use ML to predict consent likelihood and pre-fetch
5. **Advanced Audit Analytics**: Add analytics dashboard for consent patterns
6. **Blockchain Integration**: Store consent hashes on blockchain for immutability
7. **GDPR Compliance**: Add right-to-be-forgotten and data portability features
8. **Multi-institution Federation**: Support consent verification across institutions

## Conclusion

The consent validation and data access control implementation provides:
- ✅ Robust consent checking with Patient Consent Agent integration
- ✅ Comprehensive data request validation
- ✅ Complete data provenance tracking with cryptographic verification
- ✅ Multi-agent communication with audit logging
- ✅ Extensive integration tests (18 tests, all passing)

This implementation ensures that patient privacy is protected while enabling ethical research access to healthcare data.
