#!/usr/bin/env python3

import uuid

# Test UUID generation
generator = uuid.uuid1()
print(f"Generated UUID: {generator}")
print(f"UUID parts: {generator.hex}")
print(f"UUID fields: {generator.fields}")

# Test parsing
uuid_str = str(generator)
parts = uuid_str.split("-")
print(f"Split parts: {parts}")
print(f"Number of parts: {len(parts)}")

# Try to extract timestamp manually
if len(parts) == 6:
    low, mid, high, clock, mac = parts[0], parts[1], parts[2], parts[3], parts[4]
    print(f"Low: {low}")
    print(f"Mid: {mid}")
    print(f"High: {high}")
    print(f"Clock: {clock}")
    print(f"Mac: {mac}")
    
    # Extract version from high part
    save = high[0]
    high_hex = high[1:4]
    print(f"Save (version): {save}")
    print(f"High hex: {high_hex}")
    
    # Combine hex parts
    hex_combined = high_hex + mid + low
    print(f"Combined hex: {hex_combined}")
    
    try:
        timestamp = int(hex_combined, 16)
        print(f"Timestamp: {timestamp}")
    except ValueError as e:
        print(f"Error converting hex: {e}")
else:
    print("UUID doesn't have 6 parts!")


