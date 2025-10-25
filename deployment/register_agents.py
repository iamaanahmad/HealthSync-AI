#!/usr/bin/env python3
"""
HealthSync Agent Registration Script.
Registers all agents on Agentverse with proper manifests and Chat Protocol support.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from deployment.agentverse_registration import AgentverseRegistrationManager
from config import AGENT_CONFIG


async def register_agents_with_monitoring():
    """Register agents and set up monitoring."""
    print("🚀 HealthSync Agentverse Registration")
    print("=" * 50)
    
    # Initialize registration manager
    manager = AgentverseRegistrationManager()
    
    try:
        # Step 1: Register all agents
        print("📋 Step 1: Registering agents on Agentverse...")
        registration_results = await manager.register_all_agents()
        
        success_count = len(registration_results["successful_registrations"])
        total_count = registration_results["total_agents"]
        
        print(f"✅ Registration completed: {success_count}/{total_count} agents registered")
        
        # Step 2: Verify Chat Protocol integration
        print("\n💬 Step 2: Verifying Chat Protocol integration...")
        chat_verification_results = []
        
        for agent_info in registration_results["successful_registrations"]:
            agent_name = agent_info["agent_name"]
            print(f"  Verifying {agent_name}...")
            
            # Verify Chat Protocol is enabled
            chat_enabled = agent_info.get("chat_protocol_enabled", False)
            chat_verification_results.append({
                "agent_name": agent_name,
                "chat_protocol_enabled": chat_enabled,
                "asi_one_compatible": chat_enabled
            })
        
        # Step 3: Verify ASI:One discovery
        print("\n🔍 Step 3: Verifying ASI:One discovery...")
        discovery_results = []
        
        for agent_info in registration_results["successful_registrations"]:
            agent_name = agent_info["agent_name"]
            print(f"  Checking discovery for {agent_name}...")
            
            discovery_result = await manager.verify_agent_discovery(agent_name)
            discovery_results.append({
                "agent_name": agent_name,
                "discoverable": discovery_result["discoverable"],
                "asi_one_url": discovery_result.get("asi_one_url")
            })
        
        # Step 4: Set up health monitoring
        print("\n🏥 Step 4: Setting up health monitoring...")
        health_results = await manager.monitor_all_agents()
        
        healthy_count = len(health_results["healthy_agents"])
        total_agents = len(AGENT_CONFIG)
        
        print(f"  Health status: {healthy_count}/{total_agents} agents healthy")
        
        # Step 5: Generate comprehensive report
        print("\n📊 Step 5: Generating deployment report...")
        
        deployment_report = {
            "deployment_timestamp": datetime.utcnow().isoformat(),
            "registration_results": registration_results,
            "chat_protocol_verification": chat_verification_results,
            "discovery_verification": discovery_results,
            "health_monitoring": health_results,
            "summary": {
                "total_agents": total_count,
                "registered_agents": success_count,
                "chat_protocol_enabled": sum(1 for r in chat_verification_results if r["chat_protocol_enabled"]),
                "discoverable_agents": sum(1 for r in discovery_results if r["discoverable"]),
                "healthy_agents": healthy_count,
                "deployment_success": success_count == total_count and healthy_count == total_count
            },
            "agentverse_urls": [
                {
                    "agent_name": agent["agent_name"],
                    "agentverse_url": agent.get("agentverse_url"),
                    "chat_url": f"https://asi.one/chat/{agent['agent_id']}"
                }
                for agent in registration_results["successful_registrations"]
            ]
        }
        
        # Save deployment report
        report_path = "deployment/deployment_report.json"
        with open(report_path, 'w') as f:
            json.dump(deployment_report, f, indent=2)
        
        print(f"📄 Deployment report saved to {report_path}")
        
        # Display summary
        print("\n" + "=" * 50)
        print("🎉 DEPLOYMENT SUMMARY")
        print("=" * 50)
        
        summary = deployment_report["summary"]
        print(f"Total Agents: {summary['total_agents']}")
        print(f"Registered: {summary['registered_agents']}")
        print(f"Chat Protocol Enabled: {summary['chat_protocol_enabled']}")
        print(f"ASI:One Discoverable: {summary['discoverable_agents']}")
        print(f"Healthy: {summary['healthy_agents']}")
        print(f"Overall Success: {'✅ YES' if summary['deployment_success'] else '❌ NO'}")
        
        if registration_results["successful_registrations"]:
            print("\n🔗 Agent URLs:")
            for url_info in deployment_report["agentverse_urls"]:
                print(f"  {url_info['agent_name']}: {url_info['chat_url']}")
        
        if registration_results["failed_registrations"]:
            print("\n❌ Failed Registrations:")
            for failure in registration_results["failed_registrations"]:
                print(f"  {failure['agent_name']}: {failure['error']}")
        
        return deployment_report
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return None


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("HealthSync Agent Registration Script")
        print("Usage: python register_agents.py")
        print("\nThis script will:")
        print("1. Register all HealthSync agents on Agentverse")
        print("2. Enable Chat Protocol for ASI:One compatibility")
        print("3. Verify agent discovery and health")
        print("4. Generate deployment report")
        return
    
    # Run registration
    result = asyncio.run(register_agents_with_monitoring())
    
    if result and result["summary"]["deployment_success"]:
        print("\n🎊 All agents successfully deployed and ready for ASI Alliance Hackathon!")
        sys.exit(0)
    else:
        print("\n⚠️  Deployment completed with issues. Check the report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()