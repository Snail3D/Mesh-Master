# Mesh Master send_direct Debug Notes

## Issue Summary
Mesh Master receives DMs from T1000-E, Qwen3.6 responds successfully (0.7s), but the reply fails to send back over LoRa.

## Symptom Pattern
1. ✅ DM received: `📡 MeshCore DM from T1000-E: [16 chars]`
2. ✅ AI responds: `💸 High-cost openai for [user]: [16 chars]` → `OpenAI replied in 0.7s`
3. ❌ send_direct fails: `ERROR:meshcore_manager:send_direct failed: ` (empty error)
4. ❌ MeshCore disconnects: `INFO:meshcore_manager:MeshCoreManager stopped` → `📡 MeshCore: Disconnected`
5. ❌ BLE callback crash: `RuntimeError: Event loop is closed`
6. 🔁 Auto-reconnect loop

## Root Cause Analysis

### Empty Error Message
The exception caught in send_direct has an empty string representation (`str(exc)` returns `""`). This suggests:
- Custom exception class without `__str__` implementation
- Or exception is suppressed somewhere

### Event Loop Closure
The BLE callback crash happens AFTER send_direct fails:
```
File "bleak/backends/corebluetooth/PeripheralDelegate.py", line 468
    self._event_loop.call_soon_threadsafe(
  File "asyncio/base_events.py", line 845
    self._check_closed()
  File "asyncio/base_events.py", line 545
    raise RuntimeError('Event loop is closed')
```

This indicates:
1. send_direct is called
2. Something causes MeshCoreManager to stop
3. Event loop closes
4. Pending BLE callbacks fire and try to access closed loop
5. Crash

### Why send_direct fails
The enhanced logging added should show:
- `result.type` from meshcore.send_msg
- Exception traceback if raised

But logging isn't appearing in mesh_master.log. This suggests either:
1. The exception isn't being raised (result.type == EventType.ERROR)
2. Logger output is going elsewhere
3. Event loop closes before logger flushes

## Potential Fixes

### Fix 1: Add Event Loop Cleanup
Ensure BLE callbacks are properly unsubscribed before closing the event loop:
```python
async def _connect_and_run(self):
    # ... existing code ...
    try:
        await self._keep_running()
    finally:
        # Unsubscribe all events before disconnecting
        self._mc.unsubscribe(EventType.CONTACT_MSG_RECV, self._handle_contact_message)
        self._mc.unsubscribe(EventType.CHANNEL_MSG_RECV, self._handle_channel_message)
        self._mc.unsubscribe(EventType.DISCONNECTED, self._handle_disconnect)
        await cx.disconnect()
```

### Fix 2: Check result.type Before Returning
```python
result = future.result(timeout=timeout)
if result.type == EventType.ERROR:
    logger.error(f"send_msg returned ERROR: {result.payload}, {result.attributes}")
    return False
return True
```

### Fix 3: Add Timeout and Retry
```python
try:
    result = future.result(timeout=timeout)
    # ...
except asyncio.TimeoutError:
    logger.error(f"send_direct timeout after {timeout}s")
    return False
```

### Fix 4: Verify sender_key
The issue might be that sender_key is empty or invalid. Add logging in on_meshcore_message:
```python
sender_key = msg.get("sender_key", "")
logger.info(f"Replying to sender_key={sender_key[:8]}, reply_text={reply_text[:50]}...")
```

## Next Steps
1. Reconnect T1000-E radio
2. Send test message
3. Check debug output for:
   - `[DEBUG] send_direct called:` print statements
   - Enhanced exception logging
   - sender_key values
4. Based on findings, apply appropriate fix

## Files Modified
- `mesh_master/meshcore_manager.py` - Added debug logging
- `mesh-master.py` - Added sender_key logging

## Git Commit
```
commit bee5169
Add debug logging for send_direct failure

- Added enhanced exception logging with traceback
- Added print statements for immediate debugging
- Issue: send_direct fails with empty error message
- MeshCore disconnects after every response
- BLE callbacks crash with 'Event loop is closed'
```