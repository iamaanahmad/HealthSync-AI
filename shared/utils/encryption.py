"""
Data encryption utilities for HealthSync system.
Implements AES encryption, key management, and secure data storage.
"""

import os
import base64
import hashlib
import secrets
from typing import Dict, Optional, Tuple, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    key_rotation_days: int = 90
    backup_key_count: int = 3
    min_key_length: int = 32
    use_hardware_security: bool = False

class KeyManager:
    """Manages encryption keys with rotation and backup"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.keys = {}  # key_id -> key_data
        self.key_metadata = {}  # key_id -> metadata
        self.current_key_id = None
        
        # Initialize with master key
        self._initialize_master_key()
    
    def _initialize_master_key(self):
        """Initialize or load master encryption key"""
        key_file = "keys/master.key"
        os.makedirs("keys", exist_ok=True)
        
        if os.path.exists(key_file):
            # Load existing key
            with open(key_file, 'rb') as f:
                key_data = f.read()
            self.master_key = key_data
        else:
            # Generate new master key
            self.master_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.master_key)
            os.chmod(key_file, 0o600)  # Restrict permissions
        
        # Set as current key
        key_id = "master_" + datetime.utcnow().strftime("%Y%m%d")
        self.keys[key_id] = self.master_key
        self.key_metadata[key_id] = {
            'created_at': datetime.utcnow(),
            'key_type': 'master',
            'status': 'active'
        }
        self.current_key_id = key_id
    
    def generate_data_key(self, purpose: str) -> str:
        """Generate new data encryption key"""
        key = Fernet.generate_key()
        key_id = f"{purpose}_{secrets.token_hex(8)}"
        
        self.keys[key_id] = key
        self.key_metadata[key_id] = {
            'created_at': datetime.utcnow(),
            'key_type': 'data',
            'purpose': purpose,
            'status': 'active'
        }
        
        logger.info(f"Generated new data key: {key_id}")
        return key_id
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Get encryption key by ID"""
        return self.keys.get(key_id)
    
    def get_current_key(self) -> Tuple[str, bytes]:
        """Get current active key"""
        return self.current_key_id, self.keys[self.current_key_id]
    
    def rotate_keys(self):
        """Rotate encryption keys"""
        # Mark old keys as deprecated
        for key_id, metadata in self.key_metadata.items():
            if metadata['status'] == 'active':
                age = datetime.utcnow() - metadata['created_at']
                if age.days >= self.config.key_rotation_days:
                    metadata['status'] = 'deprecated'
                    logger.info(f"Deprecated key: {key_id}")
        
        # Generate new master key
        self._initialize_master_key()
    
    def cleanup_old_keys(self):
        """Remove old deprecated keys"""
        to_remove = []
        
        for key_id, metadata in self.key_metadata.items():
            if metadata['status'] == 'deprecated':
                age = datetime.utcnow() - metadata['created_at']
                if age.days > (self.config.key_rotation_days * 2):
                    to_remove.append(key_id)
        
        for key_id in to_remove:
            del self.keys[key_id]
            del self.key_metadata[key_id]
            logger.info(f"Removed old key: {key_id}")

class DataEncryption:
    """Main data encryption service"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.encryption_cache = {}
    
    def encrypt_sensitive_data(self, data: Union[str, Dict], 
                             data_type: str = "general") -> Dict[str, str]:
        """
        Encrypt sensitive data with metadata
        
        Args:
            data: Data to encrypt (string or dict)
            data_type: Type of data for key selection
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        try:
            # Convert data to JSON string if dict
            if isinstance(data, dict):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            # Get or generate key for this data type
            key_id = self._get_key_for_type(data_type)
            key = self.key_manager.get_key(key_id)
            
            if not key:
                raise ValueError(f"Encryption key not found: {key_id}")
            
            # Encrypt data
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data_str.encode())
            
            # Create result with metadata
            result = {
                'encrypted_data': base64.b64encode(encrypted_data).decode(),
                'key_id': key_id,
                'data_type': data_type,
                'encrypted_at': datetime.utcnow().isoformat(),
                'algorithm': 'Fernet-AES256'
            }
            
            logger.debug(f"Encrypted {data_type} data with key {key_id}")
            return result
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_package: Dict[str, str]) -> Union[str, Dict]:
        """
        Decrypt sensitive data from encrypted package
        
        Args:
            encrypted_package: Package with encrypted data and metadata
            
        Returns:
            Decrypted data (original type)
        """
        try:
            # Extract metadata
            key_id = encrypted_package['key_id']
            encrypted_data_b64 = encrypted_package['encrypted_data']
            data_type = encrypted_package.get('data_type', 'general')
            
            # Get decryption key
            key = self.key_manager.get_key(key_id)
            if not key:
                raise ValueError(f"Decryption key not found: {key_id}")
            
            # Decrypt data
            fernet = Fernet(key)
            encrypted_data = base64.b64decode(encrypted_data_b64)
            decrypted_bytes = fernet.decrypt(encrypted_data)
            decrypted_str = decrypted_bytes.decode()
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_patient_data(self, patient_data: Dict[str, any]) -> Dict[str, str]:
        """Encrypt patient-specific data with enhanced security"""
        # Remove or hash PII before encryption
        sanitized_data = self._sanitize_patient_data(patient_data)
        
        return self.encrypt_sensitive_data(sanitized_data, "patient_data")
    
    def encrypt_research_data(self, research_data: Dict[str, any]) -> Dict[str, str]:
        """Encrypt research query data"""
        return self.encrypt_sensitive_data(research_data, "research_data")
    
    def encrypt_consent_data(self, consent_data: Dict[str, any]) -> Dict[str, str]:
        """Encrypt consent preferences"""
        return self.encrypt_sensitive_data(consent_data, "consent_data")
    
    def _get_key_for_type(self, data_type: str) -> str:
        """Get or generate encryption key for specific data type"""
        # Check if we have a key for this type
        for key_id, metadata in self.key_manager.key_metadata.items():
            if (metadata.get('purpose') == data_type and 
                metadata.get('status') == 'active'):
                return key_id
        
        # Generate new key for this type
        return self.key_manager.generate_data_key(data_type)
    
    def _sanitize_patient_data(self, patient_data: Dict[str, any]) -> Dict[str, any]:
        """Sanitize patient data before encryption"""
        sanitized = patient_data.copy()
        
        # Hash direct identifiers
        pii_fields = ['ssn', 'phone', 'email', 'address', 'full_name']
        
        for field in pii_fields:
            if field in sanitized:
                # Replace with hash
                original_value = str(sanitized[field])
                hashed_value = hashlib.sha256(original_value.encode()).hexdigest()
                sanitized[f"{field}_hash"] = hashed_value
                del sanitized[field]
        
        return sanitized

class AsymmetricEncryption:
    """RSA asymmetric encryption for key exchange"""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._generate_key_pair()
    
    def _generate_key_pair(self):
        """Generate RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_with_public_key(self, data: bytes, public_key_pem: str) -> bytes:
        """Encrypt data with public key"""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted
    
    def decrypt_with_private_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with private key"""
        decrypted = self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()

class SecureStorage:
    """Secure storage with encryption at rest"""
    
    def __init__(self, encryption_service: DataEncryption):
        self.encryption = encryption_service
        self.storage_path = "secure_storage"
        os.makedirs(self.storage_path, exist_ok=True)
    
    def store_encrypted(self, key: str, data: Dict[str, any], 
                       data_type: str = "general") -> str:
        """Store data with encryption"""
        try:
            # Encrypt the data
            encrypted_package = self.encryption.encrypt_sensitive_data(data, data_type)
            
            # Add storage metadata
            storage_record = {
                'storage_key': key,
                'stored_at': datetime.utcnow().isoformat(),
                'data_type': data_type,
                'encrypted_package': encrypted_package
            }
            
            # Store to file
            file_path = os.path.join(self.storage_path, f"{key}.enc")
            with open(file_path, 'w') as f:
                json.dump(storage_record, f)
            
            # Restrict file permissions
            os.chmod(file_path, 0o600)
            
            logger.info(f"Stored encrypted data: {key}")
            return file_path
            
        except Exception as e:
            logger.error(f"Secure storage failed: {str(e)}")
            raise
    
    def retrieve_encrypted(self, key: str) -> Optional[Dict[str, any]]:
        """Retrieve and decrypt stored data"""
        try:
            file_path = os.path.join(self.storage_path, f"{key}.enc")
            
            if not os.path.exists(file_path):
                return None
            
            # Load storage record
            with open(file_path, 'r') as f:
                storage_record = json.load(f)
            
            # Decrypt the data
            encrypted_package = storage_record['encrypted_package']
            decrypted_data = self.encryption.decrypt_sensitive_data(encrypted_package)
            
            logger.debug(f"Retrieved encrypted data: {key}")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Secure retrieval failed: {str(e)}")
            return None
    
    def delete_encrypted(self, key: str) -> bool:
        """Securely delete stored data"""
        try:
            file_path = os.path.join(self.storage_path, f"{key}.enc")
            
            if os.path.exists(file_path):
                # Overwrite file before deletion (basic secure delete)
                file_size = os.path.getsize(file_path)
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(file_size))
                
                os.remove(file_path)
                logger.info(f"Securely deleted: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Secure deletion failed: {str(e)}")
            return False

# Initialize encryption services
encryption_config = EncryptionConfig()
key_manager = KeyManager(encryption_config)
data_encryption = DataEncryption(key_manager)
asymmetric_encryption = AsymmetricEncryption()
secure_storage = SecureStorage(data_encryption)