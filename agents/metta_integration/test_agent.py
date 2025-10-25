"""
Unit tests for MeTTa Integration Agent
Tests query execution, reasoning capabilities, and error handling
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from agents.metta_integration.agent import (
    MeTTaIntegrationAgent, MeTTaQuery, MeTTaResponse
)
from shared.protocols.agent_messages import AgentMessage, MessageTypes


class TestMeTTaIntegrationAgent(unittest.TestCase):
    """Test cases for MeTTa Integration Agent initialization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = MeTTaIntegrationAgent(
            seed="test_metta_seed",
            port=8099
        )
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.name, "MeTTa Integration Agent")
        self.assertIsNotNone(self.agent.schema_manager)
        self.assertIsNotNone(self.agent.knowledge_graph)
    
    def test_knowledge_graph_structure(self):
        """Test knowledge graph has correct structure"""
        self.assertIn('entities', self.agent.knowledge_graph)
        self.assertIn('relationships', self.agent.knowledge_graph)
        self.assertIn('rules', self.agent.knowledge_graph)
    
    def test_reasoning_stats_initialized(self):
        """Test reasoning statistics are initialized"""
        stats = self.agent.get_reasoning_stats()
        self.assertEqual(stats['total_queries'], 0)
        self.assertEqual(stats['successful_queries'], 0)
        self.assertEqual(stats['failed_queries'], 0)


class TestMeTTaQuery(unittest.TestCase):
    """Test cases for MeTTa query objects"""
    
    def test_query_creation(self):
        """Test creating a MeTTa query"""
        query = MeTTaQuery(
            query_type="has_valid_consent",
            query_expression="test_expression",
            context_variables={'patient_id': 'P001'}
        )
        
        self.assertIsNotNone(query.query_id)
        self.assertEqual(query.query_type, "has_valid_consent")
        self.assertIsNotNone(query.timestamp)


class TestMeTTaResponse(unittest.TestCase):
    """Test cases for MeTTa response objects"""
    
    def test_response_creation(self):
        """Test creating a MeTTa response"""
        response = MeTTaResponse(
            query_id="test_query_123",
            results=[{'key': 'value'}],
            reasoning_path=["step1", "step2"],
            confidence_score=0.95
        )
        
        self.assertEqual(response.query_id, "test_query_123")
        self.assertEqual(len(response.results), 1)
        self.assertEqual(len(response.reasoning_path), 2)
        self.assertEqual(response.confidence_score, 0.95)
    
    def test_response_to_dict(self):
        """Test converting response to dictionary"""
        response = MeTTaResponse(
            query_id="test_query_123",
            results=[],
            reasoning_path=["step1"],
            confidence_score=1.0
        )
        
        response_dict = response.to_dict()
        self.assertIn('query_id', response_dict)
        self.assertIn('results', response_dict)
        self.assertIn('reasoning_path', response_dict)
        self.assertIn('confidence_score', response_dict)


class TestEntityStorage(unittest.IsolatedAsyncioTestCase):
    """Test cases for entity storage operations"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
    
    async def test_store_patient_entity(self):
        """Test storing a patient entity"""
        patient = self.agent.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="hash123"
        )
        
        self.agent._store_entity(patient)
        
        stored = self.agent.knowledge_graph['entities']['Patient']['P001']
        self.assertEqual(stored['patient_id'], 'P001')
    
    async def test_store_consent_record(self):
        """Test storing a consent record"""
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        consent = self.agent.schema_manager.create_consent_record(
            consent_id="C001",
            patient_id="P001",
            data_type_id="DT001",
            research_category_id="RC001",
            consent_granted=True,
            expiry_date=expiry
        )
        
        self.agent._store_entity(consent)
        
        stored = self.agent.knowledge_graph['entities']['ConsentRecord']['C001']
        self.assertEqual(stored['consent_id'], 'C001')
        self.assertTrue(stored['consent_granted'])
    
    async def test_default_entities_loaded(self):
        """Test that default entities are loaded on startup"""
        stats = self.agent.get_knowledge_graph_stats()
        
        self.assertGreater(stats['total_entities'], 0)
        self.assertIn('DataType', stats['entities_by_type'])
        self.assertIn('ResearchCategory', stats['entities_by_type'])
        self.assertIn('PrivacyRule', stats['entities_by_type'])


class TestConsentValidation(unittest.IsolatedAsyncioTestCase):
    """Test cases for consent validation queries"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
        
        # Add test patient and consent
        patient = self.agent.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="hash123"
        )
        self.agent._store_entity(patient)
        
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        consent = self.agent.schema_manager.create_consent_record(
            consent_id="C001",
            patient_id="P001",
            data_type_id="DT001",
            research_category_id="RC001",
            consent_granted=True,
            expiry_date=expiry
        )
        self.agent._store_entity(consent)
    
    async def test_valid_consent_query(self):
        """Test querying for valid consent"""
        results, reasoning, confidence = await self.agent._query_valid_consent({
            'patient_id': 'P001',
            'data_type_id': 'DT001',
            'research_category_id': 'RC001'
        })
        
        self.assertEqual(confidence, 1.0)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['valid'])
        self.assertGreater(len(reasoning), 0)
    
    async def test_invalid_consent_query(self):
        """Test querying for non-existent consent"""
        results, reasoning, confidence = await self.agent._query_valid_consent({
            'patient_id': 'P999',
            'data_type_id': 'DT001',
            'research_category_id': 'RC001'
        })
        
        self.assertEqual(confidence, 0.0)
        self.assertEqual(len(results), 0)
    
    async def test_expired_consent(self):
        """Test that expired consent is not valid"""
        # Add expired consent
        expired_date = (datetime.now() - timedelta(days=1)).isoformat()
        expired_consent = self.agent.schema_manager.create_consent_record(
            consent_id="C002",
            patient_id="P001",
            data_type_id="DT002",
            research_category_id="RC001",
            consent_granted=True,
            expiry_date=expired_date
        )
        self.agent._store_entity(expired_consent)
        
        results, reasoning, confidence = await self.agent._query_valid_consent({
            'patient_id': 'P001',
            'data_type_id': 'DT002',
            'research_category_id': 'RC001'
        })
        
        self.assertEqual(confidence, 0.0)
        self.assertIn("expired", " ".join(reasoning).lower())


class TestPrivacyRuleQueries(unittest.IsolatedAsyncioTestCase):
    """Test cases for privacy rule queries"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
    
    async def test_get_privacy_rule(self):
        """Test retrieving privacy rule for data type"""
        results, reasoning, confidence = await self.agent._query_privacy_rule({
            'data_type_id': 'DT001'
        })
        
        self.assertEqual(confidence, 1.0)
        self.assertEqual(len(results), 1)
        self.assertIn('k_anonymity_threshold', results[0])
        self.assertIn('anonymization_method', results[0])
    
    async def test_default_privacy_rule(self):
        """Test default privacy rule for unknown data type"""
        results, reasoning, confidence = await self.agent._query_privacy_rule({
            'data_type_id': 'DT999'
        })
        
        self.assertEqual(confidence, 0.5)
        self.assertEqual(results[0]['rule_id'], 'default')


class TestResearchValidation(unittest.IsolatedAsyncioTestCase):
    """Test cases for research request validation"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
        
        # Add test patient and consents
        patient = self.agent.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="hash123"
        )
        self.agent._store_entity(patient)
        
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        for dt_id in ['DT001', 'DT002']:
            consent = self.agent.schema_manager.create_consent_record(
                consent_id=f"C_{dt_id}",
                patient_id="P001",
                data_type_id=dt_id,
                research_category_id="RC001",
                consent_granted=True,
                expiry_date=expiry
            )
            self.agent._store_entity(consent)
    
    async def test_valid_research_request(self):
        """Test validating a complete research request"""
        results, reasoning, confidence = await self.agent._query_validate_research({
            'patient_id': 'P001',
            'data_types': ['DT001', 'DT002'],
            'research_category_id': 'RC001'
        })
        
        self.assertEqual(confidence, 1.0)
        self.assertTrue(results[0]['valid'])
    
    async def test_invalid_data_type_for_research(self):
        """Test research request with disallowed data type"""
        results, reasoning, confidence = await self.agent._query_validate_research({
            'patient_id': 'P001',
            'data_types': ['DT999'],
            'research_category_id': 'RC001'
        })
        
        self.assertEqual(confidence, 0.0)


class TestConsentChainTraversal(unittest.IsolatedAsyncioTestCase):
    """Test cases for recursive consent chain traversal"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
        
        # Add test patient with multiple consents
        patient = self.agent.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="hash123"
        )
        self.agent._store_entity(patient)
        
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        for i, dt_id in enumerate(['DT001', 'DT002', 'DT004']):
            consent = self.agent.schema_manager.create_consent_record(
                consent_id=f"C00{i+1}",
                patient_id="P001",
                data_type_id=dt_id,
                research_category_id="RC001",
                consent_granted=True,
                expiry_date=expiry
            )
            self.agent._store_entity(consent)
    
    async def test_traverse_consent_chain(self):
        """Test traversing all consents for a patient"""
        results, reasoning, confidence = await self.agent._query_consent_chain({
            'patient_id': 'P001',
            'research_category_id': 'RC001'
        })
        
        self.assertEqual(confidence, 1.0)
        self.assertEqual(len(results), 3)
        
        # Verify each result has privacy rule
        for result in results:
            self.assertIn('consent_id', result)
            self.assertIn('data_type_id', result)
            self.assertIn('privacy_rule', result)


class TestMessageHandlers(unittest.IsolatedAsyncioTestCase):
    """Test cases for agent message handlers"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
        
        self.mock_ctx = Mock()
        self.mock_ctx.send = AsyncMock()
    
    async def test_handle_metta_query(self):
        """Test handling MeTTa query message"""
        msg = Mock()
        msg.payload = {
            'query_type': 'get_privacy_rule',
            'query_expression': '',
            'context_variables': {'data_type_id': 'DT001'}
        }
        
        result = await self.agent.handle_metta_query(
            self.mock_ctx, "test_sender", msg
        )
        
        self.assertIn('results', result)
        self.assertIn('reasoning_path', result)
        self.assertIn('confidence_score', result)
    
    async def test_handle_metta_store(self):
        """Test handling entity storage message"""
        patient = self.agent.schema_manager.create_patient_entity(
            patient_id="P999",
            demographic_hash="hash999"
        )
        
        msg = Mock()
        msg.payload = {
            'entity_type': 'Patient',
            'entity_data': patient,
            'relationships': []
        }
        
        result = await self.agent.handle_metta_store(
            self.mock_ctx, "test_sender", msg
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['entity_id'], 'P999')
    
    async def test_handle_metta_validate_consent(self):
        """Test handling consent validation message"""
        # Add test data
        patient = self.agent.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="hash123"
        )
        self.agent._store_entity(patient)
        
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        consent = self.agent.schema_manager.create_consent_record(
            consent_id="C001",
            patient_id="P001",
            data_type_id="DT001",
            research_category_id="RC001",
            consent_granted=True,
            expiry_date=expiry
        )
        self.agent._store_entity(consent)
        
        msg = Mock()
        msg.payload = {
            'validation_type': 'consent',
            'validation_data': {
                'patient_id': 'P001',
                'data_type_id': 'DT001',
                'research_category_id': 'RC001'
            }
        }
        
        result = await self.agent.handle_metta_validate(
            self.mock_ctx, "test_sender", msg
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('reasoning', result)


class TestQueryCaching(unittest.IsolatedAsyncioTestCase):
    """Test cases for query caching"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
    
    async def test_query_caching(self):
        """Test that queries are cached"""
        query = MeTTaQuery(
            'get_privacy_rule',
            '',
            {'data_type_id': 'DT001'}
        )
        
        # First query
        response1 = await self.agent._execute_query(query)
        cache_hits_before = self.agent.reasoning_stats['cache_hits']
        
        # Second identical query
        response2 = await self.agent._execute_query(query)
        cache_hits_after = self.agent.reasoning_stats['cache_hits']
        
        self.assertEqual(cache_hits_after, cache_hits_before + 1)


class TestReasoningStatistics(unittest.IsolatedAsyncioTestCase):
    """Test cases for reasoning statistics"""
    
    async def asyncSetUp(self):
        """Set up async test fixtures"""
        self.agent = MeTTaIntegrationAgent(seed="test_seed", port=8099)
        self.agent.schema_manager.load_schema()
        await self.agent._initialize_default_entities()
    
    async def test_statistics_updated(self):
        """Test that statistics are updated after queries"""
        initial_stats = self.agent.get_reasoning_stats()
        initial_total = initial_stats['total_queries']
        
        # Create mock message
        msg = Mock()
        msg.payload = {
            'query_type': 'get_privacy_rule',
            'query_expression': '',
            'context_variables': {'data_type_id': 'DT001'}
        }
        
        mock_ctx = Mock()
        
        await self.agent.handle_metta_query(mock_ctx, "test_sender", msg)
        
        updated_stats = self.agent.get_reasoning_stats()
        self.assertEqual(updated_stats['total_queries'], initial_total + 1)
    
    async def test_knowledge_graph_stats(self):
        """Test knowledge graph statistics"""
        stats = self.agent.get_knowledge_graph_stats()
        
        self.assertIn('total_entities', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('entities_by_type', stats)
        self.assertGreater(stats['total_entities'], 0)


if __name__ == '__main__':
    unittest.main()
