#!/usr/bin/env python3
"""
Demo Video Script Generator for HealthSync
Creates a comprehensive, timed demo script optimized for ASI Alliance Hackathon
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class DemoVideoScriptGenerator:
    """Generates optimized demo video script with precise timing."""
    
    def __init__(self):
        self.target_duration = 240  # 4 minutes
        self.optimized_duration = 280  # 4:40 minutes with buffer
        
        self.demo_steps = [
            {
                "step": 1,
                "title": "System Overview & Problem Statement",
                "duration": 30,
                "start_time": 0,
                "narration": "Introduce healthcare data silos problem and HealthSync solution",
                "actions": [
                    {"time": 0, "action": "Show healthcare data fragmentation statistics"},
                    {"time": 10, "action": "Introduce ASI Alliance technology stack"},
                    {"time": 20, "action": "Display agent architecture overview"}
                ],
                "key_points": [
                    "5 autonomous AI agents working together",
                    "Patient-controlled data sharing",
                    "Privacy-first research enablement"
                ]
            },
            {
                "step": 2,
                "title": "Patient Consent Management",
                "duration": 45,
                "start_time": 30,
                "narration": "Demonstrate patient control over data sharing preferences",
                "actions": [
                    {"time": 0, "action": "Login as Sarah Chen (patient_001)"},
                    {"time": 11, "action": "Show current consent dashboard"},
                    {"time": 22, "action": "Update consent preferences for diabetes research"},
                    {"time": 34, "action": "Demonstrate Chat Protocol integration with ASI:One"}
                ],
                "key_points": [
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
                "start_time": 75,
                "narration": "Show researcher submitting ethical research query",
                "actions": [
                    {"time": 0, "action": "Login as Dr. Jennifer Park (researcher_001)"},
                    {"time": 10, "action": "Submit diabetes prevention research query"},
                    {"time": 20, "action": "Show ethical compliance validation"},
                    {"time": 30, "action": "Display query processing status"}
                ],
                "key_points": [
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
                "start_time": 115,
                "narration": "Showcase autonomous agent workflow execution",
                "actions": [
                    {"time": 0, "action": "Switch to Agent Activity Monitor"},
                    {"time": 15, "action": "Watch agents collaborate in real-time"},
                    {"time": 30, "action": "Show message flow between agents"},
                    {"time": 45, "action": "Display MeTTa reasoning paths"}
                ],
                "key_points": [
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
                "start_time": 175,
                "narration": "Demonstrate privacy-preserving data processing",
                "actions": [
                    {"time": 0, "action": "Show raw dataset before anonymization"},
                    {"time": 9, "action": "Display Privacy Agent anonymization process"},
                    {"time": 18, "action": "Show k-anonymity compliance (k>=5)"},
                    {"time": 26, "action": "Verify no personally identifiable information"}
                ],
                "key_points": [
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
                "start_time": 210,
                "narration": "Show anonymized results delivered to researcher",
                "actions": [
                    {"time": 0, "action": "Return to researcher portal"},
                    {"time": 8, "action": "Display anonymized research dataset"},
                    {"time": 15, "action": "Show data quality metrics"},
                    {"time": 22, "action": "Demonstrate result export functionality"}
                ],
                "key_points": [
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
                "start_time": 240,
                "narration": "Showcase MeTTa reasoning and knowledge representation",
                "actions": [
                    {"time": 0, "action": "Open MeTTa Explorer interface"},
                    {"time": 6, "action": "Browse medical ontologies and relationships"},
                    {"time": 12, "action": "Execute complex reasoning queries"},
                    {"time": 19, "action": "Show nested query results and reasoning paths"}
                ],
                "key_points": [
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
                "start_time": 265,
                "narration": "Highlight all ASI Alliance technologies in action",
                "actions": [
                    {"time": 0, "action": "Show Agentverse agent discovery"},
                    {"time": 4, "action": "Demonstrate Chat Protocol compliance"},
                    {"time": 8, "action": "Display Innovation Lab badges"},
                    {"time": 11, "action": "Verify ASI:One integration"}
                ],
                "key_points": [
                    "All agents registered on Agentverse",
                    "Chat Protocol enabled for natural interaction",
                    "MeTTa Knowledge Graph for reasoning",
                    "Full ASI Alliance technology stack"
                ]
            }
        ]
    
    def generate_demo_script(self) -> str:
        """Generate the complete demo script in Markdown format."""
        
        script_content = f"""# HealthSync Demo Script - Optimized for Video Recording

**Target Duration:** {self.target_duration} seconds ({self.target_duration//60}:{self.target_duration%60:02d} minutes)
**Optimized Duration:** {self.optimized_duration} seconds ({self.optimized_duration//60}:{self.optimized_duration%60:02d} minutes)

## Pre-Recording Checklist

- [ ] All agents running and responsive
- [ ] Frontend loaded with demo data
- [ ] Screen recording software configured (1080p, 30fps)
- [ ] Audio levels tested and optimized
- [ ] Browser zoom set to 100%
- [ ] Notifications disabled
- [ ] Demo personas logged in and ready

## Detailed Demo Script with Timing

"""
        
        for step in self.demo_steps:
            start_min = step["start_time"] // 60
            start_sec = step["start_time"] % 60
            end_time = step["start_time"] + step["duration"]
            end_min = end_time // 60
            end_sec = end_time % 60
            
            script_content += f"""### Step {step["step"]}: {step["title"]}
**Time:** {start_min}:{start_sec:02d} - {end_min}:{end_sec:02d} ({step["duration"]}s duration)

**Narration:** {step["narration"]}

**Actions with Timing:**
"""
            
            for action in step["actions"]:
                action_min = action["time"] // 60
                action_sec = action["time"] % 60
                script_content += f"- [{action_min:02d}:{action_sec:02d}] {action['action']}\n"
            
            script_content += f"""
**Key Points to Emphasize:**
"""
            for point in step["key_points"]:
                script_content += f"- {point}\n"
            
            script_content += f"""
**Transition:** Pause 1.0s before next step

"""
        
        script_content += """## Post-Recording Checklist

- [ ] Verify recording quality and audio sync
- [ ] Check all key points were covered
- [ ] Confirm demo duration within target range
- [ ] Save raw recording with timestamp
- [ ] Reset demo environment for next recording

"""
        
        return script_content
    
    def generate_timing_cue_cards(self) -> Dict[str, Any]:
        """Generate timing cue cards for the presenter."""
        
        cue_cards = {
            "demo_info": {
                "target_duration": f"{self.target_duration} seconds",
                "optimized_duration": f"{self.optimized_duration} seconds",
                "total_steps": len(self.demo_steps)
            },
            "timing_alerts": [],
            "step_summaries": []
        }
        
        # Generate timing alerts at key intervals
        alert_intervals = [60, 120, 180, 240, 270]  # 1min, 2min, 3min, 4min, 4:30min
        
        for interval in alert_intervals:
            current_step = None
            for step in self.demo_steps:
                if step["start_time"] <= interval < step["start_time"] + step["duration"]:
                    current_step = step
                    break
            
            if current_step:
                time_in_step = interval - current_step["start_time"]
                cue_cards["timing_alerts"].append({
                    "time": f"{interval//60}:{interval%60:02d}",
                    "message": f"Should be in Step {current_step['step']}: {current_step['title']}",
                    "time_in_step": f"{time_in_step}s into step",
                    "remaining_in_step": f"{current_step['duration'] - time_in_step}s remaining"
                })
        
        # Generate step summaries
        for step in self.demo_steps:
            start_time = f"{step['start_time']//60}:{step['start_time']%60:02d}"
            end_time = f"{(step['start_time'] + step['duration'])//60}:{(step['start_time'] + step['duration'])%60:02d}"
            
            cue_cards["step_summaries"].append({
                "step": step["step"],
                "title": step["title"],
                "time_range": f"{start_time} - {end_time}",
                "duration": f"{step['duration']}s",
                "key_actions": [action["action"] for action in step["actions"]],
                "main_points": step["key_points"][:2]  # Top 2 points
            })
        
        return cue_cards
    
    def generate_rehearsal_schedule(self) -> Dict[str, Any]:
        """Generate rehearsal schedule for demo preparation."""
        
        rehearsal_schedule = {
            "total_rehearsal_time": "2 hours",
            "sessions": [
                {
                    "session": 1,
                    "duration": "30 minutes",
                    "focus": "Complete run-through with timing",
                    "goals": [
                        "Practice entire demo from start to finish",
                        "Check timing accuracy for each step",
                        "Identify problem areas or transitions",
                        "Ensure all technical components work"
                    ]
                },
                {
                    "session": 2,
                    "duration": "20 minutes", 
                    "focus": "Focus on problem areas and transitions",
                    "goals": [
                        "Practice difficult transitions",
                        "Improve timing on slow sections",
                        "Refine narration for clarity",
                        "Test backup scenarios"
                    ]
                },
                {
                    "session": 3,
                    "duration": "25 minutes",
                    "focus": "Final polished run-through",
                    "goals": [
                        "Execute complete demo smoothly",
                        "Verify all timing targets met",
                        "Practice natural narration",
                        "Confirm technical reliability"
                    ]
                },
                {
                    "session": 4,
                    "duration": "15 minutes",
                    "focus": "Recording setup and final check",
                    "goals": [
                        "Test recording software and settings",
                        "Verify audio levels and quality",
                        "Final technical check of all components",
                        "Prepare for actual recording"
                    ]
                }
            ],
            "preparation_checklist": [
                "Review demo script thoroughly",
                "Understand each step's purpose and timing",
                "Practice smooth transitions between steps",
                "Prepare backup explanations for technical issues",
                "Test all demo personas and data",
                "Verify agent responsiveness",
                "Check frontend functionality",
                "Prepare recording environment"
            ]
        }
        
        return rehearsal_schedule
    
    def create_backup_scenarios(self) -> Dict[str, Any]:
        """Create backup scenarios for demo contingencies."""
        
        backup_scenarios = {
            "technical_failures": {
                "agent_failure": {
                    "description": "One or more agents fail during demo",
                    "backup_plan": "Use pre-recorded screenshots and explain expected behavior",
                    "preparation": [
                        "Create screenshots of key agent interactions",
                        "Prepare explanation of agent collaboration",
                        "Have architecture diagrams ready"
                    ]
                },
                "frontend_issues": {
                    "description": "Frontend has loading or display issues",
                    "backup_plan": "Use agent monitor and backend APIs directly",
                    "preparation": [
                        "Prepare curl commands for key operations",
                        "Have agent status endpoints ready",
                        "Know how to show raw agent responses"
                    ]
                },
                "network_problems": {
                    "description": "Network connectivity fails",
                    "backup_plan": "Use local mock data and offline demo",
                    "preparation": [
                        "Ensure all demo data is available locally",
                        "Prepare offline versions of key interfaces",
                        "Have static screenshots as fallback"
                    ]
                }
            },
            "timing_issues": {
                "running_long": {
                    "description": "Demo is taking longer than expected",
                    "backup_plan": "Skip detailed explanations, focus on visual demonstration",
                    "shortened_steps": [
                        "Step 1: 20s (reduce statistics explanation)",
                        "Step 2: 30s (show consent update only)",
                        "Step 3: 25s (quick query submission)",
                        "Step 4: 45s (focus on key agent interactions)",
                        "Step 5: 20s (show final anonymized result)",
                        "Step 6: 15s (quick result display)",
                        "Step 7: 15s (brief MeTTa overview)",
                        "Step 8: 10s (show ASI Alliance compliance)"
                    ]
                },
                "technical_delays": {
                    "description": "Technical issues cause delays",
                    "backup_plan": "Continue with explanation while troubleshooting",
                    "strategies": [
                        "Explain what should be happening",
                        "Show architecture while system recovers",
                        "Use the delay to emphasize key concepts",
                        "Move to next working component"
                    ]
                }
            },
            "content_adjustments": {
                "audience_technical": {
                    "description": "Audience is highly technical",
                    "adjustments": [
                        "Include more technical details about agent communication",
                        "Show actual MeTTa queries and responses",
                        "Explain privacy algorithms in detail",
                        "Demonstrate API endpoints and message formats"
                    ]
                },
                "audience_business": {
                    "description": "Audience is business-focused",
                    "adjustments": [
                        "Emphasize problem-solution fit",
                        "Focus on real-world impact and benefits",
                        "Highlight scalability and adoption potential",
                        "Show clear ROI and value proposition"
                    ]
                }
            }
        }
        
        return backup_scenarios
    
    def save_all_demo_materials(self):
        """Save all demo materials to files."""
        
        # Create demo directory if it doesn't exist
        os.makedirs("demo", exist_ok=True)
        
        # Generate and save demo script
        script_content = self.generate_demo_script()
        with open("demo/OPTIMIZED_DEMO_SCRIPT.md", "w") as f:
            f.write(script_content)
        
        # Generate and save timing cue cards
        cue_cards = self.generate_timing_cue_cards()
        with open("demo/timing_cue_cards.json", "w") as f:
            json.dump(cue_cards, f, indent=2)
        
        # Generate and save rehearsal schedule
        rehearsal_schedule = self.generate_rehearsal_schedule()
        with open("demo/rehearsal_schedule.json", "w") as f:
            json.dump(rehearsal_schedule, f, indent=2)
        
        # Generate and save backup scenarios
        backup_scenarios = self.create_backup_scenarios()
        with open("demo/backup_scenarios.json", "w") as f:
            json.dump(backup_scenarios, f, indent=2)
        
        # Create summary report
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "target_duration": f"{self.target_duration} seconds",
            "optimized_duration": f"{self.optimized_duration} seconds",
            "total_steps": len(self.demo_steps),
            "files_created": [
                "demo/OPTIMIZED_DEMO_SCRIPT.md",
                "demo/timing_cue_cards.json", 
                "demo/rehearsal_schedule.json",
                "demo/backup_scenarios.json"
            ],
            "next_steps": [
                "Review the optimized demo script",
                "Practice with timing cue cards",
                "Follow rehearsal schedule",
                "Prepare backup scenarios",
                "Record demo video"
            ]
        }
        
        with open("demo/demo_materials_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        return summary


def main():
    """Generate all demo video materials."""
    print("🎬 HealthSync Demo Video Script Generator")
    print("=" * 60)
    
    generator = DemoVideoScriptGenerator()
    
    try:
        summary = generator.save_all_demo_materials()
        
        print("✅ Demo materials generated successfully!")
        print(f"📄 Files created: {len(summary['files_created'])}")
        print(f"🎯 Target duration: {summary['target_duration']}")
        print(f"⏱️  Optimized duration: {summary['optimized_duration']}")
        print(f"📋 Total steps: {summary['total_steps']}")
        
        print("\n📁 Generated files:")
        for file in summary['files_created']:
            print(f"  - {file}")
        
        print("\n📋 Next steps:")
        for step in summary['next_steps']:
            print(f"  1. {step}")
        
        print("\n🎊 Demo video materials ready for ASI Alliance Hackathon!")
        
    except Exception as e:
        print(f"❌ Failed to generate demo materials: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())