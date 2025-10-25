"""
Base agent class for HealthSync system.
Provides common functionality for all agents including uAgents integration,
Chat Protocol support, and error handling.
"""

from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
from typing import Dict, Any, Optional, Callable, List
import asyncio
from datetime import datetime
import uuid
import json
from aiohttp import web
import aiohttp

from .protocols.chat_protocol import ChatProtocolHandler, ChatMessage, ChatResponse
from .protocols.agent_messages import AgentMessage, AgentAcknowledgment, MessageTypes
from .protocols.communication_manager import CommunicationManager, DeliveryPriority
from .protocols.message_delivery import MessageStatus
from .utils.logging import get_logger
from .utils.error_handling import ErrorRecoveryManager, with_error_handling


class HealthSyncBaseAgent:
    """Base class for all HealthSync agents with uAgents integration."""
    
    def __init__(self, name: str, seed: str = None, port: int = None, endpoint: str = None):
        self.name = name
        self.agent_id = f"healthsync_{name.lower().replace(' ', '_')}"
        self.port = port
        
        # Initialize uAgents agent
        self.agent = Agent(
            name=self.agent_id,
            seed=seed or self.agent_id,
            port=port,
            endpoint=endpoint
        )
        
        # Initialize logging and error handling
        self.logger = get_logger(self.agent_id)
        self.error_manager = ErrorRecoveryManager(self.agent_id)
        
        # Initialize Chat Protocol handler
        self.chat_handler = ChatProtocolHandler(self.agent_id)
        
        # Initialize enhanced communication manager
        self.comm_manager = CommunicationManager(self.agent_id)
        
        # Message handlers registry
        self.message_handlers: Dict[str, Callable] = {}
        
        # Agent state
        self.is_running = False
        self.health_status = "healthy"
        self.last_heartbeat = datetime.utcnow()
        self.start_time = datetime.utcnow()
        
        # HTTP server for health checks and monitoring
        self.http_app = None
        self.http_runner = None
        self.http_site = None
        
        # Setup base handlers
        self._setup_base_handlers()
        self._setup_http_endpoints()
        
        self.logger.info("HealthSync agent initialized", agent_id=self.agent_id)
    
    def _setup_base_handlers(self):
        """Setup base message handlers for all agents."""
        
        @self.agent.on_message(model=AgentMessage)
        async def handle_agent_message(ctx: Context, sender: str, msg: AgentMessage):
            """Handle incoming agent messages."""
            await self._process_agent_message(ctx, sender, msg)
        
        @self.agent.on_message(model=AgentAcknowledgment)
        async def handle_acknowledgment(ctx: Context, sender: str, ack: AgentAcknowledgment):
            """Handle acknowledgments from other agents."""
            await self.comm_manager.handle_acknowledgment(ack)
        
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle incoming chat messages."""
            await self._process_chat_message(ctx, sender, msg)
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            """Handle agent startup."""
            await self._on_startup(ctx)
        
        @self.agent.on_event("shutdown")
        async def shutdown_handler(ctx: Context):
            """Handle agent shutdown."""
            await self._on_shutdown(ctx)
        
        @self.agent.on_interval(period=30.0)  # Health check every 30 seconds
        async def health_check(ctx: Context):
            """Periodic health check."""
            await self._health_check(ctx)
    
    async def _process_agent_message(self, ctx: Context, sender: str, msg: AgentMessage):
        """Process incoming agent message through communication manager."""
        try:
            self.logger.message_log(
                direction="received",
                message_type=msg.message_type,
                message_id=msg.message_id,
                sender=sender,
                recipient=self.agent_id
            )
            
            # Process through communication manager
            response_data = await self.comm_manager.handle_incoming_message(sender, msg)
            
            # Send acknowledgment if required
            if msg.requires_acknowledgment:
                ack = AgentAcknowledgment(
                    original_message_id=msg.message_id,
                    sender_agent=self.agent_id,
                    recipient_agent=sender,
                    status="processed" if response_data and "error" not in response_data else "error",
                    response_data=response_data
                )
                await ctx.send(sender, ack)
        
        except Exception as e:
            self.logger.error("Error processing agent message",
                            message_id=msg.message_id,
                            error=str(e))
            
            if msg.requires_acknowledgment:
                ack = AgentAcknowledgment(
                    original_message_id=msg.message_id,
                    sender_agent=self.agent_id,
                    recipient_agent=sender,
                    status="error",
                    response_data={"error": str(e)}
                )
                await ctx.send(sender, ack)
    
    async def _process_chat_message(self, ctx: Context, sender: str, msg: ChatMessage):
        """Process incoming chat message."""
        try:
            self.logger.message_log(
                direction="received",
                message_type="chat_message",
                message_id=msg.message_id,
                sender=sender,
                recipient=self.agent_id
            )
            
            # Process through chat handler
            response = await self.chat_handler.handle_message(msg)
            
            # Send response back
            await ctx.send(sender, response)
            
        except Exception as e:
            self.logger.error("Error processing chat message",
                            message_id=msg.message_id,
                            error=str(e))
    
    async def _on_startup(self, ctx: Context):
        """Handle agent startup."""
        self.is_running = True
        self.health_status = "healthy"
        self.last_heartbeat = datetime.utcnow()
        
        # Fund agent if needed
        fund_agent_if_low(ctx.wallet.address())
        
        # Start HTTP server for health checks
        if self.port and self.http_app:
            await self._start_http_server()
        
        # Start communication manager
        self.comm_manager.context = ctx
        await self.comm_manager.start()
        
        self.logger.info("Agent started successfully",
                        address=ctx.address,
                        wallet_address=ctx.wallet.address(),
                        http_port=self.port)
        
        # Call custom startup handler
        await self.on_startup(ctx)
    
    async def _on_shutdown(self, ctx: Context):
        """Handle agent shutdown."""
        self.is_running = False
        self.health_status = "shutdown"
        
        # Stop HTTP server
        await self._stop_http_server()
        
        # Stop communication manager
        await self.comm_manager.stop()
        
        self.logger.info("Agent shutting down")
        
        # Call custom shutdown handler
        await self.on_shutdown(ctx)
    
    async def _health_check(self, ctx: Context):
        """Perform health check."""
        self.last_heartbeat = datetime.utcnow()
        
        # Update health status based on error rate
        error_stats = self.error_manager.get_error_statistics()
        recent_errors = error_stats.get("recent_errors_1h", 0)
        
        if recent_errors > 10:
            self.health_status = "degraded"
        elif recent_errors > 5:
            self.health_status = "warning"
        else:
            self.health_status = "healthy"
        
        self.logger.debug("Health check completed",
                         status=self.health_status,
                         recent_errors=recent_errors)
        
        # Call custom health check
        await self.on_health_check(ctx)
    
    def _setup_http_endpoints(self):
        """Setup HTTP endpoints for health checks and monitoring."""
        self.http_app = web.Application()
        
        # Health check endpoint
        self.http_app.router.add_get('/health', self._handle_health_check)
        
        # Agent info endpoint
        self.http_app.router.add_get('/info', self._handle_agent_info)
        
        # Status endpoint
        self.http_app.router.add_get('/status', self._handle_status)
        
        # Metrics endpoint
        self.http_app.router.add_get('/metrics', self._handle_metrics)
    
    async def _handle_health_check(self, request):
        """Handle HTTP health check requests."""
        try:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            health_data = {
                "status": self.health_status,
                "agent_id": self.agent_id,
                "name": self.name,
                "is_running": self.is_running,
                "last_heartbeat": self.last_heartbeat.isoformat(),
                "uptime_seconds": uptime,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add custom health metrics
            custom_health = await self.get_custom_health_metrics()
            if custom_health:
                health_data.update(custom_health)
            
            status_code = 200 if self.health_status == "healthy" else 503
            
            return web.json_response(health_data, status=status_code)
            
        except Exception as e:
            self.logger.error("Health check endpoint error", error=str(e))
            return web.json_response(
                {"status": "error", "error": str(e)}, 
                status=500
            )
    
    async def _handle_agent_info(self, request):
        """Handle agent info requests."""
        try:
            info = self.get_agent_info()
            return web.json_response(info)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_status(self, request):
        """Handle status requests."""
        try:
            status = {
                "agent_id": self.agent_id,
                "name": self.name,
                "status": self.health_status,
                "is_running": self.is_running,
                "address": self.agent.address,
                "port": self.port,
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                "message_stats": self.comm_manager.get_statistics() if hasattr(self.comm_manager, 'get_statistics') else {},
                "error_stats": self.error_manager.get_error_statistics(),
                "timestamp": datetime.utcnow().isoformat()
            }
            return web.json_response(status)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_metrics(self, request):
        """Handle metrics requests."""
        try:
            metrics = {
                "agent_id": self.agent_id,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "health_status": self.health_status,
                "is_running": self.is_running,
                "last_heartbeat": self.last_heartbeat.isoformat(),
                "error_count": self.error_manager.get_error_statistics().get("total_errors", 0),
                "message_count": getattr(self.comm_manager, 'message_count', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add custom metrics
            custom_metrics = await self.get_custom_metrics()
            if custom_metrics:
                metrics.update(custom_metrics)
            
            return web.json_response(metrics)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message type."""
        self.comm_manager.register_message_handler(message_type, handler)
        self.logger.info("Message handler registered",
                        message_type=message_type)
    
    async def send_message(self, ctx: Context, recipient: str, message_type: str, 
                          payload: Dict[str, Any], requires_ack: bool = True,
                          priority: DeliveryPriority = DeliveryPriority.NORMAL,
                          ordered_group: Optional[str] = None) -> Optional[str]:
        """Send message to another agent with enhanced reliability."""
        try:
            message_id = await self.comm_manager.send_message(
                recipient=recipient,
                message_type=message_type,
                payload=payload,
                priority=priority,
                requires_ack=requires_ack,
                ordered_group=ordered_group
            )
            
            self.logger.message_log(
                direction="sent",
                message_type=message_type,
                message_id=message_id,
                sender=self.agent_id,
                recipient=recipient
            )
            
            return message_id
        except Exception as e:
            self.logger.error("Failed to send message",
                            recipient=recipient,
                            message_type=message_type,
                            error=str(e))
            raise
    
    async def send_request_response(self, ctx: Context, recipient: str, 
                                  message_type: str, payload: Dict[str, Any],
                                  timeout: float = 30.0) -> Dict[str, Any]:
        """Send message and wait for response."""
        return await self.comm_manager.send_request_response(
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            timeout=timeout
        )
    
    async def broadcast_message(self, ctx: Context, message_type: str,
                              payload: Dict[str, Any],
                              recipients: Optional[List[str]] = None) -> List[str]:
        """Broadcast message to multiple recipients."""
        return await self.comm_manager.broadcast_message(
            message_type=message_type,
            payload=payload,
            recipients=recipients
        )
    
    def run(self, **kwargs):
        """Run the agent."""
        self.logger.info("Starting agent", agent_id=self.agent_id)
        self.agent.run(**kwargs)
    
    # Override these methods in subclasses
    async def on_startup(self, ctx: Context):
        """Custom startup logic - override in subclasses."""
        pass
    
    async def on_shutdown(self, ctx: Context):
        """Custom shutdown logic - override in subclasses."""
        pass
    
    async def on_health_check(self, ctx: Context):
        """Custom health check logic - override in subclasses."""
        pass
    
    async def get_custom_health_metrics(self) -> Optional[Dict[str, Any]]:
        """Get custom health metrics - override in subclasses."""
        return None
    
    async def get_custom_metrics(self) -> Optional[Dict[str, Any]]:
        """Get custom metrics - override in subclasses."""
        return None
    
    async def _start_http_server(self):
        """Start HTTP server for health checks."""
        try:
            if not self.http_app:
                return
            
            # Create HTTP server
            self.http_runner = web.AppRunner(self.http_app)
            await self.http_runner.setup()
            
            # Start server on specified port + 1000 (to avoid conflicts with uAgents)
            http_port = self.port + 1000 if self.port else 9000
            self.http_site = web.TCPSite(self.http_runner, 'localhost', http_port)
            await self.http_site.start()
            
            self.logger.info("HTTP server started", 
                           port=http_port,
                           health_endpoint=f"http://localhost:{http_port}/health")
            
        except Exception as e:
            self.logger.error("Failed to start HTTP server", error=str(e))
    
    async def _stop_http_server(self):
        """Stop HTTP server."""
        try:
            if self.http_site:
                await self.http_site.stop()
                self.http_site = None
            
            if self.http_runner:
                await self.http_runner.cleanup()
                self.http_runner = None
            
            self.logger.info("HTTP server stopped")
            
        except Exception as e:
            self.logger.error("Error stopping HTTP server", error=str(e))
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information for monitoring."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "address": self.agent.address,
            "is_running": self.is_running,
            "health_status": self.health_status,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "registered_handlers": list(self.message_handlers.keys()),
            "error_stats": self.error_manager.get_error_statistics()
        }


# Agent manifest template for Agentverse registration
AGENT_MANIFEST_TEMPLATE = {
    "version": "1.0.0",
    "name": "{agent_name}",
    "description": "{agent_description}",
    "author": "HealthSync Team",
    "license": "MIT",
    "aea_version": ">=1.0.0",
    "fingerprint": {},
    "fingerprint_ignore_patterns": [],
    "connections": ["fetchai/http_client:0.24.0"],
    "contracts": [],
    "protocols": ["fetchai/default:1.0.0"],
    "skills": [],
    "default_connection": "fetchai/http_client:0.24.0",
    "default_ledger": "fetchai",
    "required_ledgers": ["fetchai"],
    "default_routing": {},
    "connection_private_key_paths": {},
    "private_key_paths": {},
    "logging_config": {
        "disable_existing_loggers": False,
        "version": 1
    },
    "badges": [
        "Innovation Lab",
        "ASI Alliance Hackathon"
    ],
    "chat_protocol_enabled": True,
    "agentverse_compatible": True
}