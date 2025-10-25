#!/usr/bin/env python3
"""
Script to run all HealthSync agents simultaneously.
Useful for development and testing.
"""

import asyncio
import subprocess
import sys
import time
import signal
from typing import List
import os

from config import AGENT_CONFIG
from shared.utils.logging import get_logger

logger = get_logger("agent_runner")


class AgentRunner:
    """Manages running multiple agents simultaneously."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
    
    def start_agent(self, agent_name: str) -> subprocess.Popen:
        """Start a single agent process."""
        agent_script = f"agents/{agent_name}/agent.py"
        
        if not os.path.exists(agent_script):
            logger.error(f"Agent script not found: {agent_script}")
            return None
        
        try:
            logger.info(f"Starting {agent_name} agent...")
            process = subprocess.Popen(
                [sys.executable, agent_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"{agent_name} agent started with PID {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start {agent_name} agent: {str(e)}")
            return None
    
    def start_all_agents(self):
        """Start all configured agents."""
        logger.info("Starting all HealthSync agents...")
        
        for agent_name in AGENT_CONFIG.keys():
            process = self.start_agent(agent_name)
            if process:
                self.processes.append(process)
                time.sleep(2)  # Stagger startup to avoid port conflicts
        
        self.running = True
        logger.info(f"Started {len(self.processes)} agents successfully")
    
    def stop_all_agents(self):
        """Stop all running agents."""
        logger.info("Stopping all agents...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"Agent with PID {process.pid} stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing agent with PID {process.pid}")
                process.kill()
            except Exception as e:
                logger.error(f"Error stopping agent with PID {process.pid}: {str(e)}")
        
        self.processes.clear()
        self.running = False
        logger.info("All agents stopped")
    
    def check_agent_health(self):
        """Check if all agents are still running."""
        running_count = 0
        for process in self.processes:
            if process.poll() is None:  # Still running
                running_count += 1
            else:
                logger.warning(f"Agent with PID {process.pid} has stopped")
        
        logger.info(f"{running_count}/{len(self.processes)} agents running")
        return running_count
    
    async def monitor_agents(self):
        """Monitor agent health and restart if needed."""
        while self.running:
            try:
                running_count = self.check_agent_health()
                
                if running_count < len(self.processes):
                    logger.warning("Some agents have stopped, consider restarting")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring agents: {str(e)}")
                await asyncio.sleep(10)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all_agents()
        sys.exit(0)


def main():
    """Main function to run all agents."""
    runner = AgentRunner()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    try:
        # Start all agents
        runner.start_all_agents()
        
        if not runner.processes:
            logger.error("No agents started successfully")
            sys.exit(1)
        
        # Monitor agents
        logger.info("Monitoring agents... Press Ctrl+C to stop")
        asyncio.run(runner.monitor_agents())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        runner.stop_all_agents()


if __name__ == "__main__":
    main()