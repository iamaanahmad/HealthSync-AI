"""
MeTTa Integration Agent for HealthSync
Manages knowledge graph operations and reasoning using MeTTa
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import hashlib

from uagents import Context
from shared.base_agent import HealthSyncBaseAgent
from shared.protocols.agent_messages import MessageTypes
from shared.utils.error_handling import with_error_handling
from .schema_manager import MeTTaSchemaManager


class MeTTaQuery:
    """Represents a MeTTa query with context"""
    
    def __init__(self, query_type: str, query_expression: str, 
                 context_variables: Optional[Dict[str, Any]] = None):
        self.query_id = hashlib.md5(
            f"{query_type}:{query_expression}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        self.query_type = query_type
        self.query_expression = query_expression
        self.context_variables = context_variables or {}
        self.timestamp = datetime.now()


class MeTTaResponse:
    """Represents a MeTTa query response with reasoning"""
    
    def __init__(self, query_id: str, results: List[Dict[str, Any]], 
                 reasoning_path: List[str], confidence_score: float):
        self.query_id = query_id
        self.results = results
        self.reasoning_path = reasoning_path
        self.confidence_score = confidence_score
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query_id': self.query_id,
            'results': self.results,
            'reasoning_path': self.reasoning_path,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp.isoformat()
        }


class MeTTaIntegrationAgent(HealthSyncBaseAgent):
    """
    MeTTa Integration Agent
    Manages knowledge graph operations and complex reasoning
    """
    
    def __init__(self, seed: str = None, port: int = 8001, endpoint: str = None):
        super().__init__(
            name="MeTTa Integration Agent",
            seed=seed or "metta_integration_agent_seed",
            port=port,
            endpoint=endpoint
        )
        
        # Initialize schema manager
        self.schema_manager = MeTTaSchemaManager()
        self.schema_loaded = False
        
        # In-memory knowledge graph storage (simulated MeTTa)
        self.knowledge_graph = {
            'entities': {},
            'relationships': [],
            'rules': []
        }
        
        # Query cache for performance
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Reasoning statistics
        self.reasoning_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'cache_hits': 0,
            'average_reasoning_time': 0.0
        }
        
        # Register message handlers
        self._register_handlers()
        
        self.logger.info("MeTTa Integration Agent initialized")
    
    def _register_handlers(self):
        """Register message handlers for MeTTa operations"""
        
        self.register_message_handler(
            MessageTypes.METTA_QUERY,
            self.handle_metta_query
        )
        
        self.register_message_handler(
            MessageTypes.METTA_STORE,
            self.handle_metta_store
        )
        
        self.register_message_handler(
            MessageTypes.METTA_VALIDATE,
            self.handle_metta_validate
        )
    
    async def on_startup(self, ctx: Context):
        """Initialize MeTTa schema on startup"""
        self.schema_loaded = self.schema_manager.load_schema()
        
        if self.schema_loaded:
            self.logger.info("MeTTa schema loaded successfully",
                           stats=self.schema_manager.get_schema_stats())
            
            # Initialize default entities
            await self._initialize_default_entities()
        else:
            self.logger.error("Failed to load MeTTa schema")
    
    async def _initialize_default_entities(self):
        """Initialize default data types, research categories, and privacy rules"""
        
        # Default data types
        default_data_types = [
            self.schema_manager.create_data_type(
                "DT001", "Medical Records", "high", 
                ["patient_consent", "ethics_approval"]
            ),
            self.schema_manager.create_data_type(
                "DT002", "Lab Results", "high",
                ["patient_consent", "ethics_approval"]
            ),
            self.schema_manager.create_data_type(
                "DT003", "Demographics", "medium",
                ["patient_consent"]
            ),
            self.schema_manager.create_data_type(
                "DT004", "Prescriptions", "high",
                ["patient_consent", "ethics_approval"]
            )
        ]
        
        # Default research categories
        default_categories = [
            self.schema_manager.create_research_category(
                "RC001", "Cancer Research", "IRB_APPROVED",
                ["DT001", "DT002", "DT004"]
            ),
            self.schema_manager.create_research_category(
                "RC002", "Diabetes Research", "IRB_APPROVED",
                ["DT001", "DT002", "DT003", "DT004"]
            ),
            self.schema_manager.create_research_category(
                "RC003", "Cardiovascular Research", "IRB_APPROVED",
                ["DT001", "DT002", "DT003"]
            )
        ]
        
        # Default anonymization methods
        default_methods = [
            self.schema_manager.create_anonymization_method(
                "AM001", "K-Anonymity", "generalization", "high"
            ),
            self.schema_manager.create_anonymization_method(
                "AM002", "Differential Privacy", "noise_injection", "high"
            ),
            self.schema_manager.create_anonymization_method(
                "AM003", "Hashing", "cryptographic_hash", "medium"
            )
        ]
        
        # Default privacy rules
        default_rules = [
            self.schema_manager.create_privacy_rule(
                "PR001", "High Sensitivity Rule", "DT001", "AM001", 5
            ),
            self.schema_manager.create_privacy_rule(
                "PR002", "Lab Results Rule", "DT002", "AM001", 5
            ),
            self.schema_manager.create_privacy_rule(
                "PR003", "Demographics Rule", "DT003", "AM003", 3
            ),
            self.schema_manager.create_privacy_rule(
                "PR004", "Prescriptions Rule", "DT004", "AM002", 5
            )
        ]
        
        # Store in knowledge graph
        for dt in default_data_types:
            self._store_entity(dt)
        
        for cat in default_categories:
            self._store_entity(cat)
        
        for method in default_methods:
            self._store_entity(method)
        
        for rule in default_rules:
            self._store_entity(rule)
        
        self.logger.info("Default entities initialized",
                        data_types=len(default_data_types),
                        categories=len(default_categories),
                        methods=len(default_methods),
                        rules=len(default_rules))
    
    def _store_entity(self, entity: Dict[str, Any]):
        """Store entity in knowledge graph"""
        entity_type = entity.get('entity_type')
        entity_id = self._get_entity_id(entity)
        
        if entity_type not in self.knowledge_graph['entities']:
            self.knowledge_graph['entities'][entity_type] = {}
        
        self.knowledge_graph['entities'][entity_type][entity_id] = entity
    
    def _get_entity_id(self, entity: Dict[str, Any]) -> str:
        """Extract entity ID from entity data"""
        entity_type = entity.get('entity_type')
        
        id_field_map = {
            'Patient': 'patient_id',
            'ConsentRecord': 'consent_id',
            'DataType': 'type_id',
            'ResearchCategory': 'category_id',
            'PrivacyRule': 'rule_id',
            'AnonymizationMethod': 'method_id'
        }
        
        id_field = id_field_map.get(entity_type)
        return entity.get(id_field, '')
    
    async def handle_metta_query(self, ctx: Context, sender: str, 
                                msg: Any) -> Dict[str, Any]:
        """Handle MeTTa query requests"""
        payload = msg.payload
        
        query_type = payload.get('query_type')
        query_expression = payload.get('query_expression')
        context_vars = payload.get('context_variables', {})
        
        self.logger.info("Processing MeTTa query",
                        query_type=query_type,
                        sender=sender)
        
        # Create query object
        query = MeTTaQuery(query_type, query_expression, context_vars)
        
        # Execute query
        response = await self._execute_query(query)
        
        # Update statistics
        self.reasoning_stats['total_queries'] += 1
        if response.confidence_score > 0:
            self.reasoning_stats['successful_queries'] += 1
        else:
            self.reasoning_stats['failed_queries'] += 1
        
        return response.to_dict()
    
    async def handle_metta_store(self, ctx: Context, sender: str,
                                msg: Any) -> Dict[str, Any]:
        """Handle entity storage requests"""
        payload = msg.payload
        
        entity_type = payload.get('entity_type')
        entity_data = payload.get('entity_data')
        
        self.logger.info("Storing entity in MeTTa",
                        entity_type=entity_type,
                        sender=sender)
        
        # Validate entity
        is_valid, errors = self.schema_manager.validate_entity(
            entity_type, entity_data
        )
        
        if not is_valid:
            return {
                'success': False,
                'errors': errors
            }
        
        # Store entity
        self._store_entity(entity_data)
        
        # Create relationships if specified
        relationships = payload.get('relationships', [])
        for rel in relationships:
            self.knowledge_graph['relationships'].append(rel)
        
        return {
            'success': True,
            'entity_id': self._get_entity_id(entity_data)
        }
    
    async def handle_metta_validate(self, ctx: Context, sender: str,
                                   msg: Any) -> Dict[str, Any]:
        """Handle validation requests"""
        payload = msg.payload
        
        validation_type = payload.get('validation_type')
        validation_data = payload.get('validation_data')
        
        self.logger.info("Validating with MeTTa",
                        validation_type=validation_type,
                        sender=sender)
        
        if validation_type == 'consent':
            result = await self._validate_consent(validation_data)
        elif validation_type == 'ethics':
            result = await self._validate_ethics(validation_data)
        elif validation_type == 'privacy':
            result = await self._validate_privacy(validation_data)
        else:
            result = {'valid': False, 'error': 'Unknown validation type'}
        
        return result
    
    async def _execute_query(self, query: MeTTaQuery) -> MeTTaResponse:
        """Execute MeTTa query with reasoning"""
        
        start_time = datetime.now()
        reasoning_path = []
        results = []
        confidence = 0.0
        
        try:
            # Check cache first
            cache_key = f"{query.query_type}:{query.query_expression}"
            if cache_key in self.query_cache:
                cached = self.query_cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl:
                    self.reasoning_stats['cache_hits'] += 1
                    return cached['response']
            
            # Execute based on query type
            if query.query_type == 'has_valid_consent':
                results, reasoning_path, confidence = await self._query_valid_consent(
                    query.context_variables
                )
            
            elif query.query_type == 'get_privacy_rule':
                results, reasoning_path, confidence = await self._query_privacy_rule(
                    query.context_variables
                )
            
            elif query.query_type == 'validate_research_request':
                results, reasoning_path, confidence = await self._query_validate_research(
                    query.context_variables
                )
            
            elif query.query_type == 'find_consenting_patients':
                results, reasoning_path, confidence = await self._query_consenting_patients(
                    query.context_variables
                )
            
            elif query.query_type == 'traverse_consent_chain':
                results, reasoning_path, confidence = await self._query_consent_chain(
                    query.context_variables
                )
            
            else:
                reasoning_path.append(f"Unknown query type: {query.query_type}")
                confidence = 0.0
            
            # Create response
            response = MeTTaResponse(
                query.query_id, results, reasoning_path, confidence
            )
            
            # Cache response
            self.query_cache[cache_key] = {
                'response': response,
                'timestamp': datetime.now()
            }
            
            # Update timing statistics (before returning)
            query_time = (datetime.now() - start_time).total_seconds()
            
            return response
            
        except Exception as e:
            self.logger.error("Query execution failed",
                            query_type=query.query_type,
                            error=str(e))
            
            reasoning_path.append(f"Error: {str(e)}")
            return MeTTaResponse(query.query_id, [], reasoning_path, 0.0)
    
    async def _query_valid_consent(self, context: Dict[str, Any]) -> Tuple[List, List, float]:
        """Query if patient has valid consent (nested query support)"""
        reasoning_path = []
        results = []
        
        patient_id = context.get('patient_id')
        data_type_id = context.get('data_type_id')
        research_category_id = context.get('research_category_id')
        
        reasoning_path.append(f"Checking consent for patient {patient_id}")
        reasoning_path.append(f"Data type: {data_type_id}, Research: {research_category_id}")
        
        # Find consent records for patient
        consents = self.knowledge_graph['entities'].get('ConsentRecord', {})
        
        for consent_id, consent in consents.items():
            if (consent.get('patient_ref') == patient_id and
                consent.get('data_type_ref') == data_type_id and
                consent.get('research_category_ref') == research_category_id):
                
                reasoning_path.append(f"Found consent record: {consent_id}")
                
                # Check if consent is granted
                if not consent.get('consent_granted'):
                    reasoning_path.append("Consent not granted")
                    continue
                
                reasoning_path.append("Consent is granted")
                
                # Check if expired
                expiry = datetime.fromisoformat(consent.get('expiry_date'))
                if expiry < datetime.now():
                    reasoning_path.append("Consent has expired")
                    continue
                
                reasoning_path.append("Consent is valid and not expired")
                results.append({
                    'consent_id': consent_id,
                    'valid': True,
                    'expiry_date': consent.get('expiry_date')
                })
                
                return results, reasoning_path, 1.0
        
        reasoning_path.append("No valid consent found")
        return results, reasoning_path, 0.0
    
    async def _query_privacy_rule(self, context: Dict[str, Any]) -> Tuple[List, List, float]:
        """Query privacy rule for data type (recursive traversal)"""
        reasoning_path = []
        
        data_type_id = context.get('data_type_id')
        
        reasoning_path.append(f"Finding privacy rule for data type: {data_type_id}")
        
        # Find applicable privacy rule
        rules = self.knowledge_graph['entities'].get('PrivacyRule', {})
        
        for rule_id, rule in rules.items():
            if rule.get('applies_to_data_type') == data_type_id:
                reasoning_path.append(f"Found privacy rule: {rule_id}")
                
                # Get anonymization method
                method_id = rule.get('anonymization_method')
                methods = self.knowledge_graph['entities'].get('AnonymizationMethod', {})
                method = methods.get(method_id, {})
                
                reasoning_path.append(f"Anonymization method: {method.get('method_name')}")
                
                results = [{
                    'rule_id': rule_id,
                    'rule_name': rule.get('rule_name'),
                    'k_anonymity_threshold': rule.get('k_anonymity_threshold'),
                    'anonymization_method': method
                }]
                
                return results, reasoning_path, 1.0
        
        reasoning_path.append("No privacy rule found, using default")
        default_rule = {
            'rule_id': 'default',
            'rule_name': 'Default Privacy Rule',
            'k_anonymity_threshold': 5,
            'anonymization_method': {'method_name': 'K-Anonymity', 'technique': 'generalization'}
        }
        
        return [default_rule], reasoning_path, 0.5
    
    async def _query_validate_research(self, context: Dict[str, Any]) -> Tuple[List, List, float]:
        """Validate complete research request (complex nested query)"""
        reasoning_path = []
        
        patient_id = context.get('patient_id')
        data_types = context.get('data_types', [])
        research_category_id = context.get('research_category_id')
        
        reasoning_path.append("Validating research request")
        reasoning_path.append(f"Patient: {patient_id}, Category: {research_category_id}")
        
        # Check ethics requirements
        categories = self.knowledge_graph['entities'].get('ResearchCategory', {})
        category = categories.get(research_category_id)
        
        if not category:
            reasoning_path.append("Research category not found")
            return [], reasoning_path, 0.0
        
        reasoning_path.append(f"Ethics requirement: {category.get('ethics_requirements')}")
        
        # Check all data types are allowed
        allowed_types = category.get('allowed_data_types', [])
        for dt in data_types:
            if dt not in allowed_types:
                reasoning_path.append(f"Data type {dt} not allowed for this research")
                return [], reasoning_path, 0.0
        
        reasoning_path.append("All data types are allowed")
        
        # Check consent for each data type
        all_consents_valid = True
        for dt in data_types:
            consent_results, consent_reasoning, consent_confidence = await self._query_valid_consent({
                'patient_id': patient_id,
                'data_type_id': dt,
                'research_category_id': research_category_id
            })
            
            reasoning_path.extend(consent_reasoning)
            
            if consent_confidence < 1.0:
                all_consents_valid = False
                break
        
        if all_consents_valid:
            reasoning_path.append("All consents validated successfully")
            return [{'valid': True, 'patient_id': patient_id}], reasoning_path, 1.0
        else:
            reasoning_path.append("Consent validation failed")
            return [{'valid': False}], reasoning_path, 0.0
    
    async def _query_consenting_patients(self, context: Dict[str, Any]) -> Tuple[List, List, float]:
        """Find all patients with consent for specific research (recursive)"""
        reasoning_path = []
        results = []
        
        data_type_id = context.get('data_type_id')
        research_category_id = context.get('research_category_id')
        
        reasoning_path.append("Finding consenting patients")
        reasoning_path.append(f"Data type: {data_type_id}, Research: {research_category_id}")
        
        # Get all consent records
        consents = self.knowledge_graph['entities'].get('ConsentRecord', {})
        patient_ids = set()
        
        for consent_id, consent in consents.items():
            if (consent.get('data_type_ref') == data_type_id and
                consent.get('research_category_ref') == research_category_id and
                consent.get('consent_granted')):
                
                # Check expiry
                expiry = datetime.fromisoformat(consent.get('expiry_date'))
                if expiry >= datetime.now():
                    patient_id = consent.get('patient_ref')
                    patient_ids.add(patient_id)
                    reasoning_path.append(f"Found consenting patient: {patient_id}")
        
        results = [{'patient_id': pid} for pid in patient_ids]
        confidence = 1.0 if results else 0.0
        
        reasoning_path.append(f"Total consenting patients: {len(results)}")
        
        return results, reasoning_path, confidence
    
    async def _query_consent_chain(self, context: Dict[str, Any]) -> Tuple[List, List, float]:
        """Traverse consent relationships for patient (recursive graph traversal)"""
        reasoning_path = []
        results = []
        
        patient_id = context.get('patient_id')
        research_category_id = context.get('research_category_id')
        
        reasoning_path.append(f"Traversing consent chain for patient: {patient_id}")
        
        # Find all consents for patient
        consents = self.knowledge_graph['entities'].get('ConsentRecord', {})
        
        for consent_id, consent in consents.items():
            if consent.get('patient_ref') == patient_id:
                reasoning_path.append(f"Examining consent: {consent_id}")
                
                # Check if active
                if not consent.get('consent_granted'):
                    reasoning_path.append("Consent not granted, skipping")
                    continue
                
                expiry = datetime.fromisoformat(consent.get('expiry_date'))
                if expiry < datetime.now():
                    reasoning_path.append("Consent expired, skipping")
                    continue
                
                # Check if matches research category
                if consent.get('research_category_ref') == research_category_id:
                    reasoning_path.append("Consent matches research category")
                    
                    # Get data type and privacy rule
                    data_type_id = consent.get('data_type_ref')
                    privacy_results, privacy_reasoning, _ = await self._query_privacy_rule({
                        'data_type_id': data_type_id
                    })
                    
                    results.append({
                        'consent_id': consent_id,
                        'data_type_id': data_type_id,
                        'privacy_rule': privacy_results[0] if privacy_results else None
                    })
        
        reasoning_path.append(f"Found {len(results)} valid consent records")
        confidence = 1.0 if results else 0.0
        
        return results, reasoning_path, confidence
    
    async def _validate_consent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate consent using MeTTa reasoning"""
        query = MeTTaQuery('has_valid_consent', '', data)
        response = await self._execute_query(query)
        
        return {
            'valid': response.confidence_score >= 1.0,
            'reasoning': response.reasoning_path,
            'results': response.results
        }
    
    async def _validate_ethics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ethics compliance"""
        query = MeTTaQuery('validate_research_request', '', data)
        response = await self._execute_query(query)
        
        return {
            'valid': response.confidence_score >= 1.0,
            'reasoning': response.reasoning_path,
            'results': response.results
        }
    
    async def _validate_privacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate privacy requirements"""
        data_type_id = data.get('data_type_id')
        k_value = data.get('k_value', 5)
        
        query = MeTTaQuery('get_privacy_rule', '', {'data_type_id': data_type_id})
        response = await self._execute_query(query)
        
        if response.results:
            rule = response.results[0]
            threshold = rule.get('k_anonymity_threshold', 5)
            valid = k_value >= threshold
            
            return {
                'valid': valid,
                'reasoning': response.reasoning_path + [
                    f"K-anonymity threshold: {threshold}",
                    f"Provided k-value: {k_value}",
                    f"Meets requirement: {valid}"
                ],
                'privacy_rule': rule
            }
        
        return {'valid': False, 'reasoning': ['No privacy rule found']}
    
    def _update_timing_stats(self, query_time: float):
        """Update average query timing statistics"""
        total = self.reasoning_stats['total_queries']
        current_avg = self.reasoning_stats['average_reasoning_time']
        
        if total > 0:
            new_avg = ((current_avg * (total - 1)) + query_time) / total
            self.reasoning_stats['average_reasoning_time'] = new_avg
    
    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get reasoning statistics"""
        return self.reasoning_stats.copy()
    
    def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        stats = {
            'total_entities': 0,
            'total_relationships': len(self.knowledge_graph['relationships']),
            'entities_by_type': {}
        }
        
        for entity_type, entities in self.knowledge_graph['entities'].items():
            count = len(entities)
            stats['entities_by_type'][entity_type] = count
            stats['total_entities'] += count
        
        return stats


# Create agent instance
def create_metta_agent(seed: str = None, port: int = 8001) -> MeTTaIntegrationAgent:
    """Factory function to create MeTTa Integration Agent"""
    return MeTTaIntegrationAgent(seed=seed, port=port)


if __name__ == "__main__":
    agent = create_metta_agent()
    agent.run()
