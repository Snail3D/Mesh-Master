# Mesh Master Fix Summary

## Problem
Mesh Master was receiving DMs and Qwen3.6 was responding successfully (0.7s), but the reply failed to send back over LoRa. After the first reply, MeshCore would disconnect and crash with `RuntimeError: Event loop is closed`.

## Root Causes Identified

### 1. Event Loop Closure Race Condition
When MeshCore disconnected, the event loop closed immediately. BLE callbacks were still pending and tried to access the closed event loop, causing crashes.

### 2. Silent Error Returns
`meshcore.send_msg()` can return `EventType.ERROR` instead of raising an exception. The original code only logged that send failed without explaining WHY.

### 3. Timeout Issues
The send operation has a 15-second timeout. If no MSG_SENT or ERROR event arrives, it returns ERROR with reason="timeout".

## Fixes Applied

### 1. Event Loop Closed Check
```python
# Check if event loop is closed before attempting send
if self._loop and self._loop.is_closed():
    logger.error("send_direct failed: event loop is closed")
    return False
```

### 2. Enhanced Error Logging
```python
# If result is ERROR, log the reason
if result.type == EventType.ERROR:
    logger.error(f"send_msg returned ERROR: {result.payload}, {result.attributes}")
```

### 3. Better Disconnect Handler
```python
async def _handle_disconnect(self, event: Any) -> None:
    """Handle a disconnect event from MeshCore."""
    reason = event.payload.get("reason", "unknown") if isinstance(event.payload, dict) else str(event.payload)
    logger.warning(f"MeshCore device disconnected: {reason}")
    self._connected = False
    self._set_status("Disconnected")
```

## Testing

Run the test script after connecting the radios:
```bash
cd ~/clawd/Mesh-Master
source .venv/bin/activate
python scripts/test_send_direct.py
```

Or restart Mesh Master and send a test message from T1000-E:
```bash
cd ~/clawd/Mesh-Master
source .venv/bin/activate
python mesh-master.py --radio meshcore --mode primary
```

## What to Look For

When sending a message from T1000-E, you should see:
1. `📡 MeshCore DM from T1000-E: [N chars]`
2. `💸 High-cost openai for [user]: [N chars]`
3. `OPENAI: Sending to OpenAI-compatible endpoint (qwen3.6-35b-a3b) 🤖`
4. `OpenAI replied in X.Xs 🤖`
5. `[DEBUG] send_direct called: dst_key=..., text_len=...`
6. `[DEBUG] send_direct result: type=EventType.MSG_SENT, error=False`
7. Reply should appear on T1000-E ✅

## Commits Pushed

1. `38a4d61` - Disable Ollama fallbacks
2. `bee5169` - Add debug logging
3. `e57a477` - Add debug documentation
4. `c954013` - Fix send_direct error handling
5. `84cb906` - Add test script

All pushed to `main` branch at `Snail3D/Mesh-Master`.