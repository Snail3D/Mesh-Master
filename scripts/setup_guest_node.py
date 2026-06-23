"""Configure a freshly-flashed T1000-E running MeshCore.

- Send appstart (init session)
- Set radio name to 'guest'
- Set frequency to 915 MHz, US band preset
- Verify
- Send an advert (broadcast presence)
- Send a broadcast channel message
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meshcore import MeshCore, SerialConnection
from meshcore.events import EventType


PORT = "/dev/cu.usbmodem101"
BAUD = 115200


async def safe(coro, label, timeout=5):
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        print(f"  {label}: {result}")
        return result
    except asyncio.TimeoutError:
        print(f"  {label}: TIMEOUT")
    except Exception as e:
        print(f"  {label}: {type(e).__name__}: {e}")
    return None


async def main(
    name: str = "guest",
    freq: float = 915.0,
    bw: float = 250.0,
    sf: int = 11,
    cr: int = 5,
    broadcast_msg: str = "Hello from commaclaw guest node!",
) -> int:
    conn = SerialConnection(PORT, baudrate=BAUD)
    mc = MeshCore(conn)
    await mc.connect()
    print(f"✓ connected to {PORT}\n")

    # Subscribe to events so we see what comes back
    # (skipping event subscription — not needed for config and can hang)

    # 1. Init session
    print("=== appstart ===")
    await safe(mc.commands.send_appstart(), "appstart", timeout=8)
    await asyncio.sleep(0.5)

    # 2. Read state
    print("\n=== state ===")
    await safe(mc.commands.get_bat(), "battery")
    await safe(mc.commands.get_tuning(), "tuning")
    await safe(mc.commands.get_self_telemetry(), "self_telemetry")

    # 3. Configure name
    print(f"\n=== set name = '{name}' ===")
    await safe(mc.commands.set_name(name), "set_name")

    # 4. Configure radio (freq MHz, bw kHz, sf, cr)
    # US/AU band: 915 MHz, BW 250 kHz, SF 11, CR 5 (legacy wide)
    # Modern narrow: 910.525 MHz, BW 62.5 kHz, SF 7, CR 5 (recommended)
    print(f"\n=== set radio freq={freq} bw={bw} sf={sf} cr={cr} ===")
    await safe(mc.commands.set_radio(freq, bw, sf, cr), "set_radio")

    # 5. Verify
    print("\n=== verify ===")
    await safe(mc.commands.get_tuning(), "tuning")
    await safe(mc.commands.get_self_telemetry(), "self_telemetry")

    # 6. Broadcast presence (advert with flood)
    print("\n=== advert (flood=True) ===")
    await safe(mc.commands.send_advert(flood=True), "advert", timeout=8)
    await asyncio.sleep(2)

    # 7. Broadcast channel message
    print(f"\n=== broadcast ch0: {broadcast_msg!r} ===")
    if hasattr(mc.commands, "send_chan_msg"):
        await safe(
            mc.commands.send_chan_msg(0, broadcast_msg),
            "send_chan_msg", timeout=10,
        )
    else:
        print("  send_chan_msg not in DeviceCommands — trying via send_msg")
        try:
            r = await asyncio.wait_for(
                mc.commands.send_msg(broadcast_msg, channel_idx=0),
                timeout=10,
            )
            print(f"  send_msg: {r}")
        except Exception as e:
            print(f"  send_msg: {e}")

    await mc.disconnect()
    print("\n✓ done")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    kwargs = {}
    for i, a in enumerate(args):
        if a == "--name" and i + 1 < len(args):
            kwargs["name"] = args[i + 1]
        elif a == "--freq" and i + 1 < len(args):
            kwargs["freq"] = float(args[i + 1])
        elif a == "--bw" and i + 1 < len(args):
            kwargs["bw"] = float(args[i + 1])
        elif a == "--sf" and i + 1 < len(args):
            kwargs["sf"] = int(args[i + 1])
        elif a == "--cr" and i + 1 < len(args):
            kwargs["cr"] = int(args[i + 1])
        elif a == "--msg" and i + 1 < len(args):
            kwargs["broadcast_msg"] = args[i + 1]
    raise SystemExit(asyncio.run(main(**kwargs)))