# HealthSync Demo System

This directory contains a comprehensive demo system for HealthSync, designed to showcase all system capabilities in a 3-5 minute video demonstration optimized for the ASI Alliance hackathon.

## Overview

The demo system includes:
- **Realistic patient and researcher personas** with diverse backgrounds
- **Sample healthcare datasets** that highlight privacy and ethics features  
- **Optimized demo script** with precise timing for video recording
- **Reset and cleanup functionality** for repeatable demonstrations
- **Timing optimization tools** to ensure demo fits within target duration

## Quick Start

### 1. Initialize Demo System

```bash
cd demo
python demo_script.py
```

This will:
- Generate realistic demo personas and datasets
- Create optimized demo script with timing cues
- Generate rehearsal schedule and timing cards
- Set up reset functionality for repeatable demos

### 2. Run Demo Reset (Before Each Demo)

```bash
python demo_reset_manager.py
```

This ensures:
- Fresh demo data for consistent experience
- Cleared temporary files and caches
- Reset agent states and consent preferences
- Backup of previous demo state

### 3. Follow Demo Script

Open `OPTIMIZED_DEMO_SCRIPT.md` for detailed step-by-step instructions with precise timing cues optimized for 3-5 minute video recording.

## Demo Components

### Core Files

| File | Purpose |
|------|---------|
| `personas.py` | Patient and researcher personas with realistic data |
| `demo_datasets.py` | Healthcare dataset generation with privacy features |
| `demo_script.py` | Main demo orchestration and execution |
| `demo_timing_optimizer.py` | Timing optimization for video recording |
| `demo_reset_manager.py` | Reset and cleanup for repeatable demos |

### Generated Files

| File | Description |
|------|-------------|
| `OPTIMIZED_DEMO_SCRIPT.md` | Step-by-step demo script with timing |
| `timing_cue_cards.json` | Presenter cue cards with timing alerts |
| `rehearsal_schedule.json` | Practice schedule for demo preparation |
| `RESET_CHECKLIST.md` | Manual verification checklist |
| `personas_data.json` | Demo personas in JSON format |
| `demo_results.json` | Demo execution results and metrics |

## Demo Personas

### Patients

**Sarah Chen (patient_001)**
- 34-year-old tech professional with Type 2 diabetes
- Demonstrates consent management and updates
- Shows privacy-conscious data sharing decisions

**Marcus Johnson (patient_002)**  
- 67-year-old retired worker with multiple chronic conditions
- Illustrates selective consent for cardiovascular research
- Cautious about genetic data sharing

**Emma Rodriguez (patient_003)**
- 28-year-old graduate student interested in mental health research
- Shows comprehensive consent for research participation
- Demonstrates young adult engagement with health data

### Researchers

**Dr. Jennifer Park (researcher_001)**
- Stanford endocrinologist researching diabetes prevention
- Submits AI-driven diabetes prevention study query
- Demonstrates ethical research query submission

**Dr. Michael Thompson (researcher_002)**
- Johns Hopkins cardiologist studying health disparities
- Shows multi-ethnic cardiovascular outcomes research
- Illustrates complex data requirements and ethics approval

## Demo Flow (240 seconds target)

### Step 1: System Overview (25s)
- Introduce healthcare data silos problem
- Show ASI Alliance technology integration
- Display agent architecture overview

### Step 2: Patient Consent Management (35s)
- Login as Sarah Chen
- Update consent preferences for diabetes research
- Demonstrate Chat Protocol integration with ASI:One
- Show real-time consent updates

### Step 3: Research Query Submission (30s)
- Login as Dr. Jennifer Park
- Submit diabetes prevention research query
- Show ethical compliance validation
- Display MeTTa reasoning for ethics approval

### Step 4: Multi-Agent Collaboration (50s)
- Switch to Agent Activity Monitor
- Watch 5 agents collaborate autonomously:
  - Research Query Agent validates ethics
  - Patient Consent Agent checks permissions
  - Data Custodian Agent finds matching datasets
  - Privacy Agent anonymizes data
  - MeTTa Integration Agent provides reasoning
- Show real-time message flow between agents

### Step 5: Privacy & Anonymization (25s)
- Display Privacy Agent anonymization process
- Show k-anonymity compliance (k≥5)
- Verify removal of personally identifiable information
- Display privacy compliance metrics

### Step 6: Research Results Delivery (20s)
- Return to researcher portal
- Display anonymized research dataset
- Show data quality and provenance metrics
- Demonstrate secure result export

### Step 7: MeTTa Knowledge Graph Exploration (20s)
- Open MeTTa Explorer interface
- Browse medical ontologies and relationships
- Execute complex reasoning queries
- Show nested query results and reasoning paths

### Step 8: ASI Alliance Technology Integration (15s)
- Show all agents registered on Agentverse
- Demonstrate Chat Protocol compliance
- Display Innovation Lab badges
- Verify ASI:One integration

## Demo Data Highlights

### Privacy Features Demonstrated
- **K-anonymity**: Minimum k=5 for all shared datasets
- **Data generalization**: Age ranges instead of exact ages
- **Identifier hashing**: Cryptographic hashing of patient IDs
- **Consent enforcement**: Real-time consent validation
- **Audit trails**: Complete logging of all data access

### Ethics Features Demonstrated  
- **MeTTa reasoning**: Complex ethics rule evaluation
- **IRB compliance**: Automatic ethics approval verification
- **Research categorization**: Granular consent by research type
- **Transparency**: Clear reasoning paths for all decisions

### ASI Alliance Technology Integration
- **uAgents Framework**: All 5 agents built with uAgents
- **Agentverse Registration**: Agents discoverable with proper manifests
- **Chat Protocol**: Natural language interaction through ASI:One
- **MeTTa Knowledge Graph**: Medical ontologies and reasoning
- **Innovation Lab Badges**: Proper hackathon categorization

## Rehearsal and Preparation

### Rehearsal Schedule (2 hours total)

1. **Session 1 (30 min)**: Complete run-through with timing
2. **Session 2 (20 min)**: Focus on problem areas and transitions  
3. **Session 3 (25 min)**: Final polished run-through
4. **Session 4 (15 min)**: Recording setup and final check

### Pre-Recording Checklist

- [ ] All agents running and responsive
- [ ] Frontend loaded with demo data
- [ ] Screen recording software configured (1080p, 30fps)
- [ ] Audio levels tested and optimized
- [ ] Browser zoom set to 100%
- [ ] Notifications disabled
- [ ] Demo personas logged in and ready
- [ ] Backup scenarios prepared

## Reset and Cleanup

### Full Reset (Before Important Demos)
```bash
python demo_reset_manager.py
```
- Creates backup of current state
- Resets all personas to initial state
- Clears temporary files and caches
- Regenerates fresh demo data
- Verifies reset completeness

### Quick Reset (Between Practice Runs)
```bash
python -c "
import asyncio
from demo_reset_manager import DemoResetManager
asyncio.run(DemoResetManager().quick_reset())
"
```
- Rapid reset for practice iterations
- Clears demo state without full backup
- Resets key persona consent preferences

## Troubleshooting

### Common Issues

**Demo running too long?**
- Use timing cue cards to stay on track
- Skip detailed explanations, focus on visual demonstration
- Practice transitions to reduce dead time

**Technical issues during demo?**
- Have pre-recorded screenshots ready as backup
- Explain expected behavior if live demo fails
- Use backup scenarios prepared in rehearsal

**Agents not responding?**
- Check agent status in monitor dashboard
- Restart agents if necessary
- Use mock data if agents are unavailable

### Backup Plans

**If agents fail:**
- Use pre-generated demo results
- Explain the expected agent collaboration
- Show agent architecture diagrams

**If frontend issues:**
- Use screenshots of key interfaces
- Narrate the user experience
- Focus on backend agent collaboration

**If timing issues:**
- Have shortened versions of each step ready
- Know which steps can be combined or skipped
- Practice smooth transitions between sections

## Files and Directories

```
demo/
├── README.md                    # This file
├── personas.py                  # Demo personas and sample data
├── demo_datasets.py            # Healthcare dataset generation
├── demo_script.py              # Main demo orchestration
├── demo_timing_optimizer.py    # Timing optimization tools
├── demo_reset_manager.py       # Reset and cleanup functionality
├── OPTIMIZED_DEMO_SCRIPT.md    # Generated demo script
├── timing_cue_cards.json       # Presenter timing cues
├── rehearsal_schedule.json     # Practice schedule
├── RESET_CHECKLIST.md          # Manual verification checklist
├── personas_data.json          # Demo personas in JSON
├── demo_results.json           # Demo execution results
├── datasets/                   # Generated healthcare datasets
├── backups/                    # Demo state backups
└── temp/                       # Temporary files (auto-cleaned)
```

## Success Metrics

The demo system tracks several metrics to ensure effectiveness:

- **Timing Accuracy**: How well actual timing matches target duration
- **Content Coverage**: Percentage of key demo points covered
- **Technical Reliability**: Success rate of agent interactions
- **Audience Engagement**: Clear demonstration of problem → solution flow

Target metrics for successful demo:
- Duration: 180-300 seconds (3-5 minutes)
- Timing accuracy: <10% deviation from target
- Content coverage: 100% of critical demo points
- Technical success: >95% of agent interactions work correctly

## Support

For issues with the demo system:
1. Check the troubleshooting section above
2. Review the reset checklist for verification steps
3. Run demo reset to ensure clean state
4. Practice with rehearsal schedule before important demos

The demo system is designed to be robust and repeatable, ensuring consistent high-quality demonstrations of HealthSync's capabilities for the ASI Alliance hackathon.