"""
Chat Protocol integration for ASI:One compatibility.
Handles natural language interactions with HealthSync agents.
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
from datetime import datetime
import uuid


class ChatMessage(BaseModel):
    """Standard chat message format for ASI:One integration."""
    message_id: str = None
    session_id: str
    user_id: str
    agent_id: str
    content_type: str  # "text", "structured_data", "command"
    content_data: Union[str, Dict[str, Any]]
    metadata: Dict[str, Any] = {}
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get('message_id') is None:
            data['message_id'] = str(uuid.uuid4())
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class ChatSession(BaseModel):
    """Chat session management for patient and researcher interactions."""
    session_id: str = None
    user_id: str
    agent_id: str
    session_type: str  # "patient_consent", "research_query"
    context: Dict[str, Any] = {}
    active: bool = True
    created_at: datetime = None
    
    def __init__(self, **data):
        if data.get('session_id') is None:
            data['session_id'] = str(uuid.uuid4())
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)


class ChatResponse(BaseModel):
    """Standardized response format for chat interactions."""
    response_id: str = None
    original_message_id: str
    agent_id: str
    response_type: str  # "acknowledgment", "data", "error", "question"
    response_data: Union[str, Dict[str, Any]]
    requires_followup: bool = False
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get('response_id') is None:
            data['response_id'] = str(uuid.uuid4())
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class ChatProtocolHandler:
    """Base handler for Chat Protocol integration."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.active_sessions: Dict[str, ChatSession] = {}
    
    async def handle_message(self, message: ChatMessage) -> ChatResponse:
        """Process incoming chat message and generate response."""
        try:
            # Validate session
            if message.session_id not in self.active_sessions:
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="error",
                    response_data="Session not found. Please start a new session."
                )
            
            # Process message based on content type
            if message.content_type == "text":
                return await self._handle_text_message(message)
            elif message.content_type == "structured_data":
                return await self._handle_structured_data(message)
            elif message.content_type == "command":
                return await self._handle_command(message)
            else:
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="error",
                    response_data=f"Unsupported content type: {message.content_type}"
                )
                
        except Exception as e:
            return ChatResponse(
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                response_type="error",
                response_data=f"Error processing message: {str(e)}"
            )
    
    async def _handle_text_message(self, message: ChatMessage) -> ChatResponse:
        """Handle natural language text messages."""
        # Base implementation - to be overridden by specific agents
        return ChatResponse(
            original_message_id=message.message_id,
            agent_id=self.agent_id,
            response_type="acknowledgment",
            response_data="Message received and processed."
        )
    
    async def _handle_structured_data(self, message: ChatMessage) -> ChatResponse:
        """Handle structured data messages."""
        # Base implementation - to be overridden by specific agents
        return ChatResponse(
            original_message_id=message.message_id,
            agent_id=self.agent_id,
            response_type="acknowledgment",
            response_data="Structured data received and processed."
        )
    
    async def _handle_command(self, message: ChatMessage) -> ChatResponse:
        """Handle command messages."""
        # Base implementation - to be overridden by specific agents
        return ChatResponse(
            original_message_id=message.message_id,
            agent_id=self.agent_id,
            response_type="acknowledgment",
            response_data="Command received and processed."
        )
    
    def create_session(self, user_id: str, session_type: str) -> ChatSession:
        """Create new chat session."""
        session = ChatSession(
            user_id=user_id,
            agent_id=self.agent_id,
            session_type=session_type
        )
        self.active_sessions[session.session_id] = session
        return session
    
    def close_session(self, session_id: str) -> bool:
        """Close chat session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].active = False
            del self.active_sessions[session_id]
            return True
        return False