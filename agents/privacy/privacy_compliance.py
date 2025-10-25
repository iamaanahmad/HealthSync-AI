"""
Privacy compliance and audit system for HealthSync Privacy Agent.
Implements privacy rule evaluation, audit logging, and rule versioning.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uagents import Context
import hashlib
import json
import uuid


class PrivacyRule:
    """Represents a privacy rule with versioning."""
    
    def __init__(self, rule_id: str, rule_type: str, conditions: Dict[str, Any],
                 actions: Dict[str, Any], version: int = 1):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.conditions = conditions
        self.actions = actions
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate rule against given context."""
        # Check if all conditions are met
        conditions_met = True
        failed_conditions = []
        
        for condition_key, condition_value in self.conditions.items():
            context_value = context.get(condition_key)
            
            if isinstance(condition_value, dict):
                # Complex condition with operators
                operator = condition_value.get("operator")
                expected = condition_value.get("value")
                
                if operator == "equals":
                    if context_value != expected:
                        conditions_met = False
                        failed_conditions.append(condition_key)
                elif operator == "greater_than":
                    if not (context_value and context_value > expected):
                        conditions_met = False
                        failed_conditions.append(condition_key)
                elif operator == "less_than":
                    if not (context_value and context_value < expected):
                        conditions_met = False
                        failed_conditions.append(condition_key)
                elif operator == "in":
                    if context_value not in expected:
                        conditions_met = False
                        failed_conditions.append(condition_key)
                elif operator == "contains":
                    if expected not in context_value:
                        conditions_met = False
                        failed_conditions.append(condition_key)
            else:
                # Simple equality check
                if context_value != condition_value:
                    conditions_met = False
                    failed_conditions.append(condition_key)
        
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "conditions_met": conditions_met,
            "failed_conditions": failed_conditions,
            "actions": self.actions if conditions_met else {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "conditions": self.conditions,
            "actions": self.actions,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class PrivacyComplianceManager:
    """Manages privacy compliance rules and evaluation."""
    
    def __init__(self, metta_agent_address: Optional[str] = None):
        self.metta_agent_address = metta_agent_address
        self.privacy_rules: Dict[str, PrivacyRule] = {}
        self.current_version = 1
        
        # Initialize default privacy rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default privacy rules."""
        # Rule 1: Minimum k-anonymity requirement
        self.add_rule(PrivacyRule(
            rule_id="k_anonymity_minimum",
            rule_type="anonymization_requirement",
            conditions={
                "k_value": {"operator": "greater_than", "value": 4}
            },
            actions={
                "enforce": True,
                "message": "K-anonymity must be at least 5"
            }
        ))
        
        # Rule 2: Identifier hashing requirement
        self.add_rule(PrivacyRule(
            rule_id="identifier_hashing_required",
            rule_type="anonymization_requirement",
            conditions={
                "has_identifiers": True
            },
            actions={
                "require_hashing": True,
                "algorithm": "sha256",
                "message": "All identifiers must be hashed"
            }
        ))
        
        # Rule 3: Sensitive data suppression
        self.add_rule(PrivacyRule(
            rule_id="sensitive_data_suppression",
            rule_type="data_protection",
            conditions={
                "data_sensitivity": {"operator": "in", "value": ["high", "critical"]}
            },
            actions={
                "suppress": True,
                "message": "Highly sensitive data must be suppressed"
            }
        ))
        
        # Rule 4: Differential privacy for numeric data
        self.add_rule(PrivacyRule(
            rule_id="differential_privacy_numeric",
            rule_type="anonymization_requirement",
            conditions={
                "has_numeric_fields": True,
                "epsilon": {"operator": "greater_than", "value": 0}
            },
            actions={
                "add_noise": True,
                "noise_type": "laplace",
                "message": "Numeric fields should have differential privacy noise"
            }
        ))
    
    def add_rule(self, rule: PrivacyRule):
        """Add a privacy rule."""
        self.privacy_rules[rule.rule_id] = rule
    
    def update_privacy_rules(self, new_rules: Dict[str, Any], version: Optional[int] = None) -> Dict[str, Any]:
        """Update privacy rules with versioning."""
        if version:
            self.current_version = version
        else:
            self.current_version += 1
        
        # Convert new rules to PrivacyRule objects
        for rule_id, rule_data in new_rules.items():
            rule = PrivacyRule(
                rule_id=rule_id,
                rule_type=rule_data.get("rule_type", "custom"),
                conditions=rule_data.get("conditions", {}),
                actions=rule_data.get("actions", {}),
                version=self.current_version
            )
            self.privacy_rules[rule_id] = rule
        
        return {
            "version": self.current_version,
            "rule_count": len(self.privacy_rules),
            "updated_at": datetime.now().isoformat()
        }
    
    def get_current_version(self) -> int:
        """Get current privacy rules version."""
        return self.current_version
    
    def evaluate_local_rules(self, records: List[Dict[str, Any]], 
                            config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate privacy rules locally without MeTTa."""
        violations = []
        warnings = []
        
        # Build evaluation context
        context = {
            "record_count": len(records),
            "k_value": config.get("k_anonymity", 5),
            "has_identifiers": bool(config.get("identifier_fields")),
            "has_numeric_fields": bool(config.get("numeric_fields_for_noise")),
            "epsilon": config.get("epsilon", 1.0),
            "data_sensitivity": config.get("data_sensitivity", "medium")
        }
        
        # Evaluate each rule
        for rule_id, rule in self.privacy_rules.items():
            result = rule.evaluate(context)
            
            if not result["conditions_met"]:
                if rule.rule_type == "anonymization_requirement":
                    violations.append({
                        "rule_id": rule_id,
                        "rule_type": rule.rule_type,
                        "message": rule.actions.get("message", "Rule violation"),
                        "failed_conditions": result["failed_conditions"]
                    })
                else:
                    warnings.append({
                        "rule_id": rule_id,
                        "rule_type": rule.rule_type,
                        "message": rule.actions.get("message", "Rule warning"),
                        "failed_conditions": result["failed_conditions"]
                    })
        
        compliant = len(violations) == 0
        
        return {
            "compliant": compliant,
            "violations": violations,
            "warnings": warnings,
            "rules_evaluated": len(self.privacy_rules),
            "evaluation_timestamp": datetime.now().isoformat()
        }
    
    async def evaluate_privacy_rules(self, ctx: Context, records: List[Dict[str, Any]],
                                    config: Dict[str, Any], 
                                    metta_address: str) -> Dict[str, Any]:
        """Evaluate privacy rules using MeTTa Integration Agent."""
        # For now, use local evaluation
        # In production, this would query MeTTa for complex reasoning
        local_result = self.evaluate_local_rules(records, config)
        
        # TODO: Query MeTTa for advanced privacy rule reasoning
        # This would involve sending a message to MeTTa Integration Agent
        # with privacy rule queries and getting reasoning paths back
        
        return local_result
    
    async def store_rules_in_metta(self, ctx: Context, rules: Dict[str, Any],
                                  version: int, metta_address: str):
        """Store privacy rules in MeTTa Knowledge Graph."""
        # TODO: Implement MeTTa storage
        # This would send rules to MeTTa Integration Agent for storage
        pass


class PrivacyAuditLogger:
    """Logs anonymization operations with cryptographic verification."""
    
    def __init__(self):
        self.audit_logs: List[Dict[str, Any]] = []
    
    def _generate_audit_id(self) -> str:
        """Generate unique audit ID."""
        return f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
    
    def _calculate_verification_hash(self, audit_data: Dict[str, Any]) -> str:
        """Calculate cryptographic hash for audit verification."""
        # Create deterministic string from audit data
        audit_string = json.dumps(audit_data, sort_keys=True)
        return hashlib.sha256(audit_string.encode()).hexdigest()
    
    def log_anonymization(self, request_id: str, dataset_id: str, requester_id: str,
                         original_record_count: int, anonymized_record_count: int,
                         techniques_applied: List[str], 
                         privacy_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Log anonymization operation with cryptographic verification."""
        audit_id = self._generate_audit_id()
        timestamp = datetime.now()
        
        audit_data = {
            "audit_id": audit_id,
            "request_id": request_id,
            "dataset_id": dataset_id,
            "requester_id": requester_id,
            "original_record_count": original_record_count,
            "anonymized_record_count": anonymized_record_count,
            "techniques_applied": techniques_applied,
            "timestamp": timestamp.isoformat()
        }
        
        # Calculate verification hash
        verification_hash = self._calculate_verification_hash(audit_data)
        
        # Create complete audit entry
        audit_entry = {
            **audit_data,
            "verification_hash": verification_hash,
            "privacy_metrics": privacy_metrics,
            "verified": True
        }
        
        self.audit_logs.append(audit_entry)
        
        return audit_entry
    
    def verify_audit_entry(self, audit_id: str) -> Dict[str, Any]:
        """Verify integrity of an audit entry."""
        # Find audit entry
        audit_entry = None
        for entry in self.audit_logs:
            if entry["audit_id"] == audit_id:
                audit_entry = entry
                break
        
        if not audit_entry:
            return {
                "verified": False,
                "message": "Audit entry not found"
            }
        
        # Recalculate hash
        audit_data = {k: v for k, v in audit_entry.items() 
                     if k not in ["verification_hash", "privacy_metrics", "verified"]}
        calculated_hash = self._calculate_verification_hash(audit_data)
        
        # Compare hashes
        stored_hash = audit_entry["verification_hash"]
        verified = calculated_hash == stored_hash
        
        return {
            "verified": verified,
            "audit_id": audit_id,
            "stored_hash": stored_hash,
            "calculated_hash": calculated_hash,
            "message": "Audit entry verified" if verified else "Hash mismatch detected"
        }
    
    def get_audit_logs(self, request_id: Optional[str] = None,
                      dataset_id: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve audit logs with optional filtering."""
        filtered_logs = self.audit_logs
        
        if request_id:
            filtered_logs = [log for log in filtered_logs 
                           if log.get("request_id") == request_id]
        
        if dataset_id:
            filtered_logs = [log for log in filtered_logs 
                           if log.get("dataset_id") == dataset_id]
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_logs = [log for log in filtered_logs 
                           if datetime.fromisoformat(log["timestamp"]) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_logs = [log for log in filtered_logs 
                           if datetime.fromisoformat(log["timestamp"]) <= end_dt]
        
        return filtered_logs
    
    def calculate_privacy_metrics_report(self) -> Dict[str, Any]:
        """Calculate aggregate privacy metrics from audit logs."""
        if not self.audit_logs:
            return {
                "total_anonymizations": 0,
                "total_records_processed": 0,
                "average_retention_rate": 0,
                "techniques_usage": {}
            }
        
        total_original = sum(log["original_record_count"] for log in self.audit_logs)
        total_anonymized = sum(log["anonymized_record_count"] for log in self.audit_logs)
        
        # Count technique usage
        techniques_usage = {}
        for log in self.audit_logs:
            for technique in log.get("techniques_applied", []):
                techniques_usage[technique] = techniques_usage.get(technique, 0) + 1
        
        return {
            "total_anonymizations": len(self.audit_logs),
            "total_original_records": total_original,
            "total_anonymized_records": total_anonymized,
            "average_retention_rate": total_anonymized / total_original if total_original > 0 else 0,
            "techniques_usage": techniques_usage,
            "report_generated_at": datetime.now().isoformat()
        }
