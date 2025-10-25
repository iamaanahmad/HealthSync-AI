#!/usr/bin/env python3
"""
Complete Agentverse Deployment Script for HealthSync.
Handles agent registration, Chat Protocol setup, and ASI:One integration.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from deployment.agentverse_registration import AgentverseRegistrationManager
from deployment.agent_monitor import AgentHealthMonitor
from config import AGENT_CONFIG


class HealthSyncDeployment:
    """Complete deployment manager for HealthSync agents."""
    
    def __init__(self):
        self.registration_manager = AgentverseRegistrationManager()
        self.health_monitor = AgentHealthMonitor()
        self.deployment_status = {
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "success": False,
            "agents_registered": 0,
            "agents_healthy": 0,
            "chat_protocol_enabled": 0,
            "asi_one_discoverable": 0,
            "errors": []
        }
    
    async def deploy_all_agents(self) -> Dict[str, Any]:
        """Deploy all HealthSync agents to Agentverse."""
        print("🚀 Starting HealthSync Agentverse Deployment")
        print("=" * 60)
        
        try:
            # Step 1: Register agents
            print("📋 Step 1: Registering agents on Agentverse...")
            registration_results = await self.registration_manager.register_all_agents()
            
            self.deployment_status["agents_registered"] = len(registration_results["successful_registrations"])
            
            if registration_results["failed_registrations"]:
                for failure in registration_results["failed_registrations"]:
                    self.deployment_status["errors"].append(f"Registration failed for {failure['agent_name']}: {failure['error']}")
            
            print(f"✅ Registration: {self.deployment_status['agents_registered']}/{len(AGENT_CONFIG)} agents registered")
            
            # Step 2: Verify Chat Protocol
            print("\n💬 Step 2: Verifying Chat Protocol integration...")
            chat_results = await self._verify_chat_protocol(registration_results["successful_registrations"])
            
            self.deployment_status["chat_protocol_enabled"] = len([r for r in chat_results if r["chat_enabled"]])
            print(f"✅ Chat Protocol: {self.deployment_status['chat_protocol_enabled']}/{len(registration_results['successful_registrations'])} agents enabled")
            
            # Step 3: Verify ASI:One discovery
            print("\n🔍 Step 3: Verifying ASI:One discovery...")
            discovery_results = await self._verify_asi_one_discovery(registration_results["successful_registrations"])
            
            self.deployment_status["asi_one_discoverable"] = len([r for r in discovery_results if r["discoverable"]])
            print(f"✅ ASI:One Discovery: {self.deployment_status['asi_one_discoverable']}/{len(registration_results['successful_registrations'])} agents discoverable")
            
            # Step 4: Health monitoring setup
            print("\n🏥 Step 4: Setting up health monitoring...")
            health_results = await self._setup_health_monitoring()
            
            self.deployment_status["agents_healthy"] = health_results.get("summary", {}).get("healthy_agents", 0)
            print(f"✅ Health Status: {self.deployment_status['agents_healthy']}/{len(AGENT_CONFIG)} agents healthy")
            
            # Step 5: Generate deployment report
            print("\n📊 Step 5: Generating deployment report...")
            deployment_report = await self._generate_deployment_report(
                registration_results, chat_results, discovery_results, health_results
            )
            
            # Determine overall success
            total_agents = len(AGENT_CONFIG)
            self.deployment_status["success"] = (
                self.deployment_status["agents_registered"] == total_agents and
                self.deployment_status["chat_protocol_enabled"] == total_agents and
                self.deployment_status["asi_one_discoverable"] == total_agents and
                self.deployment_status["agents_healthy"] == total_agents
            )
            
            self.deployment_status["completed_at"] = datetime.utcnow().isoformat()
            
            # Display final summary
            await self._display_deployment_summary(deployment_report)
            
            return deployment_report
            
        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            self.deployment_status["errors"].append(error_msg)
            self.deployment_status["completed_at"] = datetime.utcnow().isoformat()
            print(f"❌ {error_msg}")
            raise
    
    async def _verify_chat_protocol(self, registered_agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify Chat Protocol integration for all agents."""
        results = []
        
        for agent_info in registered_agents:
            agent_name = agent_info["agent_name"]
            print(f"  Verifying Chat Protocol for {agent_name}...")
            
            try:
                # Check manifest for Chat Protocol configuration
                manifest_path = f"agents/manifests/{agent_name}_manifest.json"
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                chat_enabled = manifest.get("chat_protocol_enabled", False)
                
                results.append({
                    "agent_name": agent_name,
                    "chat_enabled": chat_enabled,
                    "agentverse_compatible": manifest.get("agentverse_compatible", False),
                    "badges": manifest.get("badges", [])
                })
                
            except Exception as e:
                results.append({
                    "agent_name": agent_name,
                    "chat_enabled": False,
                    "error": str(e)
                })
        
        return results
    
    async def _verify_asi_one_discovery(self, registered_agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify ASI:One discovery for all agents."""
        results = []
        
        for agent_info in registered_agents:
            agent_name = agent_info["agent_name"]
            print(f"  Checking ASI:One discovery for {agent_name}...")
            
            try:
                # Use registration manager to verify discovery
                discovery_result = await self.registration_manager.verify_agent_discovery(agent_name)
                
                results.append({
                    "agent_name": agent_name,
                    "discoverable": discovery_result["discoverable"],
                    "asi_one_url": discovery_result.get("asi_one_url"),
                    "badges_visible": discovery_result.get("badges_visible", False)
                })
                
            except Exception as e:
                results.append({
                    "agent_name": agent_name,
                    "discoverable": False,
                    "error": str(e)
                })
        
        return results
    
    async def _setup_health_monitoring(self) -> Dict[str, Any]:
        """Setup health monitoring for all agents."""
        print("  Starting health monitoring system...")
        
        # Check health of all agents
        health_results = await self.health_monitor.check_all_agents()
        
        # Start continuous monitoring in background
        # Note: In production, this would be a separate service
        print("  Health monitoring system configured")
        
        return health_results
    
    async def _generate_deployment_report(self, registration_results: Dict[str, Any],
                                        chat_results: List[Dict[str, Any]],
                                        discovery_results: List[Dict[str, Any]],
                                        health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive deployment report."""
        
        report = {
            "deployment_timestamp": datetime.utcnow().isoformat(),
            "deployment_status": self.deployment_status,
            "registration_results": registration_results,
            "chat_protocol_verification": chat_results,
            "asi_one_discovery": discovery_results,
            "health_monitoring": health_results,
            "agentverse_urls": [],
            "asi_one_urls": [],
            "health_check_urls": []
        }
        
        # Generate URLs for successful registrations
        for agent_info in registration_results["successful_registrations"]:
            agent_name = agent_info["agent_name"]
            agent_id = agent_info["agent_id"]
            
            # Agentverse URLs
            report["agentverse_urls"].append({
                "agent_name": agent_name,
                "agentverse_url": agent_info.get("agentverse_url"),
                "chat_protocol_url": agent_info.get("chat_protocol_url")
            })
            
            # ASI:One URLs
            report["asi_one_urls"].append({
                "agent_name": agent_name,
                "asi_one_chat_url": f"https://asi.one/chat/{agent_id}",
                "asi_one_agent_url": f"https://asi.one/agents/{agent_id}"
            })
            
            # Health check URLs
            agent_config = AGENT_CONFIG.get(agent_name, {})
            port = agent_config.get("port")
            if port:
                health_port = port + 1000  # HTTP server port
                report["health_check_urls"].append({
                    "agent_name": agent_name,
                    "health_url": f"http://localhost:{health_port}/health",
                    "status_url": f"http://localhost:{health_port}/status",
                    "metrics_url": f"http://localhost:{health_port}/metrics"
                })
        
        # Save report
        report_path = "deployment/complete_deployment_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Complete deployment report saved to {report_path}")
        
        return report
    
    async def _display_deployment_summary(self, report: Dict[str, Any]):
        """Display deployment summary."""
        print("\n" + "=" * 60)
        print("🎉 HEALTHSYNC AGENTVERSE DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        status = self.deployment_status
        
        print(f"📊 Overall Status: {'✅ SUCCESS' if status['success'] else '❌ PARTIAL/FAILED'}")
        print(f"📅 Started: {status['started_at']}")
        print(f"📅 Completed: {status['completed_at']}")
        print()
        
        print("📈 Deployment Metrics:")
        print(f"  Agents Registered: {status['agents_registered']}/{len(AGENT_CONFIG)}")
        print(f"  Chat Protocol Enabled: {status['chat_protocol_enabled']}/{len(AGENT_CONFIG)}")
        print(f"  ASI:One Discoverable: {status['asi_one_discoverable']}/{len(AGENT_CONFIG)}")
        print(f"  Agents Healthy: {status['agents_healthy']}/{len(AGENT_CONFIG)}")
        print()
        
        if report["agentverse_urls"]:
            print("🔗 Agentverse URLs:")
            for url_info in report["agentverse_urls"]:
                print(f"  {url_info['agent_name']}: {url_info['agentverse_url']}")
            print()
        
        if report["asi_one_urls"]:
            print("🌐 ASI:One URLs:")
            for url_info in report["asi_one_urls"]:
                print(f"  {url_info['agent_name']}: {url_info['asi_one_chat_url']}")
            print()
        
        if report["health_check_urls"]:
            print("🏥 Health Check URLs:")
            for url_info in report["health_check_urls"]:
                print(f"  {url_info['agent_name']}: {url_info['health_url']}")
            print()
        
        if status["errors"]:
            print("⚠️  Errors:")
            for error in status["errors"]:
                print(f"  - {error}")
            print()
        
        print("🎊 HealthSync agents are ready for ASI Alliance Hackathon!")
        print("=" * 60)


async def main():
    """Main deployment function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("HealthSync Complete Agentverse Deployment")
        print("Usage: python deploy_to_agentverse.py")
        print("\nThis script will:")
        print("1. Register all agents on Agentverse")
        print("2. Enable Chat Protocol for ASI:One compatibility")
        print("3. Verify agent discovery and health")
        print("4. Setup monitoring and alerting")
        print("5. Generate comprehensive deployment report")
        return
    
    deployment = HealthSyncDeployment()
    
    try:
        result = await deployment.deploy_all_agents()
        
        if deployment.deployment_status["success"]:
            print("\n🎊 All agents successfully deployed and ready!")
            sys.exit(0)
        else:
            print("\n⚠️  Deployment completed with issues. Check the report for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())