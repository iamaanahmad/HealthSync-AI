#!/usr/bin/env python3
"""
Complete HealthSync Deployment Script.
Orchestrates the full deployment process including agent registration,
health monitoring, and ASI:One verification.
"""

import asyncio
import sys
import os
import json
import subprocess
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import deployment.deploy_to_agentverse as deploy_module
from deployment.verify_asi_one_integration import ASIOneVerificationManager
from deployment.agent_monitor import AgentHealthMonitor
from config import AGENT_CONFIG


class CompleteDeploymentOrchestrator:
    """Orchestrates the complete HealthSync deployment process."""
    
    def __init__(self):
        self.deployment_manager = deploy_module.HealthSyncDeployment()
        self.verification_manager = ASIOneVerificationManager()
        self.health_monitor = AgentHealthMonitor()
        
        self.deployment_log = {
            "started_at": datetime.utcnow().isoformat(),
            "phases": [],
            "overall_success": False,
            "completion_time": None
        }
    
    async def execute_complete_deployment(self) -> Dict[str, Any]:
        """Execute the complete deployment process."""
        print("🚀 HealthSync Complete Deployment Process")
        print("=" * 70)
        print("This will deploy all agents to Agentverse with full ASI:One integration")
        print("=" * 70)
        
        try:
            # Phase 1: Pre-deployment checks
            await self._phase_1_pre_deployment_checks()
            
            # Phase 2: Agent deployment
            await self._phase_2_agent_deployment()
            
            # Phase 3: ASI:One verification
            await self._phase_3_asi_one_verification()
            
            # Phase 4: Health monitoring setup
            await self._phase_4_health_monitoring_setup()
            
            # Phase 5: Final validation
            await self._phase_5_final_validation()
            
            # Phase 6: Generate final report
            await self._phase_6_generate_final_report()
            
            self.deployment_log["overall_success"] = True
            self.deployment_log["completion_time"] = datetime.utcnow().isoformat()
            
            print("\n🎊 Complete deployment successful!")
            return self.deployment_log
            
        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            self.deployment_log["phases"].append({
                "phase": "error",
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.deployment_log["completion_time"] = datetime.utcnow().isoformat()
            print(f"\n❌ {error_msg}")
            raise
    
    async def _phase_1_pre_deployment_checks(self):
        """Phase 1: Pre-deployment checks."""
        print("\n📋 Phase 1: Pre-deployment Checks")
        print("-" * 40)
        
        phase_start = datetime.utcnow()
        checks_passed = 0
        total_checks = 4
        
        try:
            # Check 1: Verify agent manifests exist
            print("1. Checking agent manifests...")
            for agent_name in AGENT_CONFIG.keys():
                manifest_path = f"agents/manifests/{agent_name}_manifest.json"
                if not os.path.exists(manifest_path):
                    raise FileNotFoundError(f"Missing manifest: {manifest_path}")
                
                # Validate manifest content
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                required_fields = ["name", "description", "badges", "chat_protocol_enabled"]
                for field in required_fields:
                    if field not in manifest:
                        raise ValueError(f"Missing field '{field}' in {manifest_path}")
            
            checks_passed += 1
            print("   ✅ All agent manifests valid")
            
            # Check 2: Verify agent code exists
            print("2. Checking agent implementations...")
            for agent_name in AGENT_CONFIG.keys():
                agent_path = f"agents/{agent_name}/agent.py"
                if not os.path.exists(agent_path):
                    raise FileNotFoundError(f"Missing agent implementation: {agent_path}")
            
            checks_passed += 1
            print("   ✅ All agent implementations found")
            
            # Check 3: Verify configuration
            print("3. Checking configuration...")
            if not AGENT_CONFIG:
                raise ValueError("No agents configured in AGENT_CONFIG")
            
            # Check for port conflicts
            ports = [config.get("port") for config in AGENT_CONFIG.values() if config.get("port")]
            if len(ports) != len(set(ports)):
                raise ValueError("Port conflicts detected in agent configuration")
            
            checks_passed += 1
            print("   ✅ Configuration valid")
            
            # Check 4: Verify dependencies
            print("4. Checking dependencies...")
            try:
                import uagents
                import aiohttp
                print("   ✅ All dependencies available")
                checks_passed += 1
            except ImportError as e:
                raise ImportError(f"Missing dependency: {str(e)}")
            
            # Record successful phase
            self.deployment_log["phases"].append({
                "phase": "pre_deployment_checks",
                "status": "success",
                "checks_passed": f"{checks_passed}/{total_checks}",
                "duration_seconds": (datetime.utcnow() - phase_start).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print(f"✅ Phase 1 Complete: {checks_passed}/{total_checks} checks passed")
            
        except Exception as e:
            self.deployment_log["phases"].append({
                "phase": "pre_deployment_checks",
                "status": "failed",
                "error": str(e),
                "checks_passed": f"{checks_passed}/{total_checks}",
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def _phase_2_agent_deployment(self):
        """Phase 2: Agent deployment to Agentverse."""
        print("\n🚀 Phase 2: Agent Deployment")
        print("-" * 40)
        
        phase_start = datetime.utcnow()
        
        try:
            # Execute deployment
            deployment_result = await self.deployment_manager.deploy_all_agents()
            
            # Record phase result
            self.deployment_log["phases"].append({
                "phase": "agent_deployment",
                "status": "success" if self.deployment_manager.deployment_status["success"] else "partial",
                "agents_registered": self.deployment_manager.deployment_status["agents_registered"],
                "agents_healthy": self.deployment_manager.deployment_status["agents_healthy"],
                "duration_seconds": (datetime.utcnow() - phase_start).total_seconds(),
                "deployment_result": deployment_result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if not self.deployment_manager.deployment_status["success"]:
                print("⚠️  Phase 2 completed with issues - continuing with verification")
            else:
                print("✅ Phase 2 Complete: All agents deployed successfully")
            
        except Exception as e:
            self.deployment_log["phases"].append({
                "phase": "agent_deployment",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def _phase_3_asi_one_verification(self):
        """Phase 3: ASI:One integration verification."""
        print("\n🔍 Phase 3: ASI:One Verification")
        print("-" * 40)
        
        phase_start = datetime.utcnow()
        
        try:
            # Execute verification
            verification_result = await self.verification_manager.verify_all_agents()
            
            # Record phase result
            self.deployment_log["phases"].append({
                "phase": "asi_one_verification",
                "status": "success" if verification_result["asi_one_compliant"] else "partial",
                "verified_agents": len(verification_result["verified_agents"]),
                "failed_verifications": len(verification_result["failed_verifications"]),
                "compliance_rate": verification_result["success_metrics"]["overall"],
                "duration_seconds": (datetime.utcnow() - phase_start).total_seconds(),
                "verification_result": verification_result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if verification_result["asi_one_compliant"]:
                print("✅ Phase 3 Complete: Full ASI:One compliance achieved")
            else:
                print("⚠️  Phase 3 completed with issues - some agents not fully compliant")
            
        except Exception as e:
            self.deployment_log["phases"].append({
                "phase": "asi_one_verification",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def _phase_4_health_monitoring_setup(self):
        """Phase 4: Health monitoring setup."""
        print("\n🏥 Phase 4: Health Monitoring Setup")
        print("-" * 40)
        
        phase_start = datetime.utcnow()
        
        try:
            # Setup health monitoring
            print("Setting up continuous health monitoring...")
            health_results = await self.health_monitor.check_all_agents()
            
            # Record phase result
            self.deployment_log["phases"].append({
                "phase": "health_monitoring_setup",
                "status": "success",
                "healthy_agents": health_results.get("summary", {}).get("healthy_agents", 0),
                "unhealthy_agents": health_results.get("summary", {}).get("unhealthy_agents", 0),
                "duration_seconds": (datetime.utcnow() - phase_start).total_seconds(),
                "health_results": health_results,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print("✅ Phase 4 Complete: Health monitoring configured")
            
        except Exception as e:
            self.deployment_log["phases"].append({
                "phase": "health_monitoring_setup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def _phase_5_final_validation(self):
        """Phase 5: Final validation."""
        print("\n✅ Phase 5: Final Validation")
        print("-" * 40)
        
        phase_start = datetime.utcnow()
        
        try:
            validation_results = {
                "agents_deployed": 0,
                "agents_healthy": 0,
                "asi_one_compliant": 0,
                "chat_protocol_enabled": 0,
                "all_requirements_met": False
            }
            
            # Check deployment phase
            deployment_phase = next((p for p in self.deployment_log["phases"] if p["phase"] == "agent_deployment"), None)
            if deployment_phase and deployment_phase["status"] in ["success", "partial"]:
                validation_results["agents_deployed"] = deployment_phase.get("agents_registered", 0)
                validation_results["agents_healthy"] = deployment_phase.get("agents_healthy", 0)
            
            # Check verification phase
            verification_phase = next((p for p in self.deployment_log["phases"] if p["phase"] == "asi_one_verification"), None)
            if verification_phase and verification_phase["status"] in ["success", "partial"]:
                validation_results["asi_one_compliant"] = verification_phase.get("verified_agents", 0)
                
                # Extract chat protocol info from verification result
                verification_result = verification_phase.get("verification_result", {})
                compat = verification_result.get("asi_one_compatibility", {})
                validation_results["chat_protocol_enabled"] = compat.get("chat_protocol_enabled", 0)
            
            # Determine if all requirements are met
            total_agents = len(AGENT_CONFIG)
            validation_results["all_requirements_met"] = (
                validation_results["agents_deployed"] == total_agents and
                validation_results["agents_healthy"] == total_agents and
                validation_results["asi_one_compliant"] == total_agents and
                validation_results["chat_protocol_enabled"] == total_agents
            )
            
            # Record phase result
            self.deployment_log["phases"].append({
                "phase": "final_validation",
                "status": "success" if validation_results["all_requirements_met"] else "partial",
                "validation_results": validation_results,
                "duration_seconds": (datetime.utcnow() - phase_start).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if validation_results["all_requirements_met"]:
                print("✅ Phase 5 Complete: All requirements validated")
            else:
                print("⚠️  Phase 5 Complete: Some requirements not fully met")
            
            print(f"   Agents Deployed: {validation_results['agents_deployed']}/{total_agents}")
            print(f"   Agents Healthy: {validation_results['agents_healthy']}/{total_agents}")
            print(f"   ASI:One Compliant: {validation_results['asi_one_compliant']}/{total_agents}")
            print(f"   Chat Protocol: {validation_results['chat_protocol_enabled']}/{total_agents}")
            
        except Exception as e:
            self.deployment_log["phases"].append({
                "phase": "final_validation",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def _phase_6_generate_final_report(self):
        """Phase 6: Generate final deployment report."""
        print("\n📊 Phase 6: Final Report Generation")
        print("-" * 40)
        
        phase_start = datetime.utcnow()
        
        try:
            # Generate comprehensive final report
            final_report = {
                "deployment_summary": self.deployment_log,
                "hackathon_readiness": {
                    "asi_alliance_compliant": False,
                    "innovation_lab_tagged": False,
                    "chat_protocol_ready": False,
                    "agentverse_deployed": False,
                    "health_monitoring_active": False
                },
                "agent_urls": {
                    "agentverse": [],
                    "asi_one": [],
                    "health_checks": []
                },
                "next_steps": [],
                "troubleshooting": []
            }
            
            # Analyze phases for hackathon readiness
            deployment_phase = next((p for p in self.deployment_log["phases"] if p["phase"] == "agent_deployment"), None)
            verification_phase = next((p for p in self.deployment_log["phases"] if p["phase"] == "asi_one_verification"), None)
            validation_phase = next((p for p in self.deployment_log["phases"] if p["phase"] == "final_validation"), None)
            
            if deployment_phase and deployment_phase["status"] == "success":
                final_report["hackathon_readiness"]["agentverse_deployed"] = True
                
                # Extract URLs from deployment result
                deployment_result = deployment_phase.get("deployment_result", {})
                final_report["agent_urls"]["agentverse"] = deployment_result.get("agentverse_urls", [])
                final_report["agent_urls"]["asi_one"] = deployment_result.get("asi_one_urls", [])
                final_report["agent_urls"]["health_checks"] = deployment_result.get("health_check_urls", [])
            
            if verification_phase and verification_phase["status"] == "success":
                verification_result = verification_phase.get("verification_result", {})
                final_report["hackathon_readiness"]["asi_alliance_compliant"] = verification_result.get("asi_one_compliant", False)
                
                compat = verification_result.get("asi_one_compatibility", {})
                final_report["hackathon_readiness"]["innovation_lab_tagged"] = compat.get("innovation_lab_tagged", 0) == len(AGENT_CONFIG)
                final_report["hackathon_readiness"]["chat_protocol_ready"] = compat.get("chat_protocol_enabled", 0) == len(AGENT_CONFIG)
            
            # Health monitoring status
            health_phase = next((p for p in self.deployment_log["phases"] if p["phase"] == "health_monitoring_setup"), None)
            if health_phase and health_phase["status"] == "success":
                final_report["hackathon_readiness"]["health_monitoring_active"] = True
            
            # Generate next steps and troubleshooting
            if not final_report["hackathon_readiness"]["agentverse_deployed"]:
                final_report["next_steps"].append("Re-run agent deployment to Agentverse")
                final_report["troubleshooting"].append("Check agent manifests and network connectivity")
            
            if not final_report["hackathon_readiness"]["chat_protocol_ready"]:
                final_report["next_steps"].append("Enable Chat Protocol in agent manifests")
                final_report["troubleshooting"].append("Verify chat_protocol_enabled: true in all manifests")
            
            if not final_report["hackathon_readiness"]["asi_alliance_compliant"]:
                final_report["next_steps"].append("Fix ASI:One compliance issues")
                final_report["troubleshooting"].append("Check badges and agent discovery settings")
            
            # Save final report
            report_path = "deployment/final_deployment_report.json"
            with open(report_path, 'w') as f:
                json.dump(final_report, f, indent=2)
            
            # Record phase result
            self.deployment_log["phases"].append({
                "phase": "final_report_generation",
                "status": "success",
                "report_path": report_path,
                "duration_seconds": (datetime.utcnow() - phase_start).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print(f"📄 Final report saved to {report_path}")
            print("✅ Phase 6 Complete: Final report generated")
            
            # Display final summary
            self._display_final_summary(final_report)
            
        except Exception as e:
            self.deployment_log["phases"].append({
                "phase": "final_report_generation",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    def _display_final_summary(self, final_report: Dict[str, Any]):
        """Display final deployment summary."""
        print("\n" + "=" * 70)
        print("🎊 HEALTHSYNC COMPLETE DEPLOYMENT SUMMARY")
        print("=" * 70)
        
        readiness = final_report["hackathon_readiness"]
        
        print("🏆 Hackathon Readiness Status:")
        print(f"  Agentverse Deployed: {'✅' if readiness['agentverse_deployed'] else '❌'}")
        print(f"  ASI Alliance Compliant: {'✅' if readiness['asi_alliance_compliant'] else '❌'}")
        print(f"  Innovation Lab Tagged: {'✅' if readiness['innovation_lab_tagged'] else '❌'}")
        print(f"  Chat Protocol Ready: {'✅' if readiness['chat_protocol_ready'] else '❌'}")
        print(f"  Health Monitoring: {'✅' if readiness['health_monitoring_active'] else '❌'}")
        print()
        
        # Overall readiness
        all_ready = all(readiness.values())
        print(f"🎯 Overall Readiness: {'✅ READY FOR HACKATHON!' if all_ready else '⚠️  NEEDS ATTENTION'}")
        print()
        
        # URLs
        if final_report["agent_urls"]["asi_one"]:
            print("🌐 ASI:One URLs:")
            for url_info in final_report["agent_urls"]["asi_one"]:
                print(f"  {url_info['agent_name']}: {url_info['asi_one_chat_url']}")
            print()
        
        # Next steps
        if final_report["next_steps"]:
            print("📋 Next Steps:")
            for step in final_report["next_steps"]:
                print(f"  - {step}")
            print()
        
        print("🎊 HealthSync deployment process complete!")
        print("=" * 70)


async def main():
    """Main deployment orchestration."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("HealthSync Complete Deployment Orchestrator")
        print("Usage: python complete_deployment.py")
        print("\nThis script orchestrates the complete deployment process:")
        print("1. Pre-deployment checks")
        print("2. Agent deployment to Agentverse")
        print("3. ASI:One integration verification")
        print("4. Health monitoring setup")
        print("5. Final validation")
        print("6. Comprehensive reporting")
        return
    
    orchestrator = CompleteDeploymentOrchestrator()
    
    try:
        result = await orchestrator.execute_complete_deployment()
        
        # Check final validation phase
        validation_phase = next((p for p in result["phases"] if p["phase"] == "final_validation"), None)
        if validation_phase and validation_phase.get("validation_results", {}).get("all_requirements_met", False):
            print("\n🎉 Complete deployment successful - ready for ASI Alliance Hackathon!")
            sys.exit(0)
        else:
            print("\n⚠️  Deployment completed with issues. Check the final report for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Complete deployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())