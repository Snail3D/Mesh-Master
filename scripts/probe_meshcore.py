"""Probe a serial device to see if it's running MeshCore firmware.

Tries to connect via the meshcore Python library and reads device info.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meshcore import MeshCore, SerialConnection


async def probe(port: str, baud: int = 115200) -> int:
    print(f"=== probing {port} @ {baud} baud ===")
    try:
        conn = SerialConnection(port, baudrate=baud)
        mc = MeshCore(conn)
        await mc.connect()
        print("✓ connected")

        # Try to read device info
        try:
            info = await mc.commands.get_device_info()
            print(f"device info: {info}")
        except Exception as e:
            print(f"get_device_info failed: {e}")

        # Try battery / version
        try:
            ver = await mc.commands.get_version()
            print(f"version: {ver}")
        except Exception as e:
            print(f"get_version failed: {e}")

        await mc.disconnect()
        return 0
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return 1


async def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/cu.usbmodem101"
    for baud in (115200, 9600):
        rc = await probe(port, baud)
        if rc == 0:
            return rc
    print("✗ device did not respond to MeshCore protocol at common baud rates")
    return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))