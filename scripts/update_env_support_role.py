"""
Update .env File with Support Staff Role ID
This script updates the SUPPORT_ROLE_ID in your .env file
"""

import os

# Configuration
SUPPORT_ROLE_ID = "1556660464765894796"
AUTO_ROLE_ID = "1556660492297043988"

env_path = os.path.join(os.path.dirname(__file__), '.env')

if not os.path.exists(env_path):
    print(f"❌ ERROR: .env file not found at {env_path}")
    print("Please make sure .env exists in the trading directory")
    exit(1)

try:
    with open(env_path, 'r') as f:
        lines = f.readlines()

    updated = False
    new_lines = []

    for line in lines:
        if line.startswith("SUPPORT_ROLE_ID="):
            new_lines.append(f"SUPPORT_ROLE_ID={SUPPORT_ROLE_ID}\n")
            updated = True
            print(f"✓ Updated SUPPORT_ROLE_ID to {SUPPORT_ROLE_ID}")
        elif line.startswith("AUTO_ROLE_ID="):
            new_lines.append(f"AUTO_ROLE_ID={AUTO_ROLE_ID}\n")
            updated = True
            print(f"✓ Updated AUTO_ROLE_ID to {AUTO_ROLE_ID}")
        else:
            new_lines.append(line)

    if not updated:
        # Add at the end if not found
        new_lines.append(f"\nSUPPORT_ROLE_ID={SUPPORT_ROLE_ID}\n")
        new_lines.append(f"AUTO_ROLE_ID={AUTO_ROLE_ID}\n")
        print(f"✓ Added SUPPORT_ROLE_ID to .env")
        print(f"✓ Added AUTO_ROLE_ID to .env")

    with open(env_path, 'w') as f:
        f.writelines(new_lines)

    print(f"\n✅ Successfully updated .env file")
    print(f"\n📝 Updated values:")
    print(f"   SUPPORT_ROLE_ID={SUPPORT_ROLE_ID}")
    print(f"   AUTO_ROLE_ID={AUTO_ROLE_ID}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
