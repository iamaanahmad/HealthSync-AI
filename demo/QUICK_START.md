# 🚀 HealthSync Demo - Quick Start Guide

**Goal:** Record a 4-5 minute demo video showcasing all HealthSync features

---

## ⚡ 4-Step Setup (5 Minutes)

### 1️⃣ Start All Agents
```bash
# From project root
python run_all_agents.py
```

**Verify:** You should see 5 agents start with "Chat Protocol: ENABLED ✅"

### 2️⃣ Start Frontend (Web Application)
```bash
# From project root
cd src
npm install  # First time only
npm run dev
```

**Verify:** Browser opens to http://localhost:9002 with HealthSync homepage

**Frontend Pages:**
- 🏠 **Home** - System overview and introduction
- 📊 **Dashboard** - Patient consent management  
- 🖥️ **Monitor** - Real-time agent activity viewer
- 🔬 **Researcher** - Research query submission portal
- 🧠 **MeTTa Explorer** - Knowledge graph visualization

### 3️⃣ Generate Demo Data
```bash
cd demo
python demo_script.py
```

**Verify:** Files created:
- `personas_data.json` - Demo patients and researchers
- `demo_results.json` - Execution results
- `datasets/` - Sample healthcare data

### 4️⃣ Review Demo Script
Open `../DEMO_WALKTHROUGH.md` for complete step-by-step recording guide

---

## 🎬 Recording Checklist

**Before Recording:**
- [ ] All 5 agents running (check terminals)
- [ ] Frontend running on http://localhost:9002
- [ ] All frontend pages tested (Dashboard, Monitor, Researcher, MeTTa)
- [ ] Agentverse dashboard open and logged in
- [ ] Screen recorder ready (1080p, 30fps)
- [ ] Audio tested and clear
- [ ] Notifications turned OFF
- [ ] Browser at 100% zoom
- [ ] Script reviewed and practiced

**During Recording:**
- Follow DEMO_WALKTHROUGH.md timing cues
- **Use frontend UI as primary demo interface**
- Switch between frontend pages to show different features
- Show agent logs in terminals as supporting evidence
- Highlight real-time agent coordination in Monitor page
- Emphasize professional, production-ready UI
- Show ASI Alliance technology integration

**After Recording:**
- [ ] Check audio quality
- [ ] Verify all key points covered
- [ ] Duration: 4-5 minutes ✅
- [ ] Upload to YouTube
- [ ] Add link to README.md

---

## 📂 Demo Files Reference

| File | Purpose |
|------|---------|
| `personas.py` | Patient and researcher personas |
| `demo_datasets.py` | Healthcare dataset generator |
| `demo_script.py` | Main demo orchestration |
| `personas_data.json` | Generated demo personas |
| `demo_results.json` | Demo execution results |
| `datasets/` | Sample healthcare data |
| `OPTIMIZED_DEMO_SCRIPT.md` | Detailed timing script |
| `README.md` | Demo system documentation |
| `RESET_CHECKLIST.md` | Reset procedures |

---

## 🎯 Key Demo Moments

**Must Show:**
1. ✅ Problem: Healthcare data silos ($3.2T problem)
2. ✅ **Frontend**: Professional Next.js web application
3. ✅ **Dashboard**: Patient consent management UI
4. ✅ **Monitor**: Real-time agent activity visualization
5. ✅ **Researcher Portal**: Query submission interface
6. ✅ **MeTTa Explorer**: Knowledge graph visualization
7. ✅ Agent collaboration: All 5 coordinating (visible in UI + logs)
8. ✅ Privacy: K-anonymity k≥5 with metrics dashboard
9. ✅ Results: Anonymized data with export functionality
10. ✅ ASI Alliance: All technologies integrated throughout

**Timing:** ~30-40 seconds each = 4-5 minutes total

---

## 🚨 Quick Troubleshooting

**Agents not starting?**
```bash
pip install -r requirements.txt
python install_check.py
```

**Frontend not starting?**
```bash
cd src
npm install
npm run dev
# Should open http://localhost:9002
```

**Demo data missing?**
```bash
cd demo
python demo_script.py
```

**Need to reset?**
```bash
cd demo
rm demo_results.json personas_data.json
python demo_script.py
```

---

## 📊 Success = Judges Can Answer YES

- [ ] Problem clear? (Healthcare data silos)
- [ ] Solution understood? (Autonomous agents)
- [ ] All ASI Alliance tech shown? (uAgents, Agentverse, MeTTa, Chat Protocol)
- [ ] Privacy demonstrated? (K-anonymity)
- [ ] Agents coordinating? (Real-time logs)
- [ ] Impact obvious? (Minutes vs months)

---

## 🎬 Ready to Record?

1. **Practice once** following DEMO_WALKTHROUGH.md
2. **Check timing** - aim for 4:00-4:30
3. **Record** when confident
4. **Upload** to YouTube
5. **Link** in README.md

**You've got this! 🚀**

For detailed walkthrough: See `../DEMO_WALKTHROUGH.md`
