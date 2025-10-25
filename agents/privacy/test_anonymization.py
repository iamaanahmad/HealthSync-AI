"""
Unit tests for anonymization algorithms.
Tests k-anonymity, data generalization, cryptographic hashing, and differential privacy.
"""

import pytest
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import hashlib

from .anonymization import (
    AnonymizationEngine,
    KAnonymityProcessor,
    DataGeneralizer,
    IdentifierHasher,
    NoiseInjector
)


class TestIdentifierHasher:
    """Test cryptographic hashing for patient identifiers."""
    
    def test_hash_identifier_sha256(self):
        """Test SHA-256 hashing of identifiers."""
        hasher = IdentifierHasher(salt="test_salt")
        
        identifier = "PATIENT-12345"
        hashed = hasher.hash_identifier(identifier, algorithm="sha256")
        
        assert len(hashed) == 64  # SHA-256 produces 64 hex characters
        assert hashed != identifier
        
        # Same input should produce same hash
        hashed2 = hasher.hash_identifier(identifier, algorithm="sha256")
        assert hashed == hashed2
    
    def test_hash_identifier_different_algorithms(self):
        """Test different hashing algorithms."""
        hasher = IdentifierHasher()
        identifier = "PATIENT-12345"
        
        sha256_hash = hasher.hash_identifier(identifier, "sha256")
        sha512_hash = hasher.hash_identifier(identifier, "sha512")
        md5_hash = hasher.hash_identifier(identifier, "md5")
        
        assert len(sha256_hash) == 64
        assert len(sha512_hash) == 128
        assert len(md5_hash) == 32
        
        # All should be different
        assert sha256_hash != sha512_hash != md5_hash
    
    def test_hash_record_identifiers(self):
        """Test hashing multiple identifier fields in a record."""
        hasher = IdentifierHasher()
        
        record = {
            "patient_id": "PATIENT-001",
            "ssn": "123-45-6789",
            "name": "John Doe",
            "age": 45
        }
        
        identifier_fields = ["patient_id", "ssn"]
        hashed_record = hasher.hash_record_identifiers(record, identifier_fields)
        
        # Identifier fields should be hashed
        assert hashed_record["patient_id"] != record["patient_id"]
        assert hashed_record["ssn"] != record["ssn"]
        assert hashed_record["patient_id_hashed"] is True
        assert hashed_record["ssn_hashed"] is True
        
        # Non-identifier fields should remain unchanged
        assert hashed_record["name"] == record["name"]
        assert hashed_record["age"] == record["age"]
    
    def test_salt_affects_hash(self):
        """Test that different salts produce different hashes."""
        hasher1 = IdentifierHasher(salt="salt1")
        hasher2 = IdentifierHasher(salt="salt2")
        
        identifier = "PATIENT-12345"
        hash1 = hasher1.hash_identifier(identifier)
        hash2 = hasher2.hash_identifier(identifier)
        
        assert hash1 != hash2


class TestDataGeneralizer:
    """Test data generalization and suppression techniques."""
    
    def test_generalize_age(self):
        """Test age generalization into bins."""
        assert DataGeneralizer.generalize_age(23, bin_size=5) == "20-24"
        assert DataGeneralizer.generalize_age(45, bin_size=5) == "45-49"
        assert DataGeneralizer.generalize_age(30, bin_size=10) == "30-39"
        assert DataGeneralizer.generalize_age(0, bin_size=5) == "0-4"
        assert DataGeneralizer.generalize_age(-1, bin_size=5) == "unknown"
    
    def test_generalize_date(self):
        """Test date generalization to different precisions."""
        test_date = date(2024, 3, 15)
        
        assert DataGeneralizer.generalize_date(test_date, "year") == "2024"
        assert DataGeneralizer.generalize_date(test_date, "month") == "2024-03"
        assert DataGeneralizer.generalize_date(test_date, "quarter") == "2024-Q1"
        
        test_date_q3 = date(2024, 8, 20)
        assert DataGeneralizer.generalize_date(test_date_q3, "quarter") == "2024-Q3"
    
    def test_generalize_zipcode(self):
        """Test zipcode generalization."""
        assert DataGeneralizer.generalize_zipcode("12345", digits=3) == "123**"
        assert DataGeneralizer.generalize_zipcode("98765-4321", digits=3) == "987******"  # 9 chars after removing dash
        assert DataGeneralizer.generalize_zipcode("12", digits=3) == "***"
        assert DataGeneralizer.generalize_zipcode("", digits=3) == "***"
    
    def test_generalize_numeric_range(self):
        """Test numeric value generalization into ranges."""
        ranges = [(0, 50), (50, 100), (100, 150)]
        
        assert DataGeneralizer.generalize_numeric_range(25, ranges) == "0-50"
        assert DataGeneralizer.generalize_numeric_range(75, ranges) == "50-100"
        assert DataGeneralizer.generalize_numeric_range(125, ranges) == "100-150"
        assert DataGeneralizer.generalize_numeric_range(-10, ranges) == "<0"
        assert DataGeneralizer.generalize_numeric_range(200, ranges) == ">=150"
    
    def test_suppress_field(self):
        """Test field suppression."""
        record = {"name": "John Doe", "age": 45, "diagnosis": "diabetes"}
        
        suppressed = DataGeneralizer.suppress_field(record, "name")
        
        assert suppressed["name"] == "***"
        assert suppressed["name_suppressed"] is True
        assert suppressed["age"] == 45  # Other fields unchanged
    
    def test_generalize_record(self):
        """Test applying multiple generalization rules to a record."""
        record = {
            "patient_id": "P001",
            "age": 34,
            "zipcode": "12345",
            "diagnosis_date": "2024-03-15",
            "blood_pressure": 125
        }
        
        rules = {
            "age": {"type": "age_bin", "bin_size": 10},
            "zipcode": {"type": "zipcode", "digits": 3},
            "diagnosis_date": {"type": "date_precision", "precision": "month"},
            "blood_pressure": {
                "type": "numeric_range",
                "ranges": [(0, 120), (120, 140), (140, 180)]
            }
        }
        
        generalized = DataGeneralizer.generalize_record(record, rules)
        
        assert generalized["age"] == "30-39"
        assert generalized["zipcode"] == "123**"
        assert generalized["diagnosis_date"] == "2024-03"
        assert generalized["blood_pressure"] == "120-140"
        assert generalized["patient_id"] == "P001"  # Not in rules, unchanged


class TestNoiseInjector:
    """Test statistical noise injection for differential privacy."""
    
    def test_laplace_noise_generation(self):
        """Test Laplace noise generation."""
        injector = NoiseInjector(epsilon=1.0, seed=42)
        
        # Generate multiple noise samples
        noises = [injector.laplace_noise(sensitivity=1.0) for _ in range(100)]
        
        # Check that noise is generated (not all zeros)
        assert any(n != 0 for n in noises)
        
        # Check that noise has both positive and negative values
        assert any(n > 0 for n in noises)
        assert any(n < 0 for n in noises)
    
    def test_gaussian_noise_generation(self):
        """Test Gaussian noise generation."""
        injector = NoiseInjector(epsilon=1.0, seed=42)
        
        noises = [injector.gaussian_noise(sensitivity=1.0) for _ in range(100)]
        
        assert any(n != 0 for n in noises)
        assert any(n > 0 for n in noises)
        assert any(n < 0 for n in noises)
    
    def test_add_noise_to_numeric(self):
        """Test adding noise to numeric values."""
        injector = NoiseInjector(epsilon=1.0, seed=42)
        
        original_value = 100.0
        noisy_value = injector.add_noise_to_numeric(original_value, noise_type="laplace")
        
        # Value should be different
        assert noisy_value != original_value
        
        # But should be reasonably close (within a few standard deviations)
        assert abs(noisy_value - original_value) < 50
    
    def test_add_noise_to_count(self):
        """Test adding noise to count values."""
        injector = NoiseInjector(epsilon=1.0, seed=42)
        
        original_count = 50
        noisy_count = injector.add_noise_to_count(original_count)
        
        # Should be integer
        assert isinstance(noisy_count, int)
        
        # Should be non-negative
        assert noisy_count >= 0
        
        # Should be different from original (with high probability)
        # Run multiple times to check
        counts = [injector.add_noise_to_count(original_count) for _ in range(10)]
        assert any(c != original_count for c in counts)
    
    def test_add_noise_to_record(self):
        """Test adding noise to numeric fields in a record."""
        injector = NoiseInjector(epsilon=1.0, seed=42)
        
        record = {
            "patient_id": "P001",
            "age": 45,
            "weight": 75.5,
            "height": 175.0,
            "name": "John Doe"
        }
        
        numeric_fields = ["age", "weight", "height"]
        noisy_record = injector.add_noise_to_record(record, numeric_fields)
        
        # Numeric fields should have noise
        assert noisy_record["age"] != record["age"]
        assert noisy_record["weight"] != record["weight"]
        assert noisy_record["height"] != record["height"]
        
        # Noise flags should be set
        assert noisy_record["age_noised"] is True
        assert noisy_record["weight_noised"] is True
        assert noisy_record["height_noised"] is True
        
        # Non-numeric fields should be unchanged
        assert noisy_record["patient_id"] == record["patient_id"]
        assert noisy_record["name"] == record["name"]
    
    def test_epsilon_affects_noise_magnitude(self):
        """Test that epsilon parameter affects noise magnitude."""
        injector_high_privacy = NoiseInjector(epsilon=0.1, seed=42)  # More noise
        injector_low_privacy = NoiseInjector(epsilon=10.0, seed=42)  # Less noise
        
        value = 100.0
        
        # Generate multiple samples
        high_privacy_noises = [
            abs(injector_high_privacy.add_noise_to_numeric(value) - value)
            for _ in range(50)
        ]
        low_privacy_noises = [
            abs(injector_low_privacy.add_noise_to_numeric(value) - value)
            for _ in range(50)
        ]
        
        # Average noise should be higher for lower epsilon
        avg_high_privacy = sum(high_privacy_noises) / len(high_privacy_noises)
        avg_low_privacy = sum(low_privacy_noises) / len(low_privacy_noises)
        
        assert avg_high_privacy > avg_low_privacy


class TestKAnonymityProcessor:
    """Test k-anonymity implementation."""
    
    def test_initialization_requires_k_at_least_5(self):
        """Test that k must be at least 5."""
        with pytest.raises(ValueError, match="k must be at least 5"):
            KAnonymityProcessor(k=3)
        
        # Should work with k >= 5
        processor = KAnonymityProcessor(k=5)
        assert processor.k == 5
    
    def test_calculate_equivalence_classes(self):
        """Test grouping records into equivalence classes."""
        processor = KAnonymityProcessor(k=5)
        
        records = [
            {"age": "20-29", "zipcode": "123**", "gender": "M"},
            {"age": "20-29", "zipcode": "123**", "gender": "M"},
            {"age": "20-29", "zipcode": "123**", "gender": "F"},
            {"age": "30-39", "zipcode": "456**", "gender": "M"},
            {"age": "30-39", "zipcode": "456**", "gender": "M"},
        ]
        
        qi_fields = ["age", "zipcode", "gender"]
        classes = processor.calculate_equivalence_classes(records, qi_fields)
        
        # Should have 3 equivalence classes
        assert len(classes) == 3
        
        # Check class sizes
        assert len(classes[("20-29", "123**", "M")]) == 2
        assert len(classes[("20-29", "123**", "F")]) == 1
        assert len(classes[("30-39", "456**", "M")]) == 2
    
    def test_check_k_anonymity_satisfied(self):
        """Test checking k-anonymity when satisfied."""
        processor = KAnonymityProcessor(k=5)
        
        # Create records that satisfy k=5
        records = []
        for i in range(6):
            records.append({"age": "20-29", "zipcode": "123**"})
        for i in range(5):
            records.append({"age": "30-39", "zipcode": "456**"})
        
        qi_fields = ["age", "zipcode"]
        satisfies, metrics = processor.check_k_anonymity(records, qi_fields)
        
        assert satisfies is True
        assert metrics["satisfies_k_anonymity"] is True
        assert metrics["k_value"] == 5
        assert metrics["smallest_class_size"] == 5
        assert len(metrics["violations"]) == 0
    
    def test_check_k_anonymity_violated(self):
        """Test checking k-anonymity when violated."""
        processor = KAnonymityProcessor(k=5)
        
        records = []
        # Add 6 records in one class (satisfies k=5)
        for i in range(6):
            records.append({"age": "20-29", "zipcode": "123**"})
        # Add 3 records in another class (violates k=5)
        for i in range(3):
            records.append({"age": "30-39", "zipcode": "456**"})
        
        qi_fields = ["age", "zipcode"]
        satisfies, metrics = processor.check_k_anonymity(records, qi_fields)
        
        assert satisfies is False
        assert metrics["satisfies_k_anonymity"] is False
        assert len(metrics["violations"]) > 0
    
    def test_check_k_anonymity_insufficient_records(self):
        """Test k-anonymity check with fewer records than k."""
        processor = KAnonymityProcessor(k=5)
        
        records = [
            {"age": "20-29", "zipcode": "123**"},
            {"age": "30-39", "zipcode": "456**"},
        ]
        
        qi_fields = ["age", "zipcode"]
        satisfies, metrics = processor.check_k_anonymity(records, qi_fields)
        
        assert satisfies is False
        assert "fewer than" in metrics["reason"]
    
    def test_enforce_k_anonymity_suppress_strategy(self):
        """Test enforcing k-anonymity with suppression strategy."""
        processor = KAnonymityProcessor(k=5)
        
        # Create dataset with some classes < k
        records = []
        # Add 6 records with same QI (satisfies k=5)
        for i in range(6):
            records.append({"age": "20-29", "zipcode": "123**", "id": f"P{i}"})
        
        # Add 3 records with different QI (violates k=5)
        for i in range(3):
            records.append({"age": "30-39", "zipcode": "456**", "id": f"P{i+6}"})
        
        qi_fields = ["age", "zipcode"]
        anonymized, metrics = processor.enforce_k_anonymity(
            records, qi_fields, strategy="suppress"
        )
        
        # Should keep the 6 records that satisfy k-anonymity
        assert len(anonymized) == 6
        assert metrics["suppressed_records"] == 3
        assert metrics["original_records"] == 9
    
    def test_enforce_k_anonymity_maintains_k(self):
        """Test that enforced dataset satisfies k-anonymity."""
        processor = KAnonymityProcessor(k=5)
        
        # Create dataset
        records = []
        for i in range(10):
            records.append({"age": "20-29", "zipcode": "123**", "id": f"P{i}"})
        for i in range(2):
            records.append({"age": "30-39", "zipcode": "456**", "id": f"P{i+10}"})
        
        qi_fields = ["age", "zipcode"]
        anonymized, metrics = processor.enforce_k_anonymity(records, qi_fields)
        
        # Check that result satisfies k-anonymity
        satisfies, check_metrics = processor.check_k_anonymity(anonymized, qi_fields)
        assert satisfies is True


class TestAnonymizationEngine:
    """Test complete anonymization engine."""
    
    def test_anonymize_dataset_with_all_techniques(self):
        """Test anonymizing dataset with all techniques combined."""
        engine = AnonymizationEngine(k=5, epsilon=1.0)
        
        # Create sample dataset
        records = []
        for i in range(10):
            records.append({
                "patient_id": f"PATIENT-{i:03d}",
                "ssn": f"123-45-{i:04d}",
                "age": 25 + i,
                "zipcode": "12345",
                "weight": 70.0 + i,
                "diagnosis": "condition_a"
            })
        
        config = {
            "identifier_fields": ["patient_id", "ssn"],
            "quasi_identifier_fields": ["age", "zipcode"],
            "generalization_rules": {
                "age": {"type": "age_bin", "bin_size": 10},
                "zipcode": {"type": "zipcode", "digits": 3}
            },
            "numeric_fields_for_noise": ["weight"],
            "k_anonymity_strategy": "suppress"
        }
        
        anonymized, metrics = engine.anonymize_dataset(records, config)
        
        # Check that techniques were applied
        assert "cryptographic_hashing" in metrics["techniques_applied"]
        assert "data_generalization" in metrics["techniques_applied"]
        assert "k_anonymity" in metrics["techniques_applied"]
        assert "differential_privacy" in metrics["techniques_applied"]
        
        # Check that records were anonymized
        assert len(anonymized) > 0
        
        # Check identifier hashing
        assert anonymized[0]["patient_id"] != records[0]["patient_id"]
        assert anonymized[0]["patient_id_hashed"] is True
        
        # Check generalization
        assert anonymized[0]["age"] in ["20-29", "30-39"]
        assert anonymized[0]["zipcode"] == "123**"
        
        # Check noise addition
        assert anonymized[0]["weight"] != records[0]["weight"]
        assert anonymized[0]["weight_noised"] is True
    
    def test_anonymize_empty_dataset(self):
        """Test anonymizing empty dataset."""
        engine = AnonymizationEngine()
        
        anonymized, metrics = engine.anonymize_dataset([], {})
        
        assert len(anonymized) == 0
        assert "error" in metrics
    
    def test_calculate_privacy_metrics(self):
        """Test calculating privacy metrics."""
        engine = AnonymizationEngine(k=5)
        
        original_records = [
            {"age": "20-29", "zipcode": "123**", "id": i}
            for i in range(10)
        ]
        
        anonymized_records = original_records[:8]  # 2 suppressed
        
        qi_fields = ["age", "zipcode"]
        metrics = engine.calculate_privacy_metrics(
            original_records,
            anonymized_records,
            qi_fields
        )
        
        assert "k_anonymity" in metrics
        assert "data_utility" in metrics
        assert abs(metrics["data_utility"]["retention_rate"] - 0.8) < 0.01
        assert abs(metrics["data_utility"]["suppression_rate"] - 0.2) < 0.01
    
    def test_anonymization_preserves_data_utility(self):
        """Test that anonymization preserves reasonable data utility."""
        engine = AnonymizationEngine(k=5, epsilon=1.0)
        
        # Create larger dataset to ensure k-anonymity can be satisfied
        records = []
        for i in range(50):
            records.append({
                "patient_id": f"P{i}",
                "age": 20 + (i % 5) * 10,  # Ages: 20, 30, 40, 50, 60
                "zipcode": f"1234{i % 2}",  # Two zipcodes
                "diagnosis": f"condition_{i % 3}"
            })
        
        config = {
            "identifier_fields": ["patient_id"],
            "quasi_identifier_fields": ["age", "zipcode"],
            "generalization_rules": {
                "age": {"type": "age_bin", "bin_size": 10},
                "zipcode": {"type": "zipcode", "digits": 4}
            },
            "k_anonymity_strategy": "suppress"
        }
        
        anonymized, metrics = engine.anonymize_dataset(records, config)
        
        # Should retain most records
        retention_rate = metrics["data_retention_rate"]
        assert retention_rate > 0.5  # At least 50% retention
        
        # Anonymized records should still have diagnosis field
        assert all("diagnosis" in record for record in anonymized)


class TestPrivacyMetrics:
    """Test privacy effectiveness metrics."""
    
    def test_k_anonymity_metric_calculation(self):
        """Test that k-anonymity metrics are correctly calculated."""
        processor = KAnonymityProcessor(k=5)
        
        # Create dataset with known equivalence classes
        records = []
        # Class 1: 7 records
        for i in range(7):
            records.append({"age": "20-29", "zip": "123**"})
        # Class 2: 5 records
        for i in range(5):
            records.append({"age": "30-39", "zip": "456**"})
        
        qi_fields = ["age", "zip"]
        satisfies, metrics = processor.check_k_anonymity(records, qi_fields)
        
        assert satisfies is True
        assert metrics["equivalence_classes"] == 2
        assert metrics["smallest_class_size"] == 5
        assert metrics["total_records"] == 12
    
    def test_data_utility_metrics(self):
        """Test data utility metrics calculation."""
        engine = AnonymizationEngine(k=5)
        
        original = [{"id": i} for i in range(100)]
        anonymized = [{"id": i} for i in range(80)]
        
        metrics = engine.calculate_privacy_metrics(original, anonymized, [])
        
        utility = metrics["data_utility"]
        assert utility["original_count"] == 100
        assert utility["anonymized_count"] == 80
        assert abs(utility["retention_rate"] - 0.8) < 0.01
        assert abs(utility["suppression_rate"] - 0.2) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
