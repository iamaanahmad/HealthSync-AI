"""
Core anonymization algorithms for HealthSync Privacy Agent.
Implements k-anonymity, data generalization, cryptographic hashing, and differential privacy.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import hashlib
import random
from datetime import datetime, date
from collections import defaultdict
import math


class IdentifierHasher:
    """Cryptographic hashing for patient identifiers."""
    
    def __init__(self, salt: str = "healthsync_privacy_salt"):
        self.salt = salt
    
    def hash_identifier(self, identifier: str, algorithm: str = "sha256") -> str:
        """Hash an identifier using specified algorithm."""
        salted = f"{self.salt}:{identifier}"
        
        if algorithm == "sha256":
            return hashlib.sha256(salted.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(salted.encode()).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(salted.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
    
    def hash_record_identifiers(self, record: Dict[str, Any], 
                                identifier_fields: List[str]) -> Dict[str, Any]:
        """Hash all identifier fields in a record."""
        hashed_record = record.copy()
        
        for field in identifier_fields:
            if field in hashed_record:
                original_value = hashed_record[field]
                hashed_record[field] = self.hash_identifier(str(original_value))
                hashed_record[f"{field}_hashed"] = True
        
        return hashed_record


class DataGeneralizer:
    """Data generalization and suppression techniques."""
    
    @staticmethod
    def generalize_age(age: int, bin_size: int = 5) -> str:
        """Generalize age into bins."""
        if age < 0:
            return "unknown"
        
        lower_bound = (age // bin_size) * bin_size
        upper_bound = lower_bound + bin_size - 1
        return f"{lower_bound}-{upper_bound}"
    
    @staticmethod
    def generalize_date(date_value: date, precision: str = "month") -> str:
        """Generalize date to specified precision."""
        if precision == "year":
            return str(date_value.year)
        elif precision == "month":
            return f"{date_value.year}-{date_value.month:02d}"
        elif precision == "quarter":
            quarter = (date_value.month - 1) // 3 + 1
            return f"{date_value.year}-Q{quarter}"
        else:
            return date_value.isoformat()
    
    @staticmethod
    def generalize_zipcode(zipcode: str, digits: int = 3) -> str:
        """Generalize zipcode to specified number of digits."""
        if not zipcode:
            return "***"
        
        zipcode_str = str(zipcode).replace("-", "")
        if len(zipcode_str) < digits:
            return "*" * digits
        
        return zipcode_str[:digits] + "*" * (len(zipcode_str) - digits)
    
    @staticmethod
    def generalize_numeric_range(value: float, ranges: List[Tuple[float, float]]) -> str:
        """Generalize numeric value into predefined ranges."""
        for lower, upper in ranges:
            if lower <= value < upper:
                return f"{lower}-{upper}"
        
        # If value doesn't fit in any range
        if value < ranges[0][0]:
            return f"<{ranges[0][0]}"
        else:
            return f">={ranges[-1][1]}"
    
    @staticmethod
    def suppress_field(record: Dict[str, Any], field: str, 
                       suppression_value: str = "***") -> Dict[str, Any]:
        """Suppress a field by replacing with suppression value."""
        suppressed_record = record.copy()
        if field in suppressed_record:
            suppressed_record[field] = suppression_value
            suppressed_record[f"{field}_suppressed"] = True
        return suppressed_record
    
    @staticmethod
    def generalize_record(record: Dict[str, Any], 
                         generalization_rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Apply generalization rules to a record."""
        generalized = record.copy()
        
        for field, rules in generalization_rules.items():
            if field not in generalized:
                continue
            
            rule_type = rules.get("type")
            value = generalized[field]
            
            if rule_type == "age_bin":
                bin_size = rules.get("bin_size", 5)
                generalized[field] = DataGeneralizer.generalize_age(int(value), bin_size)
            
            elif rule_type == "date_precision":
                precision = rules.get("precision", "month")
                if isinstance(value, str):
                    value = datetime.fromisoformat(value).date()
                generalized[field] = DataGeneralizer.generalize_date(value, precision)
            
            elif rule_type == "zipcode":
                digits = rules.get("digits", 3)
                generalized[field] = DataGeneralizer.generalize_zipcode(str(value), digits)
            
            elif rule_type == "numeric_range":
                ranges = rules.get("ranges", [])
                generalized[field] = DataGeneralizer.generalize_numeric_range(float(value), ranges)
            
            elif rule_type == "suppress":
                suppression_value = rules.get("value", "***")
                generalized[field] = suppression_value
                generalized[f"{field}_suppressed"] = True
        
        return generalized


class NoiseInjector:
    """Statistical noise injection for differential privacy."""
    
    def __init__(self, epsilon: float = 1.0, seed: Optional[int] = None):
        """
        Initialize noise injector.
        
        Args:
            epsilon: Privacy budget parameter (smaller = more privacy, more noise)
            seed: Random seed for reproducibility
        """
        self.epsilon = epsilon
        if seed is not None:
            random.seed(seed)
    
    def laplace_noise(self, sensitivity: float = 1.0) -> float:
        """Generate Laplace noise for differential privacy."""
        scale = sensitivity / self.epsilon
        # Laplace distribution: sample from uniform and transform
        u = random.uniform(-0.5, 0.5)
        return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))
    
    def gaussian_noise(self, sensitivity: float = 1.0, delta: float = 1e-5) -> float:
        """Generate Gaussian noise for differential privacy."""
        sigma = math.sqrt(2 * math.log(1.25 / delta)) * sensitivity / self.epsilon
        return random.gauss(0, sigma)
    
    def add_noise_to_numeric(self, value: float, noise_type: str = "laplace",
                            sensitivity: float = 1.0) -> float:
        """Add noise to a numeric value."""
        if noise_type == "laplace":
            noise = self.laplace_noise(sensitivity)
        elif noise_type == "gaussian":
            noise = self.gaussian_noise(sensitivity)
        else:
            raise ValueError(f"Unsupported noise type: {noise_type}")
        
        return value + noise
    
    def add_noise_to_count(self, count: int, sensitivity: int = 1) -> int:
        """Add noise to a count value and ensure non-negative."""
        noisy_count = count + self.laplace_noise(float(sensitivity))
        return max(0, int(round(noisy_count)))
    
    def add_noise_to_record(self, record: Dict[str, Any], 
                           numeric_fields: List[str],
                           noise_type: str = "laplace",
                           sensitivity: float = 1.0) -> Dict[str, Any]:
        """Add noise to numeric fields in a record."""
        noisy_record = record.copy()
        
        for field in numeric_fields:
            if field in noisy_record and isinstance(noisy_record[field], (int, float)):
                original_value = noisy_record[field]
                noisy_value = self.add_noise_to_numeric(
                    float(original_value), 
                    noise_type, 
                    sensitivity
                )
                noisy_record[field] = noisy_value
                noisy_record[f"{field}_noised"] = True
        
        return noisy_record


class KAnonymityProcessor:
    """K-anonymity implementation for group privacy."""
    
    def __init__(self, k: int = 5):
        """
        Initialize k-anonymity processor.
        
        Args:
            k: Minimum group size for k-anonymity (k≥5 as per requirements)
        """
        if k < 5:
            raise ValueError("k must be at least 5 for privacy requirements")
        self.k = k
    
    def identify_quasi_identifiers(self, records: List[Dict[str, Any]], 
                                   quasi_identifier_fields: List[str]) -> List[Tuple]:
        """Extract quasi-identifier combinations from records."""
        qi_combinations = []
        
        for record in records:
            qi_tuple = tuple(record.get(field) for field in quasi_identifier_fields)
            qi_combinations.append(qi_tuple)
        
        return qi_combinations
    
    def calculate_equivalence_classes(self, records: List[Dict[str, Any]],
                                     quasi_identifier_fields: List[str]) -> Dict[Tuple, List[int]]:
        """Group records into equivalence classes based on quasi-identifiers."""
        equivalence_classes = defaultdict(list)
        
        for idx, record in enumerate(records):
            qi_tuple = tuple(record.get(field) for field in quasi_identifier_fields)
            equivalence_classes[qi_tuple].append(idx)
        
        return dict(equivalence_classes)
    
    def check_k_anonymity(self, records: List[Dict[str, Any]],
                         quasi_identifier_fields: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """Check if dataset satisfies k-anonymity."""
        if len(records) < self.k:
            return False, {
                "satisfies_k_anonymity": False,
                "reason": f"Dataset has fewer than {self.k} records",
                "total_records": len(records),
                "k_value": self.k,
                "violations": []
            }
        
        equivalence_classes = self.calculate_equivalence_classes(records, quasi_identifier_fields)
        
        # Check if all equivalence classes have at least k members
        small_classes = []
        for qi_tuple, indices in equivalence_classes.items():
            if len(indices) < self.k:
                small_classes.append({
                    "quasi_identifiers": qi_tuple,
                    "size": len(indices)
                })
        
        satisfies = len(small_classes) == 0
        
        result = {
            "satisfies_k_anonymity": satisfies,
            "k_value": self.k,
            "total_records": len(records),
            "equivalence_classes": len(equivalence_classes),
            "smallest_class_size": min(len(indices) for indices in equivalence_classes.values()),
            "violations": small_classes
        }
        
        return satisfies, result
    
    def enforce_k_anonymity(self, records: List[Dict[str, Any]],
                           quasi_identifier_fields: List[str],
                           strategy: str = "suppress") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Enforce k-anonymity using specified strategy."""
        equivalence_classes = self.calculate_equivalence_classes(records, quasi_identifier_fields)
        
        anonymized_records = []
        suppressed_count = 0
        generalized_count = 0
        
        for qi_tuple, indices in equivalence_classes.items():
            class_size = len(indices)
            
            if class_size >= self.k:
                # Class satisfies k-anonymity, keep records
                for idx in indices:
                    anonymized_records.append(records[idx].copy())
            else:
                # Class violates k-anonymity
                if strategy == "suppress":
                    # Suppress these records (don't include them)
                    suppressed_count += class_size
                
                elif strategy == "generalize":
                    # Generalize quasi-identifiers further
                    # For now, we'll suppress as generalization requires domain knowledge
                    suppressed_count += class_size
                
                elif strategy == "sample":
                    # Sample records to reach k (may duplicate)
                    while len(indices) < self.k:
                        indices.append(random.choice(indices))
                    
                    for idx in indices[:self.k]:
                        anonymized_records.append(records[idx].copy())
                    generalized_count += self.k
        
        metrics = {
            "original_records": len(records),
            "anonymized_records": len(anonymized_records),
            "suppressed_records": suppressed_count,
            "generalized_records": generalized_count,
            "k_value": self.k,
            "strategy": strategy,
            "data_retention_rate": len(anonymized_records) / len(records) if records else 0
        }
        
        return anonymized_records, metrics


class AnonymizationEngine:
    """Main anonymization engine coordinating all techniques."""
    
    def __init__(self, k: int = 5, epsilon: float = 1.0, salt: str = "healthsync_privacy"):
        """
        Initialize anonymization engine.
        
        Args:
            k: K-anonymity parameter (minimum group size)
            epsilon: Differential privacy parameter
            salt: Salt for cryptographic hashing
        """
        self.k_anonymity = KAnonymityProcessor(k=k)
        self.hasher = IdentifierHasher(salt=salt)
        self.generalizer = DataGeneralizer()
        self.noise_injector = NoiseInjector(epsilon=epsilon)
        
        self.k = k
        self.epsilon = epsilon
    
    def anonymize_dataset(self, records: List[Dict[str, Any]],
                         config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Anonymize a complete dataset using configured techniques.
        
        Args:
            records: List of data records to anonymize
            config: Anonymization configuration with fields:
                - identifier_fields: Fields to hash
                - quasi_identifier_fields: Fields for k-anonymity
                - generalization_rules: Rules for data generalization
                - numeric_fields_for_noise: Fields to add differential privacy noise
                - k_anonymity_strategy: Strategy for enforcing k-anonymity
        
        Returns:
            Tuple of (anonymized_records, metrics)
        """
        if not records:
            return [], {"error": "No records to anonymize"}
        
        # Extract configuration
        identifier_fields = config.get("identifier_fields", [])
        quasi_identifier_fields = config.get("quasi_identifier_fields", [])
        generalization_rules = config.get("generalization_rules", {})
        numeric_fields_for_noise = config.get("numeric_fields_for_noise", [])
        k_strategy = config.get("k_anonymity_strategy", "suppress")
        
        metrics = {
            "original_record_count": len(records),
            "techniques_applied": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: Hash identifiers
        processed_records = []
        for record in records:
            hashed_record = self.hasher.hash_record_identifiers(record, identifier_fields)
            processed_records.append(hashed_record)
        
        if identifier_fields:
            metrics["techniques_applied"].append("cryptographic_hashing")
            metrics["hashed_fields"] = identifier_fields
        
        # Step 2: Apply generalization
        if generalization_rules:
            generalized_records = []
            for record in processed_records:
                generalized = self.generalizer.generalize_record(record, generalization_rules)
                generalized_records.append(generalized)
            processed_records = generalized_records
            
            metrics["techniques_applied"].append("data_generalization")
            metrics["generalized_fields"] = list(generalization_rules.keys())
        
        # Step 3: Enforce k-anonymity
        if quasi_identifier_fields:
            # Check k-anonymity before enforcement
            satisfies, k_check = self.k_anonymity.check_k_anonymity(
                processed_records, 
                quasi_identifier_fields
            )
            
            metrics["k_anonymity_check"] = k_check
            
            # Always enforce k-anonymity to ensure compliance
            processed_records, k_metrics = self.k_anonymity.enforce_k_anonymity(
                processed_records,
                quasi_identifier_fields,
                strategy=k_strategy
            )
            metrics["k_anonymity_enforcement"] = k_metrics
            metrics["techniques_applied"].append("k_anonymity")
        
        # Step 4: Add differential privacy noise
        if numeric_fields_for_noise:
            noisy_records = []
            for record in processed_records:
                noisy_record = self.noise_injector.add_noise_to_record(
                    record,
                    numeric_fields_for_noise
                )
                noisy_records.append(noisy_record)
            processed_records = noisy_records
            
            metrics["techniques_applied"].append("differential_privacy")
            metrics["noised_fields"] = numeric_fields_for_noise
            metrics["epsilon"] = self.epsilon
        
        # Final metrics
        metrics["anonymized_record_count"] = len(processed_records)
        metrics["data_retention_rate"] = (
            len(processed_records) / len(records) if records else 0
        )
        
        return processed_records, metrics
    
    def calculate_privacy_metrics(self, original_records: List[Dict[str, Any]],
                                  anonymized_records: List[Dict[str, Any]],
                                  quasi_identifier_fields: List[str]) -> Dict[str, Any]:
        """Calculate privacy metrics for anonymized dataset."""
        metrics = {}
        
        # K-anonymity metrics
        if quasi_identifier_fields and anonymized_records:
            satisfies, k_check = self.k_anonymity.check_k_anonymity(
                anonymized_records,
                quasi_identifier_fields
            )
            metrics["k_anonymity"] = k_check
        
        # Data utility metrics
        metrics["data_utility"] = {
            "original_count": len(original_records),
            "anonymized_count": len(anonymized_records),
            "retention_rate": len(anonymized_records) / len(original_records) if original_records else 0,
            "suppression_rate": 1 - (len(anonymized_records) / len(original_records)) if original_records else 0
        }
        
        return metrics
