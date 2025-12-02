#!/usr/bin/env python3
"""
Test script to verify fast UUID generation method.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import fast_generator
import uuid

def test_fast_uuid_generation():
    """Test fast UUID generation method."""
    
    # Test UUIDs from the user's example
    start_uuid = "0867d7ee-f8d5-11ef-8a38-aedb2c11800f"
    missing_uuid = "08df43ec-f8d5-11ef-8a38-aedb2c11800f"
    end_uuid = "093444c8-f8d5-11ef-8a38-aedb2c11800f"
    
    print("Testing fast UUID generation...")
    print(f"Start UUID: {start_uuid}")
    print(f"Missing UUID: {missing_uuid}")
    print(f"End UUID: {end_uuid}")
    print()
    
    # Extract timestamp components exactly like the fast method
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
    
    print(f"Start timestamp hex: {start_timestamp_hex}")
    print(f"End timestamp hex: {end_timestamp_hex}")
    print(f"Range: {end_timestamp_hex - start_timestamp_hex + 1} UUIDs")
    print()
    
    # Extract clock_seq and mac from start UUID
    clock_seq = f"{start_uuid_obj.fields[3]:02x}{start_uuid_obj.fields[4]:02x}"
    mac_address = f"{start_uuid_obj.fields[5]:012x}"
    save_char = f"{start_uuid_obj.fields[2]:04x}"[0]
    
    print(f"Clock sequence: {clock_seq}")
    print(f"MAC address: {mac_address}")
    print(f"Save char: {save_char}")
    print()
    
    # Test generating a few UUIDs in the range
    print("Generating UUIDs in range...")
    count = 0
    max_test = 100
    
    for current_timestamp_hex in range(start_timestamp_hex, end_timestamp_hex + 1):
        try:
            uuid_str = fast_generator.generate_uuid_v1_custom(current_timestamp_hex, clock_seq, mac_address, save_char)
            if uuid_str:
                print(f"Step {count + 1}: {uuid_str}")
                count += 1
                
                # Check if we generated the missing UUID
                if uuid_str == missing_uuid:
                    print(f"✓ Found missing UUID at step {count}!")
                    break
                    
                if count >= max_test:
                    print(f"Reached test limit of {max_test} UUIDs")
                    break
                    
        except Exception as e:
            print(f"Error at step {count + 1}: {e}")
            break
    
    print(f"\nGenerated {count} UUIDs in range")

if __name__ == "__main__":
    test_fast_uuid_generation()
