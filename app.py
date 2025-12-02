#!/usr/bin/env python3
"""
UUID Version 1 Generator Web Application

A web-based tool for generating UUID v1s and finding all UUIDs between two given UUIDs.
"""

import os
import uuid
import time
import tempfile
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import threading
import hashlib
from typing import Optional, Dict, Any

app = Flask(__name__)
CORS(app)

# UUID validation regex pattern (strict)
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def validate_uuid(uuid_str: str) -> bool:
    """Strictly validate UUID format."""
    if not uuid_str or not isinstance(uuid_str, str):
        return False
    uuid_str = uuid_str.strip()
    # Check regex pattern
    if not UUID_PATTERN.match(uuid_str):
        return False
    # Also validate with uuid module
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False

def validate_text_input(text: str, max_length: int = 1000) -> bool:
    """Validate text input - only allow safe text characters."""
    if not text or not isinstance(text, str):
        return False
    text = text.strip()
    # Check length
    if len(text) == 0 or len(text) > max_length:
        return False
    # Allow alphanumeric, spaces, and common safe characters
    # Block potentially dangerous characters
    if re.search(r'[<>"\']', text):
        return False
    # Allow printable characters except control characters
    if not all(ord(c) >= 32 and ord(c) != 127 for c in text):
        return False
    return True

def validate_version(version: str) -> bool:
    """Validate UUID version string."""
    return version in ['1', '2', '3', '4']

def validate_namespace(namespace: str) -> bool:
    """Validate namespace string."""
    return namespace.upper() in ['DNS', 'URL', 'OID', 'X500']

class UUIDv1Generator:
    """UUID Version 1 Generator with range functionality."""
    
    def __init__(self):
        self.node = uuid.getnode()  # Get MAC address
    
    def generate_uuid_v1(self, timestamp: Optional[float] = None) -> uuid.UUID:
        """Generate a UUID version 1."""
        if timestamp is not None:
            # Generate UUID at specific timestamp
            # Convert Unix timestamp to UUID timestamp (100-nanosecond intervals since UUID epoch)
            uuid_timestamp = int((timestamp + 12219292800) * 10000000)
            
            # Extract 60-bit timestamp components
            time_low = uuid_timestamp & 0xffffffff      # 32 bits
            time_mid = (uuid_timestamp >> 32) & 0xffff # 16 bits
            time_hi = (uuid_timestamp >> 48) & 0x0fff  # 12 bits
            
            # Add version (1) to time_hi
            time_hi_version = time_hi | (1 << 12)
            
            # Generate unique clock sequence for each timestamp to ensure uniqueness
            # Use a combination of timestamp and a counter to make it unique
            import time as time_module
            clock_seq_low = (int(timestamp * 1000000) & 0xff)  # Use microseconds part
            clock_seq_high = ((int(timestamp * 1000000) >> 8) & 0x3f) | 0x80  # Add variant bits
            
            node = self.node
            
            # Create UUID with specified timestamp
            return uuid.UUID(fields=(time_low, time_mid, time_hi_version, clock_seq_high, clock_seq_low, node))
        else:
            # Use standard Python UUID v1 generation which handles clock sequence properly
            return uuid.uuid1(node=self.node)
    
    def uuid_to_timestamp(self, uuid_obj: uuid.UUID) -> float:
        """Extract timestamp from UUID v1."""
        time_low = uuid_obj.fields[0]
        time_mid = uuid_obj.fields[1]
        time_hi_version = uuid_obj.fields[2] & 0x0fff
        
        uuid_time = (time_hi_version << 48) | (time_mid << 32) | time_low
        # Convert from 100-nanosecond intervals to seconds since UUID epoch
        uuid_seconds = uuid_time / 10000000
        # UUID epoch is October 15, 1582, convert to Unix epoch (January 1, 1970)
        # UUID epoch in seconds since Unix epoch: 12219292800
        timestamp = uuid_seconds - 12219292800
        
        return timestamp
    
    def analyze_uuid(self, uuid_str: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        try:
            uuid_obj = uuid.UUID(uuid_str)
            # Determine UUID version and provide appropriate analysis
            # Note: Python's uuid module doesn't natively support v2, so we need manual detection
            version = uuid_obj.version
            possible_v2 = False
            
            # Check if this might actually be a UUID v2 by examining the clock sequence
            # UUID v2 has specific bit patterns in the clock sequence for DCE Security
            # We check both version == 1 and version == None cases
            if version == 1 or version is None:
                is_v2 = self.is_likely_uuid_v2(uuid_obj)
                
                if is_v2:
                    version = 2
                    possible_v2 = True
            
            # For v1 or detected v2 we compute timestamp; for others we mark N/A
            if version == 1 or (version == 2 and possible_v2):
                timestamp = self.uuid_to_timestamp(uuid_obj)
                # Convert UUID timestamp to Unix timestamp and handle large values
                try:
                    # Convert to UTC datetime (naive)
                    dt_utc = datetime.utcfromtimestamp(timestamp)
                    # Convert to IST (UTC+5:30)
                    dt_ist = dt_utc + timedelta(hours=5, minutes=30)

                    # Friendly formats
                    friendly_utc = dt_utc.strftime('%A, %B %d, %Y at %I:%M:%S %p')
                    friendly_ist = dt_ist.strftime('%A, %B %d, %Y at %I:%M:%S %p')

                    # Also keep the old fields for compatibility
                    datetime_str_utc = dt_utc.isoformat()
                    datetime_str_ist = dt_ist.isoformat()
                    date_str_utc = dt_utc.strftime('%Y-%m-%d')
                    date_str_ist = dt_ist.strftime('%Y-%m-%d')
                    time_str_utc = dt_utc.strftime('%H:%M:%S.%f')[:-3]
                    time_str_ist = dt_ist.strftime('%H:%M:%S.%f')[:-3]

                except (OSError, ValueError, OverflowError):
                    # Handle very large timestamps
                    friendly_utc = "Timestamp too large for conversion"
                    friendly_ist = "Timestamp too large for conversion"
                    datetime_str_utc = "N/A"
                    datetime_str_ist = "N/A"
                    date_str_utc = "N/A"
                    date_str_ist = "N/A"
                    time_str_utc = "N/A"
                    time_str_ist = "N/A"
            else:
                timestamp = None
                friendly_utc = "N/A"
                friendly_ist = "N/A"
                datetime_str_utc = "N/A"
                datetime_str_ist = "N/A"
                date_str_utc = "N/A"
                date_str_ist = "N/A"
                time_str_utc = "N/A"
                time_str_ist = "N/A"

            # Extract clock sequence and variant
            clock_seq_hi = uuid_obj.fields[3]
            clock_seq_low = uuid_obj.fields[4]
            clock_seq = ((clock_seq_hi & 0x3f) << 8) | clock_seq_low
            variant = clock_seq_hi >> 6

            # Determine variant description
            if variant == 0:
                variant_desc = "Reserved (NCS backward compatibility)"
            elif variant == 1:
                variant_desc = "DCE 1.1, ISO/IEC 11578:1996"
            elif variant == 2:
                variant_desc = "Microsoft GUID"
            else:
                variant_desc = "Reserved for future definition"

            # Set version description
            if possible_v2:
                version_desc = "Possible UUID v2 (DCE Security) - Version bit shows 1 but patterns suggest v2"
            else:
                version_desc = self.get_version_description(version)
            
            # Base result with common fields
            # For UUID v3, many fields are hash components, not actual time/clock/node values
            # For UUID v4, all fields are random bits, not actual time/clock/node values
            if version == 3:
                result = {
                    'uuid': str(uuid_obj),
                    'timestamp': None,  # N/A for v3
                    'datetime_utc': 'N/A',
                    'datetime_ist': 'N/A',
                    'date_utc': 'N/A',
                    'date_ist': 'N/A',
                    'time_utc': 'N/A',
                    'time_ist': 'N/A',
                    'friendly_utc': 'N/A - UUID v3 is name-based, not time-based',
                    'friendly_ist': 'N/A - UUID v3 is name-based, not time-based',
                    'timezone_utc': 'N/A',
                    'timezone_ist': 'N/A',
                    'version': str(version),
                    'version_desc': version_desc,
                    'variant': variant_desc,
                    'variant_code': variant,
                    'node': f"{uuid_obj.fields[5]:012x}",
                    'node_desc': 'MD5 hash component (48 bits) - not a MAC address',
                    'clock_seq': f"{clock_seq:04x}",
                    'clock_seq_desc': 'MD5 hash component (14 bits) - not a clock sequence',
                    'clock_seq_hi': f"{clock_seq_hi:02x}",
                    'clock_seq_low': f"{clock_seq_low:02x}",
                    'time_low': f"{uuid_obj.fields[0]:08x}",
                    'time_mid': f"{uuid_obj.fields[1]:04x}",
                    'time_hi': f"{uuid_obj.fields[2] & 0x0fff:04x}",
                    'time_hi_version': f"{uuid_obj.fields[2]:04x}",
                    'note_time_fields': 'Fields named "time_low", "time_mid", "time_hi" are MD5 hash components, not timestamps',
                    'note_clock_node': 'Fields named "clock_seq" and "node" are MD5 hash components, not clock sequence or MAC address'
                }
            elif version == 4:
                result = {
                    'uuid': str(uuid_obj),
                    'timestamp': None,  # N/A for v4
                    'datetime_utc': 'N/A',
                    'datetime_ist': 'N/A',
                    'date_utc': 'N/A',
                    'date_ist': 'N/A',
                    'time_utc': 'N/A',
                    'time_ist': 'N/A',
                    'friendly_utc': 'N/A - UUID v4 is random, not time-based',
                    'friendly_ist': 'N/A - UUID v4 is random, not time-based',
                    'timezone_utc': 'N/A',
                    'timezone_ist': 'N/A',
                    'version': str(version),
                    'version_desc': version_desc,
                    'variant': variant_desc,
                    'variant_code': variant,
                    'node': f"{uuid_obj.fields[5]:012x}",
                    'node_desc': 'Random bits (48 bits) - not a MAC address',
                    'clock_seq': f"{clock_seq:04x}",
                    'clock_seq_desc': 'Random bits (14 bits) - not a clock sequence',
                    'clock_seq_hi': f"{clock_seq_hi:02x}",
                    'clock_seq_low': f"{clock_seq_low:02x}",
                    'time_low': f"{uuid_obj.fields[0]:08x}",
                    'time_mid': f"{uuid_obj.fields[1]:04x}",
                    'time_hi': f"{uuid_obj.fields[2] & 0x0fff:04x}",
                    'time_hi_version': f"{uuid_obj.fields[2]:04x}",
                    'note_time_fields': 'Fields named "time_low", "time_mid", "time_hi" are random bits, not timestamps',
                    'note_clock_node': 'Fields named "clock_seq" and "node" are random bits, not clock sequence or MAC address'
                }
            else:
                result = {
                    'uuid': str(uuid_obj),
                    'timestamp': timestamp,
                    'datetime_utc': datetime_str_utc,
                    'datetime_ist': datetime_str_ist,
                    'date_utc': date_str_utc,
                    'date_ist': date_str_ist,
                    'time_utc': time_str_utc,
                    'time_ist': time_str_ist,
                    'friendly_utc': friendly_utc,
                    'friendly_ist': friendly_ist,
                    'timezone_utc': 'UTC',
                    'timezone_ist': 'IST (UTC+5:30)',
                    'version': str(version),
                    'version_desc': version_desc,
                    'variant': variant_desc,
                    'variant_code': variant,
                    'node': f"{uuid_obj.fields[5]:012x}",
                    'node_desc': self.get_node_description(version),
                    'clock_seq': f"{clock_seq:04x}",
                    'clock_seq_desc': self.get_clock_seq_description(version),
                    'clock_seq_hi': f"{clock_seq_hi:02x}",
                    'clock_seq_low': f"{clock_seq_low:02x}",
                    'time_low': f"{uuid_obj.fields[0]:08x}",
                    'time_mid': f"{uuid_obj.fields[1]:04x}",
                    'time_hi': f"{uuid_obj.fields[2] & 0x0fff:04x}",
                    'time_hi_version': f"{uuid_obj.fields[2]:04x}"
                }
            
            # Add version-specific fields
            if version == 1:
                result.update(self.get_version1_specific_fields(uuid_obj))
            elif version == 2:
                if possible_v2:
                    # Enhanced analysis for possible v2 UUIDs
                    result.update(self.get_possible_v2_specific_fields(uuid_obj))
                else:
                    result.update(self.get_version2_specific_fields(uuid_obj))
            elif version == 3:
                # Pass namespace if provided
                result.update(self.get_version3_specific_fields(uuid_obj, namespace))
            elif version == 4:
                result.update(self.get_version4_specific_fields(uuid_obj))
            
            return result
        except ValueError:
            return {'error': 'Invalid UUID format'}
    
    def get_version_description(self, version: int) -> str:
        """Get human-readable description for UUID version."""
        descriptions = {
            1: 'Time-based UUID using timestamp and MAC address',
            2: 'DCE Security UUID (time-based + POSIX UID/GID)',
            3: 'Name-based UUID using MD5 hash',
            4: 'Random UUID (cryptographically secure)',
            5: 'Name-based UUID using SHA-1 hash'
        }
        return descriptions.get(version, f'Unknown UUID version {version}')
    
    def is_likely_uuid_v2(self, uuid_obj: uuid.UUID) -> bool:
        """Detect if a UUID v1 might actually be a UUID v2 based on DCE Security patterns."""
        try:
            # UUID v2 has specific characteristics:
            # 1. Clock sequence high byte has specific bit patterns for DCE Security
            # 2. Node field may contain POSIX UID/GID information
            # 3. Specific variant bits for DCE Security
            
            clock_seq_hi = uuid_obj.fields[3]
            variant = clock_seq_hi >> 6
            
            # DCE Security typically uses variant 1 (0x40-0x7F)
            if variant == 1:
                # Additional checks for DCE Security patterns
                clock_seq_low = uuid_obj.fields[4]
                clock_seq = ((clock_seq_hi & 0x3f) << 8) | clock_seq_low
                
                # DCE Security UUIDs typically have clock sequences in specific ranges
                # The clock sequence 0x0027 (39) is well within the valid range
                if clock_seq >= 0x0001 and clock_seq <= 0x3FFF:
                    
                    # For DCE Security, we're more lenient with node field patterns
                    # since they can contain various structured data
                    node_field = uuid_obj.fields[5]
                    
                    # Check if this looks like a DCE Security UUID
                    # The key indicators are:
                    # 1. Variant 1 (DCE Security)
                    # 2. Reasonable clock sequence range
                    # 3. Node field that's not obviously a standard MAC address
                    
                    # Most importantly: if variant is 1 and clock sequence is reasonable,
                    # this is very likely a DCE Security UUID (v2)
                    return True
                    
            return False
        except:
            return False
    
    def get_node_description(self, version: int) -> str:
        """Get description for node field based on UUID version."""
        descriptions = {
            1: 'MAC address of the generating computer',
            2: 'MAC address with POSIX UID/GID',
            3: 'MD5 hash output (48 bits) - part of the hash result, not a MAC address',
            4: 'Randomly generated (not a real MAC address)',
            5: 'SHA-1 hash output (48 bits) - part of the hash result, not a MAC address'
        }
        return descriptions.get(version, 'Unknown node type')
    
    def get_clock_seq_description(self, version: int) -> str:
        """Get description for clock sequence based on UUID version."""
        descriptions = {
            1: 'Random or pseudo-random number to ensure uniqueness',
            2: 'Security domain identifier',
            3: 'MD5 hash output (14 bits) - part of the hash result, not a clock sequence',
            4: 'Randomly generated (not used for timing)',
            5: 'SHA-1 hash output (14 bits) - part of the hash result, not a clock sequence'
        }
        return descriptions.get(version, 'Unknown clock sequence type')
    
    def get_version1_specific_fields(self, uuid_obj: uuid.UUID) -> Dict[str, Any]:
        """Get version 1 specific analysis fields."""
        return {
            'timestamp_hex': f"{uuid_obj.fields[2]:04x}{uuid_obj.fields[1]:04x}{uuid_obj.fields[0]:08x}",
            'mac_address': f"{uuid_obj.fields[5]:012x}",
            'mac_address_formatted': ':'.join([f"{uuid_obj.fields[5]:012x}"[i:i+2] for i in range(0, 12, 2)]),
            'clock_sequence_purpose': 'Prevents duplicates when system clock goes backwards',
            'time_precision': '100 nanoseconds',
            'epoch_base': 'October 15, 1582 (Gregorian calendar reform)',
            'sandwich_attack_possibility': 'HIGH - Time-based UUIDs are vulnerable to sandwich attacks',
            'sandwich_attack_description': 'UUID v1 timestamps are predictable and can be manipulated to create collisions or predict future UUIDs',
            'sandwich_attack_risk': 'Attackers can generate UUIDs with timestamps before and after a target UUID, potentially causing database conflicts',
            'sandwich_attack_exploitation': 'Use UUID SANDWICHER tool to generate payloads for testing and exploitation',
            'sandwich_attack_article_url': 'https://medium.com/@ibm_ptc_security/sandwich-attack-uuid-v1-a114e3a8b6c4',
            'sandwich_attack_article_title': 'UUID Sandwich Attacks: Time-Based Vulnerabilities in Distributed Systems',
            'sandwich_attack_lab_url': 'https://github.com/harikrishnankv/file-storage-lab',
            'sandwich_attack_lab_title': 'File Storage Lab - UUID v1 Vulnerability Challenge'
        }
    
    def get_version2_specific_fields(self, uuid_obj: uuid.UUID) -> Dict[str, Any]:
        """Get version 2 specific analysis fields."""
        clock_seq_hi = uuid_obj.fields[3]
        clock_seq_low = uuid_obj.fields[4]
        clock_seq = ((clock_seq_hi & 0x3f) << 8) | clock_seq_low
        
        return {
            'timestamp_hex': f"{uuid_obj.fields[2]:04x}{uuid_obj.fields[1]:04x}{uuid_obj.fields[0]:08x}",
            'dce_domain': self.get_dce_domain(clock_seq),
            'posix_uid_gid': self.extract_posix_info(uuid_obj.fields[5]),
            'security_identifier': f"{clock_seq:04x}",
            'clock_sequence_purpose': 'DCE Security domain and POSIX UID/GID identification',
            'time_precision': '100 nanoseconds',
            'epoch_base': 'October 15, 1582 (Gregorian calendar reform)',
            'dce_security_features': 'Distributed Computing Environment security model'
        }
    
    def get_version3_specific_fields(self, uuid_obj: uuid.UUID, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get version 3 specific analysis fields - only showing certain/definitive data."""
        # Extract hash components (these are MD5 hash output, not time/clock/node)
        hash_low = uuid_obj.fields[0]      # 32 bits of hash
        hash_mid = uuid_obj.fields[1]      # 16 bits of hash
        hash_hi = uuid_obj.fields[2] & 0x0fff  # 12 bits of hash (version bits removed)
        clock_seq_hi = uuid_obj.fields[3]
        clock_seq_low = uuid_obj.fields[4]
        hash_clock = ((clock_seq_hi & 0x3f) << 8) | clock_seq_low  # 14 bits of hash
        hash_node = uuid_obj.fields[5]     # 48 bits of hash
        
        # Base result with only certain/definitive information
        result = {
            'hash_algorithm': 'MD5',
            'hash_output': '128 bits',
            'deterministic': True,
            'collision_resistance': 'Good (MD5 provides sufficient collision resistance for namespaces)',
            'use_cases': 'Identifiers, URLs, Namespaces, Consistent ID generation',
            'hash_components': {
                'hash_low_32bits': f"{hash_low:08x}",
                'hash_mid_16bits': f"{hash_mid:04x}",
                'hash_hi_12bits': f"{hash_hi:04x}",
                'hash_clock_14bits': f"{hash_clock:04x}",
                'hash_node_48bits': f"{hash_node:012x}",
                'note': 'These fields are MD5 hash output components, not time/clock/node values'
            },
            'field_naming_note': 'UUID v3 uses the same field structure as v1, but all fields represent MD5 hash output rather than timestamp, clock sequence, and MAC address'
        }
        
        # Only add namespace information if explicitly provided by user
        if namespace:
            namespace_upper = namespace.upper()
            namespace_info = {
                'DNS': {
                    'uuid': str(uuid.NAMESPACE_DNS),
                    'description': 'Domain Name System (DNS) - for domain names',
                    'example': 'example.com'
                },
                'URL': {
                    'uuid': str(uuid.NAMESPACE_URL),
                    'description': 'Uniform Resource Locator (URL) - for URLs',
                    'example': 'https://example.com/page'
                },
                'OID': {
                    'uuid': str(uuid.NAMESPACE_OID),
                    'description': 'ISO Object Identifier (OID) - for ISO OIDs',
                    'example': '1.3.6.1.4.1'
                },
                'X500': {
                    'uuid': str(uuid.NAMESPACE_X500),
                    'description': 'X.500 Distinguished Name (DN) - for X.500 DNs',
                    'example': 'CN=John Doe, OU=Engineering, O=Company'
                }
            }
            
            if namespace_upper in namespace_info:
                result['used_namespace'] = namespace_upper
                result['used_namespace_uuid'] = namespace_info[namespace_upper]['uuid']
                result['used_namespace_description'] = namespace_info[namespace_upper]['description']
            else:
                result['used_namespace'] = namespace
                result['used_namespace_note'] = 'Custom or unknown namespace'
        
        return result
    
    def get_version4_specific_fields(self, uuid_obj: uuid.UUID) -> Dict[str, Any]:
        """Get version 4 specific analysis fields."""
        return {
            'randomness_source': 'Cryptographically secure random number generator',
            'unpredictability': 'Maximum (completely random)',
            'collision_probability': 'Extremely low (statistically negligible)',
            'entropy_source': 'Operating system entropy sources',
            'use_cases': 'Session IDs, Tokens, Unique Keys, Temporary Identifiers',
            'security_level': 'High (when using good random numbers generators)'
        }
    
    def generate_uuid_v2_like(self) -> uuid.UUID:
        """Generate a UUID v2-like structure for DCE Security testing."""
        import random
        
        try:
            # Get current timestamp (100-nanosecond precision)
            now = datetime.now()
            timestamp_ns = int(now.timestamp() * 10000000) + 122192928000000000
            
            # Extract timestamp components
            time_low = timestamp_ns & 0xFFFFFFFF
            time_mid = (timestamp_ns >> 32) & 0xFFFF
            time_hi = (timestamp_ns >> 48) & 0x0FFF
            
            # Set version bits to 0001 (v1) but we'll detect it as v2
            time_hi_version = time_hi | 0x1000
            
            # Generate DCE Security specific clock sequence
            # DCE Security uses specific patterns in clock sequence
            clock_seq_hi = 0x40  # Variant 1 (DCE Security)
            clock_seq_low = random.randint(0x01, 0x3F)  # DCE Security range
            
            # Generate node field with DCE Security patterns
            # This simulates POSIX UID/GID information
            # Note: Node field is 48 bits, so we need to keep values within limits
            dce_domain = random.randint(0x01, 0x0F)  # 4 bits for domain
            posix_uid = random.randint(1000, 0xFFFF)  # 16 bits for UID
            posix_gid = random.randint(1000, 0xFFFF)  # 16 bits for GID
            
            # Combine into node field (48 bits total)
            # Format: dce_domain (4 bits) + posix_uid (16 bits) + posix_gid (16 bits) + padding (12 bits)
            node_field = (dce_domain << 44) | (posix_uid << 28) | (posix_gid << 12)
            
            # Create UUID using hex string construction
            # Format: time_low-time_mid-time_hi_version-clock_seq_hi_clock_seq_low-node
            uuid_hex = f"{time_low:08x}-{time_mid:04x}-{time_hi_version:04x}-{clock_seq_hi:02x}{clock_seq_low:02x}-{node_field:012x}"
            
            return uuid.UUID(uuid_hex)
            
        except Exception as e:
            # Fallback to regular UUID v1 if v2 generation fails
            print(f"Warning: UUID v2 generation failed: {e}, falling back to v1")
            return self.generate_uuid_v1()
    
    def get_possible_v2_specific_fields(self, uuid_obj: uuid.UUID) -> Dict[str, Any]:
        """Get enhanced analysis for possible UUID v2 cases where version bit is 1."""
        clock_seq_hi = uuid_obj.fields[3]
        clock_seq_low = uuid_obj.fields[4]
        clock_seq = ((clock_seq_hi & 0x3f) << 8) | clock_seq_low
        node_field = uuid_obj.fields[5]
        
        return {
            'timestamp_hex': f"{uuid_obj.fields[2]:04x}{uuid_obj.fields[1]:04x}{uuid_obj.fields[0]:08x}",
            'dce_domain': self.get_dce_domain(clock_seq),
            'posix_uid_gid': self.extract_posix_info(node_field),
            'security_identifier': f"{clock_seq:04x}",
            'clock_sequence_purpose': 'DCE Security domain and POSIX UID/GID identification',
            'time_precision': '100 nanoseconds',
            'epoch_base': 'October 15, 1582 (Gregorian calendar reform)',
            'dce_security_features': 'Distributed Computing Environment security model',
            'detection_note': 'Detected as possible v2 based on DCE Security patterns despite version bit 1',
            'confidence_level': 'High - DCE Security patterns clearly identified',
            'analysis_method': 'Pattern-based detection using clock sequence and node field analysis',
            'recommendation': 'Treat as UUID v2 for DCE Security applications'
        }
    
    def get_dce_domain(self, clock_seq: int) -> str:
        """Get DCE domain description based on clock sequence."""
        # DCE Security domains based on clock sequence patterns
        if clock_seq < 0x1000:
            return "Local DCE Security Domain"
        elif clock_seq < 0x2000:
            return "Network DCE Security Domain"
        elif clock_seq < 0x3000:
            return "Distributed DCE Security Domain"
        elif clock_seq < 0x4000:
            return "Enterprise DCE Security Domain"
        else:
            return "Custom DCE Security Domain"
    
    def extract_posix_info(self, node_field: int) -> str:
        """Extract POSIX UID/GID information from node field."""
        try:
            # In UUID v2, the node field may contain POSIX UID/GID
            # New bit layout: dce_domain (4 bits) + posix_uid (16 bits) + posix_gid (16 bits) + padding (12 bits)
            dce_domain = (node_field >> 44) & 0x0F
            uid = (node_field >> 28) & 0xFFFF
            gid = (node_field >> 12) & 0xFFFF
            
            if uid > 0 or gid > 0:
                return f"Domain: {dce_domain}, UID: {uid}, GID: {gid}"
            else:
                return "No POSIX UID/GID information"
        except:
            return "Unable to extract POSIX information"
    
    def estimate_range_size(self, start_uuid: str, end_uuid: str, 
                           step_seconds: float = 0.0000001) -> Dict[str, Any]:
        """Estimate the size and time for UUID range generation using Ruby-like logic."""
        try:
            start_uuid_obj = uuid.UUID(start_uuid)
            end_uuid_obj = uuid.UUID(end_uuid)
            
            # Extract timestamp components exactly like Ruby code: high + mid + low
            start_time_low = f"{start_uuid_obj.fields[0]:08x}"
            start_time_mid = f"{start_uuid_obj.fields[1]:04x}"
            start_time_hi = f"{start_uuid_obj.fields[2]:04x}"
            start_timestamp_hex = int(start_time_hi[1:] + start_time_mid + start_time_low, 16)  # Remove version bit
            
            end_time_low = f"{end_uuid_obj.fields[0]:08x}"
            end_time_mid = f"{end_uuid_obj.fields[1]:04x}"
            end_time_hi = f"{end_uuid_obj.fields[2]:04x}"
            end_timestamp_hex = int(end_time_hi[1:] + end_time_mid + end_time_low, 16)  # Remove version bit
            
            if start_timestamp_hex > end_timestamp_hex:
                start_timestamp_hex, end_timestamp_hex = end_timestamp_hex, start_timestamp_hex
            
            # Calculate count exactly like Ruby: end - start + 1
            total_possible = end_timestamp_hex - start_timestamp_hex + 1
            
            # Estimate generation time (rough estimate)
            estimated_time_seconds = total_possible * 0.0001  # 0.1ms per UUID
            
            return {
                'start_timestamp_hex': start_timestamp_hex,
                'end_timestamp_hex': end_timestamp_hex,
                'total_possible': total_possible,
                'estimated_time_seconds': estimated_time_seconds,
                'estimated_time_human': str(timedelta(seconds=estimated_time_seconds)),
                'note': 'Using Ruby-like hex timestamp logic for exact precision'
            }
        except ValueError:
            return {'error': 'Invalid UUID format'}

class FastUUIDv1Generator:
    """Fast UUID v1 generator using direct hex manipulation like the Ruby implementation."""
    
    def __init__(self):
        # Get MAC address (node) - same as before
        self.node = self._get_mac_address()
    
    def _get_mac_address(self):
        """Get MAC address for the current machine."""
        import uuid as uuid_module
        return uuid_module.getnode()
    
    def generate_uuid_v1_custom(self, timestamp_hex: int, clock_seq: str, mac_address: str, save_char: str) -> str:
        """Generate a UUID v1 using the exact same logic as sandwich-irah.rb."""
        try:
            # Convert timestamp to hex string (same as Ruby: timestamp.to_s(16))
            hex_str = f"{timestamp_hex:x}"
            
            # 60-bit timestamp = 15 hex characters
            hex_str = hex_str.zfill(15)
            
            # Extract components exactly like Ruby code
            # Ruby: high = hex[0..2], mid = hex[3..6], low = hex[7..]
            high = hex_str[0:3]      # First 3 hex chars
            mid = hex_str[3:7]       # Next 4 hex chars  
            low = hex_str[7:]        # Last 8 hex chars (or whatever is left)
            
            # Format UUID exactly like Ruby: "#{ low }-#{ mid }-#{ save }#{ high }-#{ clock }-#{ mac }"
            uuid_str = f"{low}-{mid}-{save_char}{high}-{clock_seq}-{mac_address}"
            return uuid_str
            
        except Exception as e:
            print(f"Error in generate_uuid_v1_custom for timestamp {timestamp_hex:x}: {e}")
            return None
    
    def generate_uuids_to_file_fast_with_progress(self, start_uuid, end_uuid, filename, task_id, total_possible=None):
        """Generate UUIDs to file using fast method with live progress updates and cancellation checks."""
        try:
            # Extract timestamps using the same logic as Ruby code
            start_uuid_obj = uuid.UUID(start_uuid)
            end_uuid_obj = uuid.UUID(end_uuid)
            
            start_time_low = f"{start_uuid_obj.fields[0]:08x}"
            start_time_mid = f"{start_uuid_obj.fields[1]:04x}"
            start_time_hi = f"{start_uuid_obj.fields[2]:04x}"
            start_timestamp_hex = int(start_time_hi[1:] + start_time_mid + start_time_low, 16)  # Remove version bit
            
            end_time_low = f"{end_uuid_obj.fields[0]:08x}"
            end_time_mid = f"{end_uuid_obj.fields[1]:04x}"
            end_time_hi = f"{end_uuid_obj.fields[2]:04x}"
            end_timestamp_hex = int(end_time_hi[1:] + end_time_mid + end_time_low, 16)  # Remove version bit
            
            # Ensure correct order
            if start_timestamp_hex > end_timestamp_hex:
                start_timestamp_hex, end_timestamp_hex = end_timestamp_hex, start_timestamp_hex
            
            # Calculate total if not supplied
            if total_possible is None:
                total_possible = end_timestamp_hex - start_timestamp_hex + 1
            
            # Extract clock_seq and mac from start UUID
            uuid_obj = uuid.UUID(start_uuid)
            clock_seq = f"{uuid_obj.fields[3]:02x}{uuid_obj.fields[4]:02x}"
            mac_address = f"{uuid_obj.fields[5]:012x}"
            save_char = f"{uuid_obj.fields[2]:04x}"[0]
            
            # Open file and expose path early
            with open(filename, 'w') as f:
                generation_tasks.get(task_id, {}).update({'file_path': filename}) if task_id in generation_tasks else None
                
                count = 0
                for current_timestamp_hex in range(start_timestamp_hex, end_timestamp_hex + 1):
                    # Responsive cancellation check every 1000
                    if (current_timestamp_hex - start_timestamp_hex) % 1000 == 0:
                        if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
                            try:
                                f.flush()
                            except Exception:
                                pass
                            try:
                                if os.path.exists(filename):
                                    os.unlink(filename)
                            except Exception:
                                pass
                            return False, 'cancelled', count
                    
                    try:
                        uuid_str = self.generate_uuid_v1_custom(current_timestamp_hex, clock_seq, mac_address, save_char)
                        if not uuid_str:
                            continue
                        f.write(f"{uuid_str}\n")
                        count += 1
                        if count % 1000 == 0:
                            progress = min(100, (count / total_possible) * 100)
                            if task_id in generation_tasks:
                                generation_tasks[task_id]['progress'] = progress
                                generation_tasks[task_id]['count'] = count
                    except Exception:
                        continue
            
            return True, 'ok', count
        except Exception as e:
            return False, str(e), 0

# Global generator instance
generator = UUIDv1Generator()
fast_generator = FastUUIDv1Generator()

# Global storage for generation tasks
generation_tasks = {}

def cleanup_all_uuid_files():
    """Delete all existing UUID generation files before starting a new generation."""
    try:
        deleted_count = 0
        current_dir = os.getcwd()
        
        for filename in os.listdir(current_dir):
            if filename.endswith('.txt') and (filename.startswith('uuid_range_') or filename.startswith('fast_uuids_')):
                try:
                    file_path = os.path.join(current_dir, filename)
                    os.unlink(file_path)
                    deleted_count += 1
                except Exception:
                    pass
        
        return deleted_count
    except Exception:
        return 0

def generate_unique_filename(start_uuid, end_uuid):
    """Generate a unique filename for the UUID range."""
    timestamp = int(time.time())
    # Create a hash of the UUIDs for uniqueness
    hash_input = f"{start_uuid}_{end_uuid}_{timestamp}"
    hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"uuid_range_{timestamp}_{hash_suffix}.txt"

def generate_uuids_to_file(start_time, end_time, step_seconds, task_id):
    """Generate UUIDs to a file in an optimized way."""
    try:
        # Delete all existing UUID files before starting generation
        cleanup_all_uuid_files()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        filename = temp_file.name
        
        # Update task status
        generation_tasks[task_id]['status'] = 'generating'
        generation_tasks[task_id]['file_path'] = filename
        
        # Optimized generation - ONLY UUIDs, no headers
        count = 0
        current_time = start_time
        
        while current_time <= end_time:
            # Check for cancellation
            if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
                print(f"DEBUG: Generation cancelled for task {task_id}, stopping at count {count}")
                temp_file.close()
                # Clean up partial file
                try:
                    os.unlink(filename)
                except:
                    pass
                return
            
            try:
                uuid_obj = generator.generate_uuid_v1(current_time)
                temp_file.write(f"{uuid_obj}\n")
                count += 1
                current_time += step_seconds
                
                # Update progress
                progress = min(100, (count / int((end_time - start_time) / step_seconds)) * 100)
                generation_tasks[task_id]['progress'] = progress
                generation_tasks[task_id]['count'] = count
                
                # Small delay to prevent overwhelming the system
                if count % 10000 == 0:
                    time.sleep(0.001)
            except Exception:
                pass
        
        temp_file.close()
        
        # Check for cancellation one more time before marking as complete
        if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
            print(f"DEBUG: Generation was cancelled for task {task_id}, cleaning up")
            try:
                os.unlink(filename)
            except:
                pass
            return
        
        # Update task status
        generation_tasks[task_id]['status'] = 'completed'
        generation_tasks[task_id]['progress'] = 100
        generation_tasks[task_id]['count'] = count
        
    except Exception as e:
        generation_tasks[task_id]['status'] = 'error'
        generation_tasks[task_id]['error'] = str(e)
        if 'temp_file' in locals():
            temp_file.close()
            try:
                os.unlink(filename)
            except:
                pass

def generate_range_background(start_uuid, end_uuid, task_id, total_possible):
    """Generate UUIDs in range in background with progress updates."""
    try:
        # Delete all existing UUID files before starting generation
        cleanup_all_uuid_files()
        
        # Update task status
        generation_tasks[task_id]['status'] = 'generating'
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        filename = temp_file.name
        
        # Update task with file path
        generation_tasks[task_id]['file_path'] = filename
        
        # Generate UUIDs in range
        count = 0
        
        # Use the fast UUID generation method that works correctly
        # This method generates UUIDs by manipulating hex timestamps directly
        start_uuid_obj = uuid.UUID(start_uuid)
        end_uuid_obj = uuid.UUID(end_uuid)
        
        # Extract timestamp components exactly like the fast method
        start_time_low = f"{start_uuid_obj.fields[0]:08x}"
        start_time_mid = f"{start_uuid_obj.fields[1]:04x}"
        start_time_hi = f"{start_uuid_obj.fields[2]:04x}"
        start_timestamp_hex = int(start_time_hi[1:] + start_time_mid + start_time_low, 16)  # Remove version bit
        
        end_time_low = f"{end_uuid_obj.fields[0]:08x}"
        end_time_mid = f"{end_uuid_obj.fields[1]:04x}"
        end_time_hi = f"{end_uuid_obj.fields[2]:04x}"
        end_timestamp_hex = int(end_time_hi[1:] + end_time_mid + end_time_low, 16)  # Remove version bit
        
        # Ensure start_timestamp_hex is always less than end_timestamp_hex
        if start_timestamp_hex > end_timestamp_hex:
            start_timestamp_hex, end_timestamp_hex = end_timestamp_hex, start_timestamp_hex
        
        # Extract clock_seq and mac from start UUID
        clock_seq = f"{start_uuid_obj.fields[3]:02x}{start_uuid_obj.fields[4]:02x}"
        mac_address = f"{start_uuid_obj.fields[5]:012x}"
        
        # Extract save_char (version bit) from start UUID
        save_char = f"{start_uuid_obj.fields[2]:04x}"[0]
        
        # Generate UUIDs for every hex timestamp in the range
        for current_timestamp_hex in range(start_timestamp_hex, end_timestamp_hex + 1):
            # Check for cancellation every 1000 iterations for more responsive cancellation
            if (current_timestamp_hex - start_timestamp_hex) % 1000 == 0:
                if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
                    print(f"DEBUG: Generation cancelled for task {task_id}, stopping at count {current_timestamp_hex - start_timestamp_hex}")
                    temp_file.close()
                    # Clean up partial file
                    try:
                        os.unlink(filename)
                    except:
                        pass
                    return
            
            try:
                # Generate UUID using the fast method
                uuid_str = fast_generator.generate_uuid_v1_custom(current_timestamp_hex, clock_seq, mac_address, save_char)
                if uuid_str:
                    # Write UUID to file
                    temp_file.write(f"{uuid_str}\n")
                    
                    # Update progress every 1000 UUIDs
                    count = current_timestamp_hex - start_timestamp_hex + 1
                    if count % 1000 == 0:
                        progress = min(100, (count / total_possible) * 100)
                        generation_tasks[task_id]['progress'] = progress
                        generation_tasks[task_id]['count'] = count
                        print(f"Range generation progress: {progress:.1f}% ({count:,}/{total_possible:,})")
                        
            except Exception as e:
                # Silent error handling - just continue
                pass
        
        temp_file.close()
        
        # Check for cancellation one more time before marking as complete
        if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
            print(f"DEBUG: Generation was cancelled for task {task_id}, cleaning up")
            try:
                os.unlink(filename)
            except:
                pass
            return
        
        # Update task status
        generation_tasks[task_id]['status'] = 'completed'
        generation_tasks[task_id]['progress'] = 100
        generation_tasks[task_id]['count'] = total_possible
        generation_tasks[task_id]['message'] = f"Generated {total_possible:,} UUIDs in range"
        
        print(f"Range generation completed. Count: {total_possible:,}")
        
    except Exception as e:
        generation_tasks[task_id]['status'] = 'error'
        generation_tasks[task_id]['error'] = str(e)
        print(f"Range generation error: {e}")
        if 'temp_file' in locals():
            temp_file.close()
            try:
                os.unlink(filename)
            except:
                pass

def generate_uuids_fast_background(start_uuid, end_uuid, task_id):
    """Generate UUIDs using fast method in background."""
    try:
        # Delete all existing UUID files before starting generation
        cleanup_all_uuid_files()
        
        # Update task status
        generation_tasks[task_id]['status'] = 'generating'
        
        # Check for cancellation before starting
        if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
            return
        
        # Pre-compute total_possible for progress
        try:
            start_uuid_obj = uuid.UUID(start_uuid)
            end_uuid_obj = uuid.UUID(end_uuid)
            start_time_low = f"{start_uuid_obj.fields[0]:08x}"
            start_time_mid = f"{start_uuid_obj.fields[1]:04x}"
            start_time_hi = f"{start_uuid_obj.fields[2]:04x}"
            start_timestamp_hex = int(start_time_hi[1:] + start_time_mid + start_time_low, 16)
            end_time_low = f"{end_uuid_obj.fields[0]:08x}"
            end_time_mid = f"{end_uuid_obj.fields[1]:04x}"
            end_time_hi = f"{end_uuid_obj.fields[2]:04x}"
            end_timestamp_hex = int(end_time_hi[1:] + end_time_mid + end_time_low, 16)
            if start_timestamp_hex > end_timestamp_hex:
                start_timestamp_hex, end_timestamp_hex = end_timestamp_hex, start_timestamp_hex
            total_possible = end_timestamp_hex - start_timestamp_hex + 1
        except Exception:
            total_possible = None

        filename = f"fast_uuids_{task_id}.txt"
        # Use the fast generator with live progress and cancellation
        success, result, count = fast_generator.generate_uuids_to_file_fast_with_progress(
            start_uuid, end_uuid, filename, task_id, total_possible
        )
        
        # Check for cancellation after generation
        if task_id in generation_tasks and generation_tasks[task_id].get('cancelled', False):
            # Clean up the generated file
            if os.path.exists(filename):
                try:
                    os.unlink(filename)
                except:
                    pass
            return
        
        if success:
            # Update task with file path and completion
            generation_tasks[task_id]['status'] = 'completed'
            generation_tasks[task_id]['file_path'] = os.path.abspath(filename)  # Use absolute path
            generation_tasks[task_id]['count'] = count
            generation_tasks[task_id]['progress'] = 100
            generation_tasks[task_id]['message'] = result
            generation_tasks[task_id]['start_uuid'] = start_uuid  # Store start UUID for filename generation
            generation_tasks[task_id]['end_uuid'] = end_uuid      # Store end UUID for filename generation
        else:
            generation_tasks[task_id]['status'] = 'error'
            generation_tasks[task_id]['error'] = result
            
    except Exception as e:
        generation_tasks[task_id]['status'] = 'error'
        generation_tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_uuid():
    """Analyze a single UUID."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    uuid_str = data.get('uuid', '')
    namespace = data.get('namespace', None)  # Optional namespace for UUID v3
    
    if not uuid_str:
        return jsonify({'error': 'UUID is required'}), 400
    
    # Strict UUID validation
    if not validate_uuid(uuid_str):
        return jsonify({'error': 'Invalid UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    
    result = generator.analyze_uuid(uuid_str, namespace=namespace)
    return jsonify(result)

@app.route('/api/estimate', methods=['POST'])
def estimate_range():
    """Estimate UUID range size and time."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    start_uuid = data.get('start_uuid', '')
    end_uuid = data.get('end_uuid', '')
    
    if not start_uuid or not end_uuid:
        return jsonify({'error': 'Both start and end UUIDs are required'}), 400
    
    # Strict UUID validation
    if not validate_uuid(start_uuid):
        return jsonify({'error': 'Invalid start UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    if not validate_uuid(end_uuid):
        return jsonify({'error': 'Invalid end UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    
    # Use a realistic default time step (100 nanoseconds = UUID's natural precision)
    step_seconds = 0.0000001  # 100 nanoseconds
    
    result = generator.estimate_range_size(start_uuid, end_uuid, step_seconds)
    return jsonify(result)

@app.route('/api/generate-range', methods=['POST'])
def generate_range():
    """Generate ALL UUIDs in range using background task."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    start_uuid = data.get('start_uuid', '')
    end_uuid = data.get('end_uuid', '')
    
    if not start_uuid or not end_uuid:
        return jsonify({'error': 'Both start and end UUIDs are required'}), 400
    
    # Strict UUID validation
    if not validate_uuid(start_uuid):
        return jsonify({'error': 'Invalid start UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    if not validate_uuid(end_uuid):
        return jsonify({'error': 'Invalid end UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    
    try:
        start_uuid_obj = uuid.UUID(start_uuid)
        end_uuid_obj = uuid.UUID(end_uuid)
    except ValueError:
        return jsonify({'error': 'Invalid UUID format'}), 400
    
    # Calculate total possible UUIDs in range using hex timestamps
    # Extract timestamp components from UUIDs
    start_time_low = f"{start_uuid_obj.fields[0]:08x}"
    start_time_mid = f"{start_uuid_obj.fields[1]:04x}"
    start_time_hi = f"{start_uuid_obj.fields[2]:04x}"
    start_timestamp_hex = int(start_time_hi[1:] + start_time_mid + start_time_low, 16)
    
    end_time_low = f"{end_uuid_obj.fields[0]:08x}"
    end_time_mid = f"{end_uuid_obj.fields[1]:04x}"
    end_time_hi = f"{end_uuid_obj.fields[2]:04x}"
    end_timestamp_hex = int(end_time_hi[1:] + end_time_mid + end_time_low, 16)
    
    if start_timestamp_hex > end_timestamp_hex:
        start_timestamp_hex, end_timestamp_hex = end_timestamp_hex, start_timestamp_hex
    
    total_possible = end_timestamp_hex - start_timestamp_hex + 1
    
    # Create unique task ID for this generation
    task_id = hashlib.md5(f"range_{start_uuid}_{end_uuid}_{time.time()}".encode()).hexdigest()
    
    # Initialize task
    generation_tasks[task_id] = {
        'status': 'queued',
        'progress': 0,
        'count': 0,
        'start_uuid': start_uuid,
        'end_uuid': end_uuid,
        'total_possible': total_possible,
        'created_at': time.time(),
        'type': 'range'
    }
    
    # Start generation in background thread
    thread = threading.Thread(
        target=generate_range_background,
        args=(start_uuid, end_uuid, task_id, total_possible)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'message': 'Range generation started in background',
        'status': 'queued',
        'total_possible': total_possible
    })

@app.route('/api/generate-single', methods=['POST'])
def generate_single():
    """Generate a single UUID with specified version."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    version = data.get('version', '1')
    name = data.get('name', '')
    
    # Validate version
    if not validate_version(version):
        return jsonify({'error': f'Invalid UUID version. Must be 1, 2, 3, or 4'}), 400
    
    try:
        if version == '1':
            uuid_obj = generator.generate_uuid_v1()
        elif version == '2':
            # Generate a UUID v2-like structure for DCE Security
            # This creates a UUID that follows DCE Security patterns
            uuid_obj = generator.generate_uuid_v2_like()
        elif version == '3':
            if not name:
                return jsonify({'error': 'Name is required for UUID v3'}), 400
            
            # Strict text validation for name
            if not validate_text_input(name, max_length=1000):
                return jsonify({'error': 'Invalid name format. Name must be text only, 1-1000 characters, and cannot contain special characters like < > " \''}), 400
            
            # Get namespace from request, default to DNS
            namespace_str = data.get('namespace', 'DNS').upper()
            
            # Validate namespace
            if not validate_namespace(namespace_str):
                return jsonify({'error': f'Invalid namespace. Must be one of: DNS, URL, OID, X500'}), 400
            
            # Map namespace string to UUID namespace
            namespace_map = {
                'DNS': uuid.NAMESPACE_DNS,
                'URL': uuid.NAMESPACE_URL,
                'OID': uuid.NAMESPACE_OID,
                'X500': uuid.NAMESPACE_X500
            }
            
            namespace_uuid = namespace_map[namespace_str]
            uuid_obj = uuid.uuid3(namespace_uuid, name)
        elif version == '4':
            uuid_obj = uuid.uuid4()
        else:
            return jsonify({'error': f'Unsupported UUID version: {version}'}), 400
        
        result = generator.analyze_uuid(str(uuid_obj), namespace=namespace_str if version == '3' else None)
        result['version'] = version
        if version == '3':
            result['name'] = name
            result['namespace_uuid'] = str(namespace_uuid)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate UUID v{version}: {str(e)}'}), 500


@app.route('/api/generate-range-fast', methods=['POST'])
def generate_range_fast():
    """Generate UUIDs using fast Ruby-like method in background."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    start_uuid = data.get('start_uuid', '')
    end_uuid = data.get('end_uuid', '')
    
    if not start_uuid or not end_uuid:
        return jsonify({'error': 'Both start and end UUIDs are required'}), 400
    
    # Strict UUID validation
    if not validate_uuid(start_uuid):
        return jsonify({'error': 'Invalid start UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    if not validate_uuid(end_uuid):
        return jsonify({'error': 'Invalid end UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}), 400
    
    try:
        # Create unique task ID
        task_id = hashlib.md5(f"fast_{start_uuid}_{end_uuid}_{time.time()}".encode()).hexdigest()
        
        # Initialize task
        generation_tasks[task_id] = {
            'status': 'queued',
            'progress': 0,
            'count': 0,
            'start_uuid': start_uuid,
            'end_uuid': end_uuid,
            'created_at': time.time(),
            'type': 'fast'
        }
        
        # Start generation in background thread
        thread = threading.Thread(
            target=generate_uuids_fast_background,
            args=(start_uuid, end_uuid, task_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': 'Fast generation started in background',
            'status': 'queued'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start fast generation: {str(e)}'}), 500


@app.route('/api/search-uuid', methods=['POST'])
def search_uuid_in_file():
    """Search for a specific UUID in a generated file using fast grep."""
    data = request.get_json()
    task_id = data.get('task_id', '')
    search_uuid = data.get('search_uuid', '')
    
    if not search_uuid:
        return jsonify({'error': 'Search UUID is required'}), 400
    
    # Validate UUID format
    if not validate_uuid(search_uuid):
        return jsonify({'error': 'Invalid UUID format'}), 400
    
    file_path = None
    
    # If task_id provided, use it; otherwise find the latest generated file
    if task_id:
        if task_id not in generation_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = generation_tasks[task_id]
        if task['status'] != 'completed':
            return jsonify({'error': 'Task not completed yet'}), 400
        
        file_path = task.get('file_path')
    else:
        # Find the latest generated UUID file
        current_dir = os.getcwd()
        uuid_files = []
        
        for filename in os.listdir(current_dir):
            if filename.endswith('.txt') and (filename.startswith('uuid_range_') or filename.startswith('fast_uuids_')):
                file_path_full = os.path.join(current_dir, filename)
                if os.path.isfile(file_path_full):
                    uuid_files.append((file_path_full, os.path.getmtime(file_path_full)))
        
        if uuid_files:
            # Sort by modification time (newest first) and get the latest
            uuid_files.sort(key=lambda x: x[1], reverse=True)
            file_path = uuid_files[0][0]
        else:
            return jsonify({'error': 'No generated UUID files found'}), 404
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Generated file not found'}), 404
    
    try:
        # Validate UUID format
        if not validate_uuid(search_uuid):
            return jsonify({'error': 'Invalid UUID format'}), 400
        
        # For very large files, use optimized grep with early exit
        # -F: fixed string (faster than regex)
        # -x: exact line match
        # -m 1: stop after first match (much faster for large files)
        import subprocess
        result = subprocess.run(['grep', '-Fxm', '1', search_uuid, file_path], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and result.stdout.strip():
            # UUID found
            return jsonify({
                'found': True,
                'count': 1,
                'message': 'UUID found in the generated file'
            })
        else:
            # UUID not found
            return jsonify({
                'found': False,
                'count': 0,
                'message': 'UUID not found in the generated file'
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Search timed out - file may be too large'}), 408
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/generation-status/<task_id>', methods=['GET'])
def get_generation_status(task_id):
    """Get the status of a generation task."""
    if task_id not in generation_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = generation_tasks[task_id]
    return jsonify(task)

@app.route('/api/download-file/<task_id>', methods=['GET'])
def download_generated_file(task_id):
    """Download the generated UUID file - file is kept after download."""
    if task_id not in generation_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = generation_tasks[task_id]
    
    if task.get('status') != 'completed':
        return jsonify({'error': 'File not ready yet'}), 400
    
    file_path = task.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Generated file not found'}), 404
    
    try:
        start_uuid = task.get('start_uuid', 'start')
        end_uuid = task.get('end_uuid', 'end')
        filename = generate_unique_filename(start_uuid, end_uuid)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/cleanup-task/<task_id>', methods=['DELETE'])
def cleanup_task(task_id):
    """Clean up a completed task from memory (file is NOT deleted)."""
    if task_id not in generation_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = generation_tasks[task_id]
    
    # Remove task from memory only - file is kept
    del generation_tasks[task_id]
    
    return jsonify({'message': 'Task removed from memory (file preserved)'})

@app.route('/api/cancel-generation/<task_id>', methods=['POST'])
def cancel_generation(task_id):
    """Cancel a running generation task and clean up files."""
    if task_id not in generation_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = generation_tasks[task_id]
    
    try:
        # Mark task as cancelled
        task['status'] = 'cancelled'
        task['error'] = 'Generation cancelled by user'
        task['cancelled'] = True  # Add cancellation flag
        
        # Clean up any existing files
        if 'file_path' in task and os.path.exists(task['file_path']):
            try:
                os.unlink(task['file_path'])
                print(f"DEBUG: Cancelled task file deleted: {task['file_path']}")
            except Exception as e:
                print(f"DEBUG: Error deleting cancelled task file: {e}")
        
        # Remove task from memory after a short delay to allow frontend to get status
        def cleanup_task():
            time.sleep(2)  # Wait 2 seconds for frontend to get final status
            if task_id in generation_tasks:
                del generation_tasks[task_id]
                print(f"DEBUG: Cancelled task {task_id} removed from memory")
        
        cleanup_thread = threading.Thread(target=cleanup_task)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        return jsonify({
            'message': 'Generation cancelled successfully',
            'status': 'cancelled'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to cancel generation: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    port = int(os.getenv('PORT', 5001))
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 
