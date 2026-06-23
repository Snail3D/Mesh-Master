"""Configure a T1000-E running MeshCore firmware - non-blocking version."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meshcore import MeshCore, SerialConnection


PORT = "/dev/cu.usbmodem101"
BAUD = 115200


async def safe(coro, name: str, default=None):
    try:
        result = await asyncio.wait_for(coro, timeout=4)
        print(f"{name}: {result}")
        return result
    except asyncio.TimeoutError:
        print(f"{name}: TIMEOUT")
        return default
    except Exception as e:
        print(f"{name}: {type(e).__name__}: {e}")
        return default


async def main(freq_mhz: int = 915, name: str = "guest", broadcast_msg: str = "Hello from commaclaw!") -> int:
    conn = SerialConnection(PORT, baudrate=BAUD)
    mc = MeshCore(conn)
    await mc.connect()
    print(f"✓ connected to {PORT}")

    # Read current state - each in parallel with timeout
    print("\n=== current state ===")
    await safe(mc.commands.get_bat(), "battery")
    await safe(mc.commands.get_tuning(), "tuning")
    await safe(mc.commands.req_owner_sync(), "owner")
    await safe(mc.commands.req_status_sync(), "status")
    await safe(mc.commands.req_self_telemetry_sync() if hasattr(mc.commands, "req_self_telemetry_sync") else mc.commands.get_self_telemetry(), "telemetry")

    # Configure
    print(f"\n=== setting freq={freq_mhz} MHz, name='{name}' ===")
    await safe(mc.commands.send_cmd(f"set name {name}", wait_for_response=True, timeout_s=5), "set name")
    await safe(mc.commands.send_cmd(f"set freq {freq_mhz}", wait_for_response=True, timeout_s=5), "set freq")

    # Verify
    print("\n=== verifying ===")
    await safe(mc.commands.req_owner_sync(), "owner after")
    await safe(mc.commands.get_tuning(), "tuning after")

    # Send broadcast
    print(f"\n=== broadcast: {broadcast_msg!r} ===")
    await safe(mc.commands.send_chan_msg(0, broadcast_msg), "broadcast ch0")

    await mc.disconnect()
    print("\n✓ done")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    freq = 915
    name = "guest"
    msg = "Hello from commaclaw!"
    for i, a in enumerate(args):
        if a == "--freq" and i + 1 < len(args):
            freq = int(args[i + 1])
        elif a == "--name" and i + 1 < len(args):
            name = args[i + 1]
        elif a == "--msg" and i + 1 < len(args):
            msg = args[i + 1]
    raise SystemExit(asyncio.run(main(freq_mhz=freq, name=name, broadcast_msg=msg)))