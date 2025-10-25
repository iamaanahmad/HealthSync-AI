# HealthSync Setup Guide

This comprehensive guide will help you set up HealthSync from scratch, whether you're a developer, researcher, or system administrator.

## 🎯 Quick Start (5 Minutes)

For those who want to get HealthSync running immediately:

```bash
# 1. Clone and enter directory
git clone https://github.com/healthsync/healthsync.git
cd healthsync

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run installation check
python install_check.py

# 4. Generate demo data
cd demo && python demo_script.py && cd ..

# 5. Start all agents
python run_all_agents.py

# 6. Verify everything is working
curl http://localhost:8001/health
```

## 📋 Prerequisites

### System Requirements

| Component | Minimum | Recommended | Purpose |
|-----------|---------|-------------|---------|
| **Python** | 3.8 | 3.9+ | Agent runtime |
| **Memory** | 4GB RAM | 8GB RAM | Agent processing |
| **Storage** | 2GB free | 10GB free | Logs and data |
| **Network** | Ports 8001-8005 | Dedicated network | Agent communication |

### Software Dependencies

```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip
pip --version

# Check git
git --version

# Optional: Check Node.js for frontend
node --version  # Should be 16+
npm --version
```

## 🔧 Detailed Installation

### Step 1: Environment Setup

#### Option A: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv healthsync-env

# Activate virtual environment
# On Windows:
healthsync-env\Scripts\activate
# On macOS/Linux:
source healthsync-env/bin/activate

# Verify activation
which python  # Should point to virtual environment
```

#### Option B: Conda Environment
```bash
# Create conda environment
conda create -n healthsync python=3.9

# Activate environment
conda activate healthsync

# Verify activation
conda info --envs
```

### Step 2: Repository Setup

```bash
# Clone repository
git clone https://github.com/healthsync/healthsync.git
cd healthsync

# Verify repository structure
ls -la
# Should see: agents/, shared/, demo/, docs/, etc.
```

### Step 3: Dependency Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Install HealthSync in development mode
pip install -e .

# Verify installation
pip show healthsync
```

### Step 4: Configuration

#### Basic Configuration
```bash
# Copy example configuration
cp config.example.py config.py

# Edit configuration (optional)
nano config.py  # or your preferred editor
```

#### Environment Variables
```bash
# Create .env file
cat > .env << EOF
# Agent Configuration
PATIENT_CONSENT_PORT=8001
DATA_CUSTODIAN_PORT=8002
RESEARCH_QUERY_PORT=8003
PRIVACY_PORT=8004
METTA_INTEGRATION_PORT=8005

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs

# MeTTa Configuration
METTA_HOST=localhost
METTA_PORT=8080

# Security Configuration
JWT_SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
EOF
```

### Step 5: Directory Structure Setup

```bash
# Create necessary directories
mkdir -p logs
mkdir -p demo/datasets
mkdir -p demo/backups
mkdir -p demo/temp

# Set permissions (Unix/Linux/macOS)
chmod 755 logs demo
chmod 644 config.py

# Verify directory structure
tree -L 2  # or ls -la
```

## 🚀 Agent Deployment

### Local Development Deployment

#### Start Individual Agents

```bash
# Terminal 1: Patient Consent Agent
python agents/patient_consent/agent.py

# Terminal 2: Data Custodian Agent
python agents/data_custodian/agent.py

# Terminal 3: Research Query Agent
python agents/research_query/agent.py

# Terminal 4: Privacy Agent
python agents/privacy/agent.py

# Terminal 5: MeTTa Integration Agent
python agents/metta_integration/agent.py
```

#### Start All Agents (Recommended)

```bash
# Start all agents in background
python run_all_agents.py

# Check agent status
python -c "
import requests
ports = [8001, 8002, 8003, 8004, 8005]
for port in ports:
    try:
        r = requests.get(f'http://localhost:{port}/health')
        print(f'Agent on port {port}: {r.json()[\"status\"]}')
    except:
        print(f'Agent on port {port}: NOT RESPONDING')
"
```

### Production Deployment

#### Docker Deployment

```bash
# Build Docker images
docker build -t healthsync/patient-consent -f docker/Dockerfile.patient-consent .
docker build -t healthsync/data-custodian -f docker/Dockerfile.data-custodian .
docker build -t healthsync/research-query -f docker/Dockerfile.research-query .
docker build -t healthsync/privacy -f docker/Dockerfile.privacy .
docker build -t healthsync/metta-integration -f docker/Dockerfile.metta-integration .

# Run with Docker Compose
docker-compose up -d

# Check container status
docker-compose ps
```

#### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments.yaml
kubectl apply -f k8s/services.yaml

# Check deployment status
kubectl get pods -n healthsync
kubectl get services -n healthsync
```

## 🌐 Agentverse Registration

### Manual Registration

```bash
# Register each agent on Agentverse
python deployment/register_agents.py

# Verify registration
python deployment/verify_asi_one_integration.py
```

### Automated Deployment

```bash
# Complete deployment to Agentverse
python deployment/complete_deployment.py

# Monitor deployment
python deployment/agent_monitor.py
```

## 🎬 Demo Setup

### Generate Demo Data

```bash
# Navigate to demo directory
cd demo

# Generate personas and datasets
python demo_script.py

# Verify demo data
ls -la *.json datasets/

# Test demo reset functionality
python demo_reset_manager.py
```

### Run Demo Scenario

```bash
# Follow optimized demo script
cat OPTIMIZED_DEMO_SCRIPT.md

# Run timing optimization
python demo_timing_optimizer.py

# Practice with rehearsal schedule
cat rehearsal_schedule.json
```

## 🧪 Testing & Validation

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=agents --cov=shared --cov-report=html

# View coverage report
open htmlcov/index.html  # or your browser
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Test agent communication
python shared/protocols/test_communication_integration.py

# Test end-to-end workflows
pytest tests/e2e/ -v
```

### System Validation

```bash
# Validate complete system
python tests/system/validate_system.py

# Check ASI Alliance compliance
python tests/e2e/agentverse-compliance.test.py

# Verify Chat Protocol integration
python tests/e2e/chat-protocol-integration.test.py
```

## 🔍 Troubleshooting

### Common Installation Issues

#### Python Version Issues
```bash
# Problem: Python version too old
python --version  # Shows < 3.8

# Solution: Install newer Python
# On Ubuntu/Debian:
sudo apt update && sudo apt install python3.9

# On macOS with Homebrew:
brew install python@3.9

# On Windows: Download from python.org
```

#### Dependency Conflicts
```bash
# Problem: Package conflicts during installation
pip install -r requirements.txt  # Shows conflicts

# Solution: Use fresh virtual environment
deactivate  # Exit current environment
rm -rf healthsync-env  # Remove old environment
python -m venv healthsync-env  # Create new environment
source healthsync-env/bin/activate  # Activate
pip install -r requirements.txt  # Reinstall
```

#### Port Conflicts
```bash
# Problem: Ports already in use
python agents/patient_consent/agent.py  # Shows port error

# Solution: Check and kill processes
netstat -an | grep 800[1-5]  # Check ports
lsof -ti:8001 | xargs kill -9  # Kill process on port 8001

# Or: Change ports in config.py
```

### Agent Communication Issues

#### Agents Not Responding
```bash
# Check agent health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health

# Check agent logs
tail -f logs/*.log

# Restart specific agent
pkill -f "patient_consent/agent.py"
python agents/patient_consent/agent.py &
```

#### Message Delivery Failures
```bash
# Test agent communication
python shared/protocols/communication_demo.py

# Check message queues
python -c "
from shared.protocols.message_delivery import MessageDelivery
md = MessageDelivery()
print(md.get_queue_status())
"

# Clear message queues
python -c "
from shared.protocols.message_delivery import MessageDelivery
md = MessageDelivery()
md.clear_all_queues()
"
```

### Demo Issues

#### Demo Data Not Loading
```bash
# Regenerate demo data
cd demo
rm -f *.json datasets/*.json
python demo_script.py

# Check file permissions
ls -la *.json datasets/
chmod 644 *.json datasets/*.json
```

#### Timing Issues in Demo
```bash
# Optimize demo timing
python demo_timing_optimizer.py

# Practice with cue cards
cat timing_cue_cards.json

# Reset demo environment
python demo_reset_manager.py
```

## 📊 Monitoring & Maintenance

### Health Monitoring

```bash
# Create monitoring script
cat > monitor_health.sh << 'EOF'
#!/bin/bash
echo "HealthSync Agent Status Check"
echo "============================="

agents=("8001:Patient Consent" "8002:Data Custodian" "8003:Research Query" "8004:Privacy" "8005:MeTTa Integration")

for agent in "${agents[@]}"; do
    port="${agent%%:*}"
    name="${agent##*:}"
    
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ $name Agent (port $port): HEALTHY"
    else
        echo "❌ $name Agent (port $port): NOT RESPONDING"
    fi
done
EOF

chmod +x monitor_health.sh
./monitor_health.sh
```

### Log Management

```bash
# Rotate logs daily
cat > rotate_logs.sh << 'EOF'
#!/bin/bash
LOG_DIR="logs"
BACKUP_DIR="logs/archive"

mkdir -p "$BACKUP_DIR"

for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        filename=$(basename "$log_file" .log)
        cp "$log_file" "$BACKUP_DIR/${filename}_${timestamp}.log"
        > "$log_file"  # Clear current log
    fi
done
EOF

chmod +x rotate_logs.sh
```

### Performance Monitoring

```bash
# Monitor resource usage
cat > monitor_resources.py << 'EOF'
import psutil
import requests
import json
from datetime import datetime

def check_system_resources():
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "network_io": psutil.net_io_counters()._asdict()
    }

def check_agent_health():
    agents = {}
    for port in [8001, 8002, 8003, 8004, 8005]:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            agents[f"agent_{port}"] = response.json()
        except:
            agents[f"agent_{port}"] = {"status": "unreachable"}
    return agents

if __name__ == "__main__":
    report = {
        "system": check_system_resources(),
        "agents": check_agent_health()
    }
    
    print(json.dumps(report, indent=2))
    
    # Save to file
    with open(f"logs/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(report, f, indent=2)
EOF

python monitor_resources.py
```

## 🔄 Updates & Maintenance

### Updating HealthSync

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migration scripts (if any)
python scripts/migrate.py

# Restart agents
python run_all_agents.py --restart
```

### Backup & Recovery

```bash
# Create backup script
cat > backup_healthsync.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp config.py "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/" 2>/dev/null || true

# Backup logs
cp -r logs "$BACKUP_DIR/"

# Backup demo data
cp -r demo "$BACKUP_DIR/"

# Create archive
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup created: ${BACKUP_DIR}.tar.gz"
EOF

chmod +x backup_healthsync.sh
./backup_healthsync.sh
```

## 🎓 Next Steps

After successful setup:

1. **📖 Read the Documentation**: Explore `docs/ARCHITECTURE.md` for system details
2. **🎬 Run the Demo**: Follow `demo/README.md` for a complete demonstration
3. **🧪 Run Tests**: Execute the test suite to ensure everything works
4. **🤝 Join the Community**: Participate in discussions and contribute
5. **🚀 Deploy to Production**: Use the production deployment guides

## 📞 Getting Help

If you encounter issues during setup:

- **📋 Check Issues**: [GitHub Issues](https://github.com/healthsync/healthsync/issues)
- **💬 Ask Questions**: [GitHub Discussions](https://github.com/healthsync/healthsync/discussions)
- **📧 Email Support**: team@healthsync.ai
- **📖 Read Docs**: Check `docs/` directory for detailed documentation

## ✅ Setup Verification Checklist

Use this checklist to ensure your setup is complete:

- [ ] **Environment**: Python 3.8+ installed and virtual environment activated
- [ ] **Repository**: HealthSync cloned and dependencies installed
- [ ] **Configuration**: Config files created and environment variables set
- [ ] **Directories**: All necessary directories created with proper permissions
- [ ] **Agents**: All 5 agents start successfully and respond to health checks
- [ ] **Communication**: Agents can communicate with each other
- [ ] **Demo Data**: Demo personas and datasets generated successfully
- [ ] **Tests**: Unit and integration tests pass
- [ ] **Monitoring**: Health monitoring and logging working
- [ ] **Documentation**: Architecture and setup docs reviewed

Congratulations! You now have a fully functional HealthSync system ready for development, testing, or demonstration. 🎉