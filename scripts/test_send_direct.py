#!/usr/bin/env python3
"""
End-to-end test for Mesh Master send_direct functionality.
Run this after connecting T1000-E radio to verify the fix.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mesh_master.meshcore_manager import MeshCoreManager
from meshcore import EventType
import logging

logging.basicConfig(level=logging.DEBUG)

def on_message(msg):
    print(f"\n📨 Received message:")
    print(f"  From: {msg.get('sender_name', 'Unknown')}")
    print(f"  Text: {msg.get('text', '')}")
    print(f"  Is direct: {msg.get('is_direct', False)}")

def on_status_change(status):
    print(f"\n📡 Status: {status}")

async def test():
    print("\n=== Starting Mesh Master Test ===\n")

    mgr = MeshCoreManager(
        connection_type="ble",
        ble_address=None,  # Auto-discover
        on_message=on_message,
        on_status_change=on_status_change,
        auto_reconnect=False,
        debug=True,
    )

    print("Starting MeshCore manager...")
    mgr.start()

    # Wait for connection
    print("Waiting for connection (30s)...")
    for i in range(30):
        await asyncio.sleep(1)
        if mgr.is_connected:
            print(f"\n✓ Connected after {i+1}s!")
            break
    else:
        print("\n✗ Failed to connect")
        mgr.stop()
        return

    # Get contacts
    await asyncio.sleep(2)
    contacts = mgr.get_contacts()
    print(f"\n📋 Contacts: {list(contacts.keys())}")

    if not contacts:
        print("\n⚠️  No contacts found - run this test while T1000-E is powered on")
        mgr.stop()
        return

    # Test send to first contact
    target_key = list(contacts.keys())[0]
    contact = contacts[target_key]
    test_msg = "Test message from Mesh Master debug script"

    print(f"\n📤 Sending to {contact.get('name', 'Unknown')}:")
    print(f"   Key: {target_key[:8]}...")
    print(f"   Message: {test_msg}")

    result = mgr.send_direct(target_key, test_msg, timeout=20)

    if result:
        print(f"\n✓ Send successful!")
    else:
        print(f"\n✗ Send failed")

    # Wait for any messages
    print("\n⏱️  Waiting 10s for messages...")
    await asyncio.sleep(10)

    # Stop
    print("\n=== Test Complete ===")
    mgr.stop()
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test())