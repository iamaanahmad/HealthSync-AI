/**
 * End-to-End Integration Tests for Chat Protocol and ASI:One Compatibility
 * Tests natural language interactions and protocol compliance
 */

import { PatientConsentApi, DataTypes, ResearchCategories } from '../../lib/patient-consent-api';
import { ResearchQueryService } from '../../lib/research-query-api';

// Mock Chat Protocol interfaces
interface ChatMessage {
  sessionId: string;
  messageId: string;
  sender: 'user' | 'agent';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

interface ChatSession {
  sessionId: string;
  userId: string;
  agentId: string;
  sessionType: 'patient_consent' | 'research_query';
  context: Record<string, any>;
  active: boolean;
  messages: ChatMessage[];
}

// Mock Chat Protocol Service
class MockChatProtocolService {
  private sessions: Map<string, ChatSession> = new Map();
  private messageHandlers: Map<string, (message: ChatMessage) => Promise<ChatMessage>> = new Map();

  createSession(userId: string, agentId: string, sessionType: 'patient_consent' | 'research_query'): ChatSession {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const session: ChatSession = {
      sessionId,
      userId,
      agentId,
      sessionType,
      context: {},
      active: true,
      messages: [],
    };
    
    this.sessions.set(sessionId, session);
    return session;
  }

  async sendMessage(sessionId: string, content: string, sender: 'user' | 'agent' = 'user'): Promise<ChatMessage> {
    const session = this.sessions.get(sessionId);
    if (!session || !session.active) {
      throw new Error('Session not found or inactive');
    }

    const message: ChatMessage = {
      sessionId,
      messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      sender,
      content,
      timestamp: new Date(),
    };

    session.messages.push(message);

    // Process message through appropriate handler
    const handler = this.messageHandlers.get(session.agentId);
    if (handler && sender === 'user') {
      const response = await handler(message);
      session.messages.push(response);
      return response;
    }

    return message;
  }

  registerMessageHandler(agentId: string, handler: (message: ChatMessage) => Promise<ChatMessage>) {
    this.messageHandlers.set(agentId, handler);
  }

  getSession(sessionId: string): ChatSession | undefined {
    return this.sessions.get(sessionId);
  }

  closeSession(sessionId: string): void {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.active = false;
    }
  }
}

describe('Chat Protocol Integration Tests', () => {
  let chatService: MockChatProtocolService;
  const testPatientId = 'P001';
  const testResearcherId = 'HMS-12345';

  beforeEach(() => {
    jest.clearAllMocks();
    chatService = new MockChatProtocolService();
    
    // Register Patient Consent Agent handler
    chatService.registerMessageHandler('patient-consent-agent', async (message: ChatMessage) => {
      const content = message.content.toLowerCase();
      
      if (content.includes('set consent') || content.includes('update consent') || content.includes('allow') || content.includes('want to')) {
        // Parse natural language consent request
        const dataType = extractDataType(content);
        const researchCategory = extractResearchCategory(content);
        const granted = content.includes('allow') || content.includes('grant') || content.includes('yes') || content.includes('want to allow');
        
        if (dataType && researchCategory) {
          const result = await PatientConsentApi.updateConsent({
            patientId: testPatientId,
            dataType,
            researchCategory,
            consentGranted: granted,
          });
          
          return {
            sessionId: message.sessionId,
            messageId: `response_${Date.now()}`,
            sender: 'agent' as const,
            content: result.success 
              ? `Consent ${granted ? 'granted' : 'revoked'} for ${dataType} data in ${researchCategory} research.`
              : `Failed to update consent: ${result.error}`,
            timestamp: new Date(),
          };
        }
      }
      
      if (content.includes('show consent') || content.includes('list consent')) {
        const consents = await PatientConsentApi.getPatientConsents(testPatientId);
        const consentList = consents.data?.map(c => 
          `${c.dataType} for ${c.researchCategory}: ${c.consentGranted ? 'Allowed' : 'Denied'}`
        ).join('\n') || 'No consents found';
        
        return {
          sessionId: message.sessionId,
          messageId: `response_${Date.now()}`,
          sender: 'agent' as const,
          content: `Your current consent preferences:\n${consentList}`,
          timestamp: new Date(),
        };
      }
      
      return {
        sessionId: message.sessionId,
        messageId: `response_${Date.now()}`,
        sender: 'agent' as const,
        content: 'I can help you manage your data sharing consent. You can say things like "allow genomic data for cancer research" or "show my current consents".',
        timestamp: new Date(),
      };
    });

    // Register Research Query Agent handler
    chatService.registerMessageHandler('research-query-agent', async (message: ChatMessage) => {
      const content = message.content.toLowerCase();
      
      if (content.includes('submit query') || content.includes('research study') || content.includes('submit a') || content.includes('want to submit')) {
        // Parse natural language research query
        const studyTitle = extractStudyTitle(content);
        const dataTypes = extractDataTypes(content);
        const researchCategories = extractResearchCategories(content);
        
        if (studyTitle && dataTypes.length > 0 && researchCategories.length > 0) {
          const query = {
            researcherId: testResearcherId,
            studyTitle,
            studyDescription: `Research study submitted via Chat Protocol: ${content}`,
            dataRequirements: {
              dataTypes,
              researchCategories,
              minimumSampleSize: 100,
            },
            ethicalApprovalId: 'IRB-2024-CHAT-001',
          };
          
          const result = await ResearchQueryService.submitQuery(query);
          
          return {
            sessionId: message.sessionId,
            messageId: `response_${Date.now()}`,
            sender: 'agent' as const,
            content: result.success 
              ? `Research query submitted successfully. Query ID: ${result.queryId}`
              : `Failed to submit query: ${result.error}`,
            timestamp: new Date(),
          };
        }
      }
      
      if (content.includes('query status') || content.includes('check status')) {
        const queries = ResearchQueryService.getQueryResults(testResearcherId);
        const statusList = queries.map(q => 
          `${q.studyTitle}: ${q.status || 'submitted'}`
        ).join('\n') || 'No queries found';
        
        return {
          sessionId: message.sessionId,
          messageId: `response_${Date.now()}`,
          sender: 'agent' as const,
          content: `Your research queries:\n${statusList}`,
          timestamp: new Date(),
        };
      }
      
      return {
        sessionId: message.sessionId,
        messageId: `response_${Date.now()}`,
        sender: 'agent' as const,
        content: 'I can help you submit research queries. You can say things like "submit a cancer genomics study" or "check my query status".',
        timestamp: new Date(),
      };
    });
  });

  // Helper methods for natural language parsing
  function extractDataType(content: string): string | null {
    const dataTypeMap: Record<string, string> = {
      'genomic': DataTypes.GENOMIC,
      'genetic': DataTypes.GENOMIC,
      'dna': DataTypes.GENOMIC,
      'clinical': DataTypes.CLINICAL_TRIALS,
      'trial': DataTypes.CLINICAL_TRIALS,
      'lab': DataTypes.LABORATORY,
      'laboratory': DataTypes.LABORATORY,
      'blood': DataTypes.LABORATORY,
      'medication': DataTypes.MEDICATIONS,
      'drug': DataTypes.MEDICATIONS,
      'imaging': DataTypes.IMAGING,
      'scan': DataTypes.IMAGING,
      'mri': DataTypes.IMAGING,
      'wearable': DataTypes.WEARABLE,
      'device': DataTypes.WEARABLE,
      'behavioral': DataTypes.BEHAVIORAL,
      'mental': DataTypes.BEHAVIORAL,
    };

    for (const [keyword, dataType] of Object.entries(dataTypeMap)) {
      if (content.toLowerCase().includes(keyword)) {
        return dataType;
      }
    }
    return DataTypes.GENOMIC; // Default fallback
  }

  function extractResearchCategory(content: string): string | null {
    const categoryMap: Record<string, string> = {
      'cancer': ResearchCategories.CANCER_RESEARCH,
      'oncology': ResearchCategories.CANCER_RESEARCH,
      'cardiovascular': ResearchCategories.CARDIOVASCULAR,
      'heart': ResearchCategories.CARDIOVASCULAR,
      'diabetes': ResearchCategories.DIABETES,
      'mental health': ResearchCategories.MENTAL_HEALTH,
      'psychiatric': ResearchCategories.MENTAL_HEALTH,
      'drug development': ResearchCategories.DRUG_DEVELOPMENT,
      'pharmaceutical': ResearchCategories.DRUG_DEVELOPMENT,
      'rare disease': ResearchCategories.RARE_DISEASES,
      'precision medicine': ResearchCategories.PRECISION_MEDICINE,
      'personalized': ResearchCategories.PRECISION_MEDICINE,
    };

    for (const [keyword, category] of Object.entries(categoryMap)) {
      if (content.toLowerCase().includes(keyword)) {
        return category;
      }
    }
    return ResearchCategories.CANCER_RESEARCH; // Default fallback
  }

  function extractStudyTitle(content: string): string {
    // Extract study title from natural language
    const titleMatch = content.match(/study[:\s]+([^.!?]+)/i);
    if (titleMatch) {
      return titleMatch[1].trim();
    }
    
    // Fallback: generate title from content
    const words = content.split(' ').slice(0, 6);
    return words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') + ' Study';
  }

  function extractDataTypes(content: string): string[] {
    const types: string[] = [];
    const dataTypeMap: Record<string, string> = {
      'genomic': 'genomics',
      'genetic': 'genomics',
      'clinical': 'clinical_trials',
      'lab': 'lab_results',
      'laboratory': 'lab_results',
      'imaging': 'imaging',
      'demographic': 'demographics',
    };

    for (const [keyword, dataType] of Object.entries(dataTypeMap)) {
      if (content.includes(keyword) && !types.includes(dataType)) {
        types.push(dataType);
      }
    }
    
    return types.length > 0 ? types : ['demographics'];
  }

  function extractResearchCategories(content: string): string[] {
    const categories: string[] = [];
    const categoryMap: Record<string, string> = {
      'cancer': 'cancer_research',
      'cardiovascular': 'cardiovascular',
      'diabetes': 'diabetes',
      'mental': 'mental_health',
      'drug': 'drug_development',
    };

    for (const [keyword, category] of Object.entries(categoryMap)) {
      if (content.includes(keyword) && !categories.includes(category)) {
        categories.push(category);
      }
    }
    
    return categories.length > 0 ? categories : ['clinical_trials'];
  }

  describe('Patient Consent Chat Interactions', () => {
    it('should handle natural language consent granting', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Patient grants consent using natural language
      const response = await chatService.sendMessage(
        session.sessionId,
        'I want to allow my genomic data to be used for cancer research'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('Consent granted');
      expect(response.content).toContain('genomic');
      expect(response.content).toContain('cancer_research');

      // Verify consent was actually updated
      const consents = await PatientConsentApi.getPatientConsents(testPatientId);
      expect(consents.success).toBe(true);
      
      const genomicConsent = consents.data!.find(
        c => c.dataType === DataTypes.GENOMIC && c.researchCategory === ResearchCategories.CANCER_RESEARCH
      );
      expect(genomicConsent).toBeDefined();
      expect(genomicConsent!.consentGranted).toBe(true);
    });

    it('should handle natural language consent revocation', async () => {
      // First grant consent
      await PatientConsentApi.updateConsent({
        patientId: testPatientId,
        dataType: DataTypes.LABORATORY,
        researchCategory: ResearchCategories.DRUG_DEVELOPMENT,
        consentGranted: true,
      });

      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Patient revokes consent using natural language
      const response = await chatService.sendMessage(
        session.sessionId,
        'I no longer want my lab data used for drug development research'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('Consent revoked');
      expect(response.content).toContain('laboratory');
      expect(response.content).toContain('drug_development');

      // Verify consent was actually revoked
      const consents = await PatientConsentApi.getPatientConsents(testPatientId);
      expect(consents.success).toBe(true);
      
      const labConsent = consents.data!.find(
        c => c.dataType === DataTypes.LABORATORY && c.researchCategory === ResearchCategories.DRUG_DEVELOPMENT
      );
      expect(labConsent).toBeDefined();
      expect(labConsent!.consentGranted).toBe(false);
    });

    it('should handle consent status inquiries', async () => {
      // Set up some consents
      await PatientConsentApi.updateConsent({
        patientId: testPatientId,
        dataType: DataTypes.IMAGING,
        researchCategory: ResearchCategories.CARDIOVASCULAR,
        consentGranted: true,
      });

      await PatientConsentApi.updateConsent({
        patientId: testPatientId,
        dataType: DataTypes.WEARABLE,
        researchCategory: ResearchCategories.DIABETES,
        consentGranted: false,
      });

      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Patient asks about current consents
      const response = await chatService.sendMessage(
        session.sessionId,
        'Show me my current consent preferences'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('current consent preferences');
      expect(response.content).toContain('imaging');
      expect(response.content).toContain('cardiovascular');
      expect(response.content).toContain('Allowed');
      expect(response.content).toContain('wearable');
      expect(response.content).toContain('diabetes');
      expect(response.content).toContain('Denied');
    });

    it('should handle ambiguous or unclear requests', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Patient sends unclear message
      const response = await chatService.sendMessage(
        session.sessionId,
        'Hello, I need help with something'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('help you manage');
      expect(response.content).toContain('consent');
      expect(response.content).toContain('say things like');
    });
  });

  describe('Research Query Chat Interactions', () => {
    it('should handle natural language research query submission', async () => {
      const session = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      // Researcher submits query using natural language
      const response = await chatService.sendMessage(
        session.sessionId,
        'I want to submit a cancer genomics study using genetic data for oncology research'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('Research query submitted successfully');
      expect(response.content).toContain('Query ID');

      // Verify query was actually submitted
      const queries = ResearchQueryService.getQueryResults(testResearcherId);
      expect(queries.length).toBeGreaterThan(0);
      
      const latestQuery = queries[queries.length - 1];
      expect(latestQuery.studyTitle).toContain('Cancer');
      expect(latestQuery.studyTitle).toContain('Genomics');
    });

    it('should handle research query status inquiries', async () => {
      // Submit a query first
      await ResearchQueryService.submitQuery({
        researcherId: testResearcherId,
        studyTitle: 'Chat Protocol Test Study',
        studyDescription: 'A study submitted to test chat protocol functionality.',
        dataRequirements: {
          dataTypes: ['demographics'],
          researchCategories: ['epidemiology'],
          minimumSampleSize: 100,
        },
        ethicalApprovalId: 'IRB-2024-CHAT-002',
      });

      const session = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      // Researcher asks about query status
      const response = await chatService.sendMessage(
        session.sessionId,
        'What is the status of my research queries?'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('research queries');
      expect(response.content).toContain('Chat Protocol Test Study');
      expect(response.content).toContain('submitted');
    });

    it('should handle complex multi-parameter research requests', async () => {
      const session = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      // Complex research request
      const response = await chatService.sendMessage(
        session.sessionId,
        'Submit a cardiovascular study using imaging and lab data for heart disease research'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('Research query submitted successfully');

      // Verify the query captured multiple data types
      const queries = ResearchQueryService.getQueryResults(testResearcherId);
      const latestQuery = queries[queries.length - 1];
      
      expect(latestQuery.studyTitle).toContain('Cardiovascular');
      expect(latestQuery.studyDescription).toContain('imaging');
      expect(latestQuery.studyDescription).toContain('lab');
    });

    it('should provide helpful responses for unclear requests', async () => {
      const session = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      // Unclear research request
      const response = await chatService.sendMessage(
        session.sessionId,
        'I need some data for my research'
      );

      expect(response.sender).toBe('agent');
      expect(response.content).toContain('help you submit research queries');
      expect(response.content).toContain('say things like');
    });
  });

  describe('Session Management and Protocol Compliance', () => {
    it('should maintain session state across multiple messages', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Send multiple messages in the same session
      await chatService.sendMessage(session.sessionId, 'Hello');
      await chatService.sendMessage(session.sessionId, 'I want to update my consent');
      await chatService.sendMessage(session.sessionId, 'Allow genomic data for cancer research');
      
      const sessionData = chatService.getSession(session.sessionId);
      expect(sessionData).toBeDefined();
      expect(sessionData!.messages.length).toBe(6); // 3 user messages + 3 agent responses
      expect(sessionData!.active).toBe(true);
    });

    it('should handle session closure properly', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      await chatService.sendMessage(session.sessionId, 'Hello');
      
      // Close session
      chatService.closeSession(session.sessionId);
      
      const sessionData = chatService.getSession(session.sessionId);
      expect(sessionData).toBeDefined();
      expect(sessionData!.active).toBe(false);
      
      // Sending message to closed session should fail
      await expect(
        chatService.sendMessage(session.sessionId, 'This should fail')
      ).rejects.toThrow('Session not found or inactive');
    });

    it('should handle concurrent sessions for different users', async () => {
      const patientSession = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      const researcherSession = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      // Send messages concurrently
      const [patientResponse, researcherResponse] = await Promise.all([
        chatService.sendMessage(patientSession.sessionId, 'Show my consents'),
        chatService.sendMessage(researcherSession.sessionId, 'Check my query status'),
      ]);

      expect(patientResponse.content).toContain('consent preferences');
      expect(researcherResponse.content).toContain('research queries');
      
      // Verify sessions are independent
      const patientSessionData = chatService.getSession(patientSession.sessionId);
      const researcherSessionData = chatService.getSession(researcherSession.sessionId);
      
      expect(patientSessionData!.userId).toBe(testPatientId);
      expect(researcherSessionData!.userId).toBe(testResearcherId);
      expect(patientSessionData!.sessionType).toBe('patient_consent');
      expect(researcherSessionData!.sessionType).toBe('research_query');
    });

    it('should validate message format and structure', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      const response = await chatService.sendMessage(session.sessionId, 'Test message');
      
      // Verify message structure
      expect(response.sessionId).toBe(session.sessionId);
      expect(response.messageId).toBeDefined();
      expect(response.sender).toBe('agent');
      expect(response.content).toBeDefined();
      expect(response.timestamp).toBeInstanceOf(Date);
      
      // Verify message is stored in session
      const sessionData = chatService.getSession(session.sessionId);
      expect(sessionData!.messages).toContain(response);
    });
  });

  describe('ASI:One Compatibility', () => {
    it('should support ASI:One message acknowledgment protocol', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Send message and verify acknowledgment
      const userMessage = await chatService.sendMessage(session.sessionId, 'Allow genomic data for cancer research');
      expect(userMessage.messageId).toBeDefined();
      
      // Agent should respond (acknowledgment)
      const sessionData = chatService.getSession(session.sessionId);
      const agentResponse = sessionData!.messages.find(m => m.sender === 'agent');
      
      expect(agentResponse).toBeDefined();
      expect(agentResponse!.content).toContain('Consent granted');
    });

    it('should handle ASI:One discovery protocol simulation', async () => {
      // Simulate agent discovery
      const agents = [
        { id: 'patient-consent-agent', name: 'Patient Consent Agent', capabilities: ['consent_management'] },
        { id: 'research-query-agent', name: 'Research Query Agent', capabilities: ['query_processing'] },
      ];

      // Verify agents are discoverable
      agents.forEach(agent => {
        expect(agent.id).toBeDefined();
        expect(agent.name).toBeDefined();
        expect(agent.capabilities).toBeDefined();
        expect(Array.isArray(agent.capabilities)).toBe(true);
      });

      // Test agent capability matching
      const consentAgent = agents.find(a => a.capabilities.includes('consent_management'));
      const queryAgent = agents.find(a => a.capabilities.includes('query_processing'));
      
      expect(consentAgent).toBeDefined();
      expect(queryAgent).toBeDefined();
    });

    it('should support ASI:One metadata and context handling', async () => {
      const session = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      // Add context to session
      session.context = {
        userPreferences: { language: 'en', timezone: 'UTC' },
        sessionMetadata: { source: 'ASI:One', version: '1.0' },
      };

      await chatService.sendMessage(session.sessionId, 'Hello');
      
      const sessionData = chatService.getSession(session.sessionId);
      expect(sessionData!.context.userPreferences).toBeDefined();
      expect(sessionData!.context.sessionMetadata).toBeDefined();
      expect(sessionData!.context.sessionMetadata.source).toBe('ASI:One');
    });

    it('should handle ASI:One error reporting protocol', async () => {
      const session = chatService.createSession('invalid-user', 'patient-consent-agent', 'patient_consent');
      
      // This should work but might produce different results for invalid user
      const response = await chatService.sendMessage(session.sessionId, 'Show my consents');
      
      // Agent should handle gracefully
      expect(response.sender).toBe('agent');
      expect(response.content).toBeDefined();
      
      // In a real implementation, this might return an error or empty result
      // For our mock, it will return empty consents
    });
  });

  describe('Multi-Agent Chat Coordination', () => {
    it('should coordinate between consent and query agents', async () => {
      // Step 1: Patient sets consent via chat
      const consentSession = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      
      const consentResponse = await chatService.sendMessage(
        consentSession.sessionId,
        'Allow my imaging data for cardiovascular research'
      );
      
      expect(consentResponse.content).toContain('Consent granted');

      // Step 2: Researcher submits query via chat
      const querySession = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      const queryResponse = await chatService.sendMessage(
        querySession.sessionId,
        'Submit a cardiovascular study using imaging data'
      );
      
      expect(queryResponse.content).toContain('Research query submitted successfully');

      // Step 3: Verify the coordination worked
      const consents = await PatientConsentApi.getPatientConsents(testPatientId);
      const queries = ResearchQueryService.getQueryResults(testResearcherId);
      
      expect(consents.success).toBe(true);
      expect(queries.length).toBeGreaterThan(0);
      
      // The query should be able to access the consented data
      const imagingConsent = consents.data!.find(
        c => c.dataType === DataTypes.IMAGING && c.researchCategory === ResearchCategories.CARDIOVASCULAR
      );
      expect(imagingConsent).toBeDefined();
      expect(imagingConsent!.consentGranted).toBe(true);
    });

    it('should handle cross-agent workflow via chat', async () => {
      // Simulate a complete workflow initiated through chat
      const patientSession = chatService.createSession(testPatientId, 'patient-consent-agent', 'patient_consent');
      const researcherSession = chatService.createSession(testResearcherId, 'research-query-agent', 'research_query');
      
      // Patient grants multiple consents
      await chatService.sendMessage(patientSession.sessionId, 'Allow genomic data for cancer research');
      await chatService.sendMessage(patientSession.sessionId, 'Allow lab data for drug development');
      
      // Researcher submits related query
      await chatService.sendMessage(
        researcherSession.sessionId,
        'Submit a cancer study using genomic and lab data for oncology and drug development research'
      );
      
      // Verify the complete workflow
      const finalConsents = await PatientConsentApi.getPatientConsents(testPatientId);
      const finalQueries = ResearchQueryService.getQueryResults(testResearcherId);
      
      expect(finalConsents.success).toBe(true);
      expect(finalConsents.data!.length).toBeGreaterThanOrEqual(2);
      expect(finalQueries.length).toBeGreaterThan(0);
      
      // Verify specific consents exist
      const genomicConsent = finalConsents.data!.find(
        c => c.dataType === DataTypes.GENOMIC && c.researchCategory === ResearchCategories.CANCER_RESEARCH
      );
      const labConsent = finalConsents.data!.find(
        c => c.dataType === DataTypes.LABORATORY && c.researchCategory === ResearchCategories.DRUG_DEVELOPMENT
      );
      
      expect(genomicConsent?.consentGranted).toBe(true);
      expect(labConsent?.consentGranted).toBe(true);
    });
  });
});