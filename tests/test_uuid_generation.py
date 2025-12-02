#!/usr/bin/env python3
"""
Test script to verify UUID generation at specific timestamps.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generator
import uuid

def test_uuid_generation():
    """Test UUID generation at specific timestamps."""
    
    # Test UUIDs from the user's example
    start_uuid = "0867d7ee-f8d5-11ef-8a38-aedb2c11800f"
    missing_uuid = "08df43ec-f8d5-11ef-8a38-aedb2c11800f"
    end_uuid = "093444c8-f8d5-11ef-8a38-aedb2c11800f"
    
    print("Testing UUID generation...")
    print(f"Start UUID: {start_uuid}")
    print(f"Missing UUID: {missing_uuid}")
    print(f"End UUID: {end_uuid}")
    print()
    
    # Extract timestamps
    start_time = generator.uuid_to_timestamp(uuid.UUID(start_uuid))
    missing_time = generator.uuid_to_timestamp(uuid.UUID(missing_uuid))
    end_time = generator.uuid_to_timestamp(uuid.UUID(end_uuid))
    
    print(f"Start timestamp: {start_time}")
    print(f"Missing timestamp: {missing_time}")
    print(f"End timestamp: {end_time}")
    print()
    
    # Generate UUIDs at these timestamps
    print("Generating UUIDs at specific timestamps...")
    
    # Generate at start time
    generated_start = generator.generate_uuid_v1(start_time)
    generated_start_time = generator.uuid_to_timestamp(generated_start)
    print(f"Generated at start time: {generated_start} (timestamp: {generated_start_time})")
    
    # Generate at missing time
    generated_missing = generator.generate_uuid_v1(missing_time)
    generated_missing_time = generator.uuid_to_timestamp(generated_missing)
    print(f"Generated at missing time: {generated_missing} (timestamp: {generated_missing_time})")
    
    # Generate at end time
    generated_end = generator.generate_uuid_v1(end_time)
    generated_end_time = generator.uuid_to_timestamp(generated_end)
    print(f"Generated at end time: {generated_end} (timestamp: {generated_end_time})")
    
    print()
    
    # Verify timestamps match
    print("Verifying timestamps...")
    start_match = abs(generated_start_time - start_time) < 0.0000001
    missing_match = abs(generated_missing_time - missing_time) < 0.0000001
    end_match = abs(generated_end_time - end_time) < 0.0000001
    
    print(f"Start timestamp match: {start_match}")
    print(f"Missing timestamp match: {missing_match}")
    print(f"End timestamp match: {end_match}")
    
    # Test range generation
    print("\nTesting range generation...")
    step_seconds = 0.0000001  # 100 nanoseconds
    
    current_time = start_time
    count = 0
    max_count = 100  # Limit for testing
    
    while current_time <= end_time and count < max_count:
        generated_uuid = generator.generate_uuid_v1(current_time)
        generated_timestamp = generator.uuid_to_timestamp(generated_uuid)
        
        print(f"Time: {current_time:.9f} -> UUID: {generated_uuid} -> Timestamp: {generated_timestamp:.9f}")
        
        current_time += step_seconds
        count += 1
        
        # Check if we generated the missing UUID
        if str(generated_uuid) == missing_uuid:
            print(f"✓ Found missing UUID at iteration {count}!")
            break
    
    print(f"\nGenerated {count} UUIDs in range")

if __name__ == "__main__":
    test_uuid_generation()
