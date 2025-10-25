"""
HealthSync Demo Script

Step-by-step demo script showcasing all system capabilities
Optimized for 3-5 minute video demonstration
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from personas import DemoPersonas

class HealthSyncDemo:
    """Orchestrates the complete HealthSync demonstration"""
    
    def __init__(self):
        self.personas = DemoPersonas()
        self.demo_state = {
            "current_step": 0,
            "start_time": None,
            "step_timings": [],
            "demo_data": {}
        }
        self.demo_steps = self._define_demo_steps()
    
    def _define_demo_steps(self) -> List[Dict[str, Any]]:
        """Define the complete demo flow with timing"""
        return [
            {
                "step": 1,
                "title": "System Overview & Problem Statement",
                "duration": 30,  # seconds
                "description": "Introduce healthcare data silos problem and HealthSync solution",
                "actions": [
                    "Show healthcare data fragmentation statistics",
                    "Introduce ASI Alliance technology stack",
                    "Display agent architecture overview"
                ],
                "demo_points": [
                    "5 autonomous AI agents working together",
                    "Patient-controlled data sharing",
                    "Privacy-first research enablement"
                ]
            },
            {
                "step": 2,
                "title": "Patient Consent Management",
                "duration": 45,
                "description": "Demonstrate patient control over data sharing preferences",
                "actions": [
                    "Login as Sarah Chen (patient_001)",
                    "Show current consent dashboard",
                    "Update consent preferences for diabetes research",
                    "Demonstrate Chat Protocol integration with ASI:One"
                ],
                "demo_points": [
                    "Granular consent control by data type",
                    "Real-time consent updates via Chat Protocol",
                    "Consent history and audit trail",
                    "Natural language interaction through ASI:One"
                ]
            },
            {
                "step": 3,
                "title": "Research Query Submission",
                "duration": 40,
                "description": "Show researcher submitting ethical research query",
                "actions": [
                    "Login as Dr. Jennifer Park (researcher_001)",
                    "Submit diabetes prevention research query",
                    "Show ethical compliance validation",
                    "Display query processing status"
                ],
                "demo_points": [
                    "Structured research query builder",
                    "Automatic ethics compliance checking",
                    "MeTTa Knowledge Graph reasoning",
                    "Real-time query status updates"
                ]
            },
            {
                "step": 4,
                "title": "Multi-Agent Collaboration",
                "duration": 60,
                "description": "Showcase autonomous agent workflow execution",
                "actions": [
                    "Switch to Agent Activity Monitor",
                    "Watch agents collaborate in real-time",
                    "Show message flow between agents",
                    "Display MeTTa reasoning paths"
                ],
                "demo_points": [
                    "Research Query Agent validates ethics",
                    "Patient Consent Agent checks permissions", 
                    "Data Custodian Agent finds matching datasets",
                    "Privacy Agent anonymizes data",
                    "MeTTa Integration Agent provides reasoning"
                ]
            },
            {
                "step": 5,
                "title": "Privacy & Anonymization",
                "duration": 35,
                "description": "Demonstrate privacy-preserving data processing",
                "actions": [
                    "Show raw dataset before anonymization",
                    "Display Privacy Agent anonymization process",
                    "Show k-anonymity compliance (k>=5)",
                    "Verify no personally identifiable information"
                ],
                "demo_points": [
                    "K-anonymity with configurable thresholds",
                    "Cryptographic hashing of identifiers",
                    "Statistical noise injection",
                    "Privacy compliance audit trail"
                ]
            },
            {
                "step": 6,
                "title": "Research Results Delivery",
                "duration": 30,
                "description": "Show anonymized results delivered to researcher",
                "actions": [
                    "Return to researcher portal",
                    "Display anonymized research dataset",
                    "Show data quality metrics",
                    "Demonstrate result export functionality"
                ],
                "demo_points": [
                    "Fully anonymized patient data",
                    "Research-ready dataset format",
                    "Data provenance and quality metrics",
                    "Secure result export and sharing"
                ]
            },
            {
                "step": 7,
                "title": "MeTTa Knowledge Graph Exploration",
                "duration": 25,
                "description": "Showcase MeTTa reasoning and knowledge representation",
                "actions": [
                    "Open MeTTa Explorer interface",
                    "Browse medical ontologies and relationships",
                    "Execute complex reasoning queries",
                    "Show nested query results and reasoning paths"
                ],
                "demo_points": [
                    "Medical knowledge graph visualization",
                    "Complex reasoning with nested queries",
                    "Ethics rules and compliance frameworks",
                    "Transparent reasoning explanations"
                ]
            },
            {
                "step": 8,
                "title": "ASI Alliance Technology Integration",
                "duration": 15,
                "description": "Highlight all ASI Alliance technologies in action",
                "actions": [
                    "Show Agentverse agent discovery",
                    "Demonstrate Chat Protocol compliance",
                    "Display Innovation Lab badges",
                    "Verify ASI:One integration"
                ],
                "demo_points": [
                    "All agents registered on Agentverse",
                    "Chat Protocol enabled for natural interaction",
                    "MeTTa Knowledge Graph for reasoning",
                    "Full ASI Alliance technology stack"
                ]
            }
        ]
    
    async def run_complete_demo(self) -> Dict[str, Any]:
        """Execute the complete demo scenario"""
        print("🚀 Starting HealthSync Complete Demo")
        print("=" * 50)
        
        self.demo_state["start_time"] = datetime.now()
        demo_log = []
        
        for step_config in self.demo_steps:
            step_result = await self._execute_demo_step(step_config)
            demo_log.append(step_result)
            
            # Add pause between steps for video recording
            await asyncio.sleep(2)
        
        total_duration = sum(step["actual_duration"] for step in demo_log)
        
        demo_summary = {
            "demo_completed": True,
            "total_duration": total_duration,
            "target_duration": sum(step["duration"] for step in self.demo_steps),
            "steps_executed": len(demo_log),
            "step_details": demo_log,
            "demo_effectiveness": self._calculate_demo_effectiveness(demo_log)
        }
        
        print(f"\n✅ Demo completed in {total_duration} seconds")
        print(f"🎯 Target duration: {demo_summary['target_duration']} seconds")
        
        return demo_summary
    
    async def _execute_demo_step(self, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single demo step"""
        step_start = datetime.now()
        
        print(f"\n📍 Step {step_config['step']}: {step_config['title']}")
        print(f"⏱️  Target duration: {step_config['duration']}s")
        print(f"📝 {step_config['description']}")
        
        # Simulate step execution
        for action in step_config['actions']:
            print(f"   ▶️ {action}")
            await asyncio.sleep(1)  # Simulate action execution time
        
        # Highlight key demo points
        print("   🎯 Key Demo Points:")
        for point in step_config['demo_points']:
            print(f"      • {point}")
        
        step_end = datetime.now()
        actual_duration = (step_end - step_start).total_seconds()
        
        return {
            "step": step_config['step'],
            "title": step_config['title'],
            "target_duration": step_config['duration'],
            "actual_duration": actual_duration,
            "actions_completed": len(step_config['actions']),
            "demo_points_covered": len(step_config['demo_points']),
            "timing_accuracy": abs(actual_duration - step_config['duration']) / step_config['duration']
        }
    
    def _calculate_demo_effectiveness(self, demo_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate demo effectiveness metrics"""
        total_points = sum(step["demo_points_covered"] for step in demo_log)
        avg_timing_accuracy = sum(step["timing_accuracy"] for step in demo_log) / len(demo_log)
        
        return {
            "total_demo_points_covered": total_points,
            "average_timing_accuracy": avg_timing_accuracy,
            "timing_grade": "excellent" if avg_timing_accuracy < 0.1 else "good" if avg_timing_accuracy < 0.2 else "needs_improvement",
            "demo_completeness": len(demo_log) / len(self.demo_steps),
            "recommended_improvements": self._get_demo_improvements(avg_timing_accuracy)
        }
    
    def _get_demo_improvements(self, timing_accuracy: float) -> List[str]:
        """Get recommendations for demo improvement"""
        improvements = []
        
        if timing_accuracy > 0.2:
            improvements.append("Practice step transitions to improve timing")
            improvements.append("Prepare demo data in advance to reduce loading time")
        
        if timing_accuracy > 0.3:
            improvements.append("Consider reducing content in longer steps")
            improvements.append("Add more rehearsal time for complex demonstrations")
        
        improvements.extend([
            "Ensure all agents are running before demo start",
            "Have backup scenarios ready for technical issues",
            "Practice natural narration for each step",
            "Verify screen recording setup and audio quality"
        ])
        
        return improvements
    
    def generate_demo_script_document(self) -> str:
        """Generate formatted demo script for video recording"""
        script = "# HealthSync Demo Script\n\n"
        script += "## Overview\n"
        script += "This demo showcases HealthSync's decentralized healthcare data exchange system built on ASI Alliance technologies.\n\n"
        script += f"**Target Duration:** {sum(step['duration'] for step in self.demo_steps)} seconds ({sum(step['duration'] for step in self.demo_steps) / 60:.1f} minutes)\n\n"
        
        script += "## Demo Flow\n\n"
        
        for step_config in self.demo_steps:
            script += f"### Step {step_config['step']}: {step_config['title']}\n"
            script += f"**Duration:** {step_config['duration']} seconds\n\n"
            script += f"{step_config['description']}\n\n"
            
            script += "**Actions:**\n"
            for action in step_config['actions']:
                script += f"- {action}\n"
            script += "\n"
            
            script += "**Key Points to Highlight:**\n"
            for point in step_config['demo_points']:
                script += f"- {point}\n"
            script += "\n"
        
        script += "## Pre-Demo Checklist\n\n"
        script += "- [ ] All agents running and registered on Agentverse\n"
        script += "- [ ] Frontend applications loaded and responsive\n"
        script += "- [ ] Demo personas and data loaded\n"
        script += "- [ ] Screen recording software configured\n"
        script += "- [ ] Audio equipment tested\n"
        script += "- [ ] Backup demo scenarios prepared\n"
        script += "- [ ] Network connectivity verified\n\n"
        
        script += "## Post-Demo Actions\n\n"
        script += "- [ ] Reset demo data for next demonstration\n"
        script += "- [ ] Save demo recording and logs\n"
        script += "- [ ] Review timing and effectiveness metrics\n"
        script += "- [ ] Update script based on lessons learned\n"
        
        return script

# Demo data generation and management
class DemoDataManager:
    """Manages demo data lifecycle and reset functionality"""
    
    def __init__(self):
        self.personas = DemoPersonas()
        self.demo_state_file = "demo_state.json"
    
    def setup_demo_data(self):
        """Initialize all demo data"""
        print("🔧 Setting up demo data...")
        
        # Generate personas
        self.personas.export_personas_json("personas_data.json")
        
        # Create initial demo state
        demo_state = {
            "setup_time": datetime.now().isoformat(),
            "demo_runs": 0,
            "last_reset": datetime.now().isoformat(),
            "current_patients": [p["patient_id"] for p in self.personas.patients],
            "current_researchers": [r["researcher_id"] for r in self.personas.researchers]
        }
        
        with open(self.demo_state_file, 'w') as f:
            json.dump(demo_state, f, indent=2)
        
        print("✅ Demo data setup complete")
    
    def reset_demo_data(self):
        """Reset demo data for repeatable demonstrations"""
        print("🔄 Resetting demo data...")
        
        # Reset consent preferences to initial state
        for patient in self.personas.patients:
            if patient["patient_id"] == "patient_001":  # Sarah Chen
                patient["consent_preferences"]["imaging_data"] = False  # She revoked this
            # Reset other patients to initial state as needed
        
        # Update demo state
        with open(self.demo_state_file, 'r') as f:
            demo_state = json.load(f)
        
        demo_state["demo_runs"] += 1
        demo_state["last_reset"] = datetime.now().isoformat()
        
        with open(self.demo_state_file, 'w') as f:
            json.dump(demo_state, f, indent=2)
        
        # Re-export personas with reset data
        self.personas.export_personas_json("personas_data.json")
        
        print("✅ Demo data reset complete")
    
    def cleanup_demo_data(self):
        """Clean up demo data after demonstration"""
        print("🧹 Cleaning up demo data...")
        
        # Clear any temporary files
        import os
        temp_files = [
            "temp_query_results.json",
            "temp_agent_logs.json",
            "temp_anonymized_data.json"
        ]
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        print("✅ Demo cleanup complete")

if __name__ == "__main__":
    # Run demo setup and execution
    async def main():
        from demo_timing_optimizer import DemoTimingOptimizer
        from demo_reset_manager import DemoResetManager
        
        print("🚀 HealthSync Demo System Initialization")
        print("=" * 50)
        
        # Initialize components
        data_manager = DemoDataManager()
        demo = HealthSyncDemo()
        optimizer = DemoTimingOptimizer()
        reset_manager = DemoResetManager()
        
        # Setup demo data
        print("\n1. Setting up demo data...")
        data_manager.setup_demo_data()
        
        # Optimize demo timing
        print("\n2. Optimizing demo timing...")
        optimization_result = optimizer.optimize_demo_flow(demo.demo_steps)
        
        # Generate optimized demo script
        print("\n3. Generating optimized demo script...")
        script_content = optimizer.create_demo_script_with_timing(demo.demo_steps)
        with open("OPTIMIZED_DEMO_SCRIPT.md", 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Generate timing cue cards
        print("\n4. Creating timing cue cards...")
        cue_cards = optimizer.generate_timing_cue_cards(demo.demo_steps)
        with open("timing_cue_cards.json", 'w', encoding='utf-8') as f:
            json.dump(cue_cards, f, indent=2)
        
        # Generate rehearsal schedule
        print("\n5. Creating rehearsal schedule...")
        rehearsal_schedule = optimizer.create_rehearsal_schedule(demo.demo_steps)
        with open("rehearsal_schedule.json", 'w', encoding='utf-8') as f:
            json.dump(rehearsal_schedule, f, indent=2)
        
        # Create reset checklist
        print("\n6. Generating reset checklist...")
        reset_checklist = reset_manager.create_reset_checklist()
        with open("RESET_CHECKLIST.md", 'w', encoding='utf-8') as f:
            f.write(reset_checklist)
        
        # Run complete demo simulation
        print("\n7. Running demo simulation...")
        demo_results = await demo.run_complete_demo()
        
        # Save demo results
        with open("demo_results.json", 'w', encoding='utf-8') as f:
            json.dump(demo_results, f, indent=2, default=str)
        
        # Generate final summary
        print("\n" + "=" * 50)
        print("✅ HealthSync Demo System Ready!")
        print("=" * 50)
        print(f"📊 Demo Duration: {demo_results['total_duration']}s (Target: {demo_results['target_duration']}s)")
        print(f"📋 Steps Covered: {demo_results['steps_executed']}")
        print(f"🎯 Timing Grade: {demo_results['demo_effectiveness']['timing_grade']}")
        print(f"📁 Files Generated:")
        print("   - OPTIMIZED_DEMO_SCRIPT.md")
        print("   - timing_cue_cards.json") 
        print("   - rehearsal_schedule.json")
        print("   - RESET_CHECKLIST.md")
        print("   - demo_results.json")
        print("   - personas_data.json")
        print("\n🎬 Ready for video recording!")
        
        return {
            "demo_ready": True,
            "optimization_result": optimization_result,
            "demo_results": demo_results,
            "files_generated": [
                "OPTIMIZED_DEMO_SCRIPT.md",
                "timing_cue_cards.json",
                "rehearsal_schedule.json", 
                "RESET_CHECKLIST.md",
                "demo_results.json",
                "personas_data.json"
            ]
        }
    
    asyncio.run(main())