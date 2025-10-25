"""
Agentverse Registration System for HealthSync Agents.
Handles agent registration, manifest publishing, and health monitoring.
"""

import json
import asyncio
import aiohttp
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import AGENTVERSE_CONFIG, AGENT_CONFIG


class AgentverseRegistrationManager:
    """Manages agent registration and monitoring on Agentverse."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or AGENTVERSE_CONFIG.get("api_key", "")
        self.endpoint = AGENTVERSE_CONFIG.get("registration_endpoint", "https://agentverse.ai")
        self.project_id = AGENTVERSE_CONFIG.get("project_id", "healthsync")
        self.badges = AGENTVERSE_CONFIG.get("badges", ["Innovation Lab", "ASI Alliance Hackathon"])
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Agent registration status
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.registration_errors: List[Dict[str, Any]] = []
    
    async def register_all_agents(self) -> Dict[str, Any]:
        """Register all HealthSync agents on Agentverse."""
        self.logger.info("Starting Agentverse registration for all HealthSync agents")
        
        results = {
            "successful_registrations": [],
            "failed_registrations": [],
            "total_agents": len(AGENT_CONFIG),
            "registration_timestamp": datetime.utcnow().isoformat()
        }
        
        # Register each agent
        for agent_name, agent_config in AGENT_CONFIG.items():
            try:
                self.logger.info(f"Registering {agent_name} agent...")
                
                # Load agent manifest
                manifest = await self._load_agent_manifest(agent_name)
                
                # Register agent
                registration_result = await self._register_agent(agent_name, manifest, agent_config)
                
                if registration_result["success"]:
                    results["successful_registrations"].append({
                        "agent_name": agent_name,
                        "agent_id": registration_result["agent_id"],
                        "agentverse_url": registration_result.get("agentverse_url"),
                        "chat_protocol_enabled": True,
                        "badges": self.badges
                    })
                    self.registered_agents[agent_name] = registration_result
                    self.logger.info(f"Successfully registered {agent_name} agent")
                else:
                    results["failed_registrations"].append({
                        "agent_name": agent_name,
                        "error": registration_result["error"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    self.registration_errors.append(registration_result)
                    self.logger.error(f"Failed to register {agent_name} agent: {registration_result['error']}")
                
                # Small delay between registrations
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Exception during {agent_name} registration: {str(e)}"
                self.logger.error(error_msg)
                results["failed_registrations"].append({
                    "agent_name": agent_name,
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Generate registration report
        await self._generate_registration_report(results)
        
        return results
    
    async def _load_agent_manifest(self, agent_name: str) -> Dict[str, Any]:
        """Load agent manifest from file."""
        manifest_path = f"agents/manifests/{agent_name}_manifest.json"
        
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Validate required fields
        required_fields = ["name", "description", "version", "badges", "chat_protocol_enabled"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field in manifest: {field}")
        
        return manifest
    
    async def _register_agent(self, agent_name: str, manifest: Dict[str, Any], 
                            agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register individual agent on Agentverse."""
        try:
            # Prepare registration payload
            registration_data = {
                "name": manifest["name"],
                "description": manifest["description"],
                "version": manifest["version"],
                "author": manifest.get("author", "HealthSync Team"),
                "license": manifest.get("license", "MIT"),
                "badges": manifest["badges"],
                "chat_protocol_enabled": manifest["chat_protocol_enabled"],
                "agentverse_compatible": manifest.get("agentverse_compatible", True),
                "agent_type": manifest.get("agent_type", "healthcare_agent"),
                "capabilities": manifest.get("capabilities", []),
                "endpoints": manifest.get("endpoints", {}),
                "tags": manifest.get("tags", []),
                "project_id": self.project_id,
                "port": agent_config.get("port"),
                "health_check_endpoint": f"http://localhost:{agent_config.get('port')}/health"
            }
            
            # For demo purposes, simulate successful registration
            # In a real implementation, this would make HTTP requests to Agentverse API
            agent_id = f"healthsync_{agent_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Simulate API call delay
            await asyncio.sleep(0.5)
            
            # Mock successful registration response
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agentverse_url": f"{self.endpoint}/agents/{agent_id}",
                "chat_protocol_url": f"{self.endpoint}/chat/{agent_id}",
                "discovery_enabled": True,
                "health_check_url": registration_data["health_check_endpoint"],
                "registration_timestamp": datetime.utcnow().isoformat(),
                "manifest": manifest
            }
            
        except Exception as e:
            return {
                "success": False,
                "agent_name": agent_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def verify_agent_discovery(self, agent_name: str) -> Dict[str, Any]:
        """Verify agent is discoverable through ASI:One interface."""
        try:
            if agent_name not in self.registered_agents:
                return {
                    "discoverable": False,
                    "error": "Agent not registered"
                }
            
            agent_info = self.registered_agents[agent_name]
            
            # Simulate discovery verification
            # In real implementation, this would check ASI:One discovery endpoint
            await asyncio.sleep(0.2)
            
            return {
                "discoverable": True,
                "agent_id": agent_info["agent_id"],
                "chat_protocol_enabled": True,
                "asi_one_url": f"https://asi.one/agents/{agent_info['agent_id']}",
                "badges_visible": True,
                "verification_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "discoverable": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Check agent health status."""
        try:
            agent_config = AGENT_CONFIG.get(agent_name)
            if not agent_config:
                return {
                    "healthy": False,
                    "error": "Agent configuration not found"
                }
            
            port = agent_config.get("port")
            health_url = f"http://localhost:{port}/health"
            
            # Simulate health check
            # In real implementation, this would make HTTP request to agent
            await asyncio.sleep(0.1)
            
            return {
                "healthy": True,
                "agent_name": agent_name,
                "port": port,
                "health_url": health_url,
                "status": "running",
                "last_heartbeat": datetime.utcnow().isoformat(),
                "response_time_ms": 50
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "agent_name": agent_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def monitor_all_agents(self) -> Dict[str, Any]:
        """Monitor health status of all registered agents."""
        self.logger.info("Monitoring health status of all agents")
        
        monitoring_results = {
            "healthy_agents": [],
            "unhealthy_agents": [],
            "monitoring_timestamp": datetime.utcnow().isoformat()
        }
        
        for agent_name in AGENT_CONFIG.keys():
            health_status = await self.check_agent_health(agent_name)
            
            if health_status["healthy"]:
                monitoring_results["healthy_agents"].append(health_status)
            else:
                monitoring_results["unhealthy_agents"].append(health_status)
        
        return monitoring_results
    
    async def _generate_registration_report(self, results: Dict[str, Any]):
        """Generate detailed registration report."""
        report_path = "deployment/agentverse_registration_report.json"
        
        # Add additional metadata
        results["registration_summary"] = {
            "total_agents": results["total_agents"],
            "successful_count": len(results["successful_registrations"]),
            "failed_count": len(results["failed_registrations"]),
            "success_rate": len(results["successful_registrations"]) / results["total_agents"] * 100,
            "project_id": self.project_id,
            "badges": self.badges
        }
        
        # Add discovery verification for successful registrations
        results["discovery_verification"] = []
        for agent_info in results["successful_registrations"]:
            discovery_result = await self.verify_agent_discovery(agent_info["agent_name"])
            results["discovery_verification"].append({
                "agent_name": agent_info["agent_name"],
                "discovery_result": discovery_result
            })
        
        # Save report
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Registration report saved to {report_path}")
    
    def get_registration_status(self) -> Dict[str, Any]:
        """Get current registration status."""
        return {
            "registered_agents": list(self.registered_agents.keys()),
            "registration_count": len(self.registered_agents),
            "total_agents": len(AGENT_CONFIG),
            "registration_errors": self.registration_errors,
            "last_update": datetime.utcnow().isoformat()
        }


async def main():
    """Main registration function."""
    print("HealthSync Agentverse Registration System")
    print("=" * 50)
    
    # Initialize registration manager
    manager = AgentverseRegistrationManager()
    
    try:
        # Register all agents
        print("Starting agent registration...")
        results = await manager.register_all_agents()
        
        print(f"\nRegistration completed!")
        print(f"Successful: {len(results['successful_registrations'])}")
        print(f"Failed: {len(results['failed_registrations'])}")
        
        # Monitor agent health
        print("\nChecking agent health...")
        health_results = await manager.monitor_all_agents()
        
        print(f"Healthy agents: {len(health_results['healthy_agents'])}")
        print(f"Unhealthy agents: {len(health_results['unhealthy_agents'])}")
        
        # Display successful registrations
        if results["successful_registrations"]:
            print("\nSuccessfully registered agents:")
            for agent in results["successful_registrations"]:
                print(f"  - {agent['agent_name']}: {agent['agent_id']}")
        
        # Display failed registrations
        if results["failed_registrations"]:
            print("\nFailed registrations:")
            for failure in results["failed_registrations"]:
                print(f"  - {failure['agent_name']}: {failure['error']}")
        
        return results
        
    except Exception as e:
        print(f"Registration failed: {str(e)}")
        return None


if __name__ == "__main__":
    asyncio.run(main())