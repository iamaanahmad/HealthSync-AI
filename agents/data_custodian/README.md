# Data Custodian Agent

The Data Custodian Agent represents healthcare institutions and manages access to patient medical records. It validates data access requests, verifies patient consent, and ensures secure data sharing for research purposes.

## Features

### Mock EHR System
- **Realistic Patient Records**: Generates 50 mock patient records with comprehensive medical data
- **Multiple Data Types**: Demographics, diagnoses, medications, lab results, vital signs, procedures, allergies, and immunizations
- **Dataset Categorization**: Automatically categorizes records into cardiovascular, diabetes, and general medical datasets
- **Data Quality Validation**: Calculates quality scores and validates data completeness

### Data Access API
- **Request Management**: Creates and tracks data access requests with full audit trails
- **Dataset Discovery**: Allows researchers to discover available datasets by research category
- **Data Provenance**: Tracks all data access events with cryptographic hashing
- **Quality Validation**: Validates data quality before sharing

### Consent Validation
- **Multi-Agent Communication**: Queries Patient Consent Agent to verify patient permissions
- **Granular Checking**: Validates consent for each patient and data type combination
- **Partial Consent Support**: Allows data sharing when >50% of patients have consented
- **Consent Rate Tracking**: Provides detailed consent verification statistics

### Access Control
- **Request Validation**: Validates ethical approval, research purpose, and data criteria
- **Dataset Matching**: Finds datasets that match research requirements
- **Access Logging**: Maintains comprehensive audit trails of all data access
- **Provenance Tracking**: Records data lineage and access history

## Architecture

```
Data Custodian Agent
├── Mock EHR System
│   ├── Patient Records (50 mock patients)
│   ├── Medical Data (diagnoses, medications, labs, etc.)
│   └── Datasets (cardiovascular, diabetes, general)
├── Data Access API
│   ├── Request Management
│   ├── Dataset Discovery
│   ├── Provenance Tracking
│   └── Quality Validation
└── Agent Communication
    ├── Patient Consent Agent (consent verification)
    ├── Research Query Agent (data requests)
    └── Privacy Agent (anonymization)
```

## Message Handlers

### DATA_REQUEST
Handles data access requests from researchers:
- Validates request parameters
- Searches for matching datasets
- Verifies patient consents
- Retrieves and returns authorized records

### dataset_discovery
Discovers available datasets by research category

### dataset_summary
Provides detailed information about a specific dataset

### data_provenance
Retrieves data access history for a patient

### access_logs
Returns access logs filtered by requester

### HEALTH_CHECK
Returns agent health status and statistics

## Usage

### Running the Agent

```python
from agents.data_custodian.agent import DataCustodianAgent

agent = DataCustodianAgent(
    port=8003,
    patient_consent_agent_address="agent1qw...",
    institution_id="HEALTHSYNC_HOSPITAL_001"
)

agent.run()
```

### Environment Variables

- `DATA_CUSTODIAN_PORT`: Port for the agent (default: 8003)
- `PATIENT_CONSENT_AGENT_ADDRESS`: Address of Patient Consent Agent
- `INSTITUTION_ID`: Healthcare institution identifier

### Example Data Request

```python
data_request = {
    "requester_id": "RESEARCHER-001",
    "data_criteria": {
        "data_types": ["demographics", "diagnoses"],
        "research_category": "cardiovascular_research"
    },
    "research_purpose": "Study cardiovascular disease patterns in elderly patients",
    "ethical_approval": "IRB-2024-001"
}
```

## Testing

### Run Unit Tests

```bash
# Test Mock EHR System
python -m pytest agents/data_custodian/test_mock_ehr.py -v

# Test Data Access API
python -m pytest agents/data_custodian/test_data_access_api.py -v

# Test Consent Integration
python -m pytest agents/data_custodian/test_consent_integration.py -v
```

### Test Coverage

- **Mock EHR System**: 18 tests covering record generation, dataset creation, search, and validation
- **Data Access API**: 24 tests covering request management, validation, provenance, and access control
- **Consent Integration**: 18 tests covering consent verification, multi-agent communication, and access workflows

All tests pass successfully, demonstrating robust consent validation and data access control.

## Data Types

The agent supports the following data types:
- `demographics`: Age, gender, ethnicity, insurance
- `diagnoses`: ICD-10 codes, descriptions, severity
- `medications`: Name, dosage, frequency, indication
- `lab_results`: Test name, value, reference range
- `vital_signs`: Blood pressure, heart rate, temperature
- `procedures`: CPT codes, descriptions, dates
- `allergies`: Allergen, reaction, severity
- `immunizations`: Vaccine, date, lot number

## Research Categories

- `cardiovascular_research`: Heart disease, hypertension
- `diabetes_research`: Type 1 and Type 2 diabetes
- `cancer_research`: Oncology studies
- `infectious_disease_research`: Infectious diseases
- `mental_health_research`: Mental health conditions
- `general_medical_research`: General medical studies

## Statistics Tracked

- `total_requests`: Total data access requests received
- `approved_requests`: Requests approved and fulfilled
- `denied_requests`: Requests denied (validation or consent failures)
- `consent_checks`: Number of consent verifications performed
- `data_accesses`: Successful data access operations
- `total_records_shared`: Total patient records shared

## Security Features

- **Consent Verification**: All data access requires patient consent
- **Audit Trails**: Complete logging of all access events
- **Cryptographic Hashing**: Access events are hashed for verification
- **Data Quality Validation**: Ensures data meets quality standards
- **Provenance Tracking**: Maintains complete data lineage

## Integration Points

### Patient Consent Agent
- Queries consent status for each patient and data type
- Validates consent before data sharing
- Tracks consent verification results

### Research Query Agent
- Receives data requests from researchers
- Returns anonymized datasets
- Provides query status updates

### Privacy Agent
- Sends raw data for anonymization
- Receives anonymized datasets
- Ensures privacy compliance

## Requirements

See `requirements.txt` for dependencies:
- uagents
- pydantic
- Additional shared utilities

## Future Enhancements

- Real EHR system integration (FHIR, HL7)
- Advanced consent verification workflows
- Real-time data quality monitoring
- Multi-institution data federation
- Enhanced provenance visualization
