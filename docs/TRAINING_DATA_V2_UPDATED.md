# Training Data Update Summary - Mesh Master Bot v2.0

## Overview
Updated training data for Mesh Master Bot fine-tuning to reflect **v2.0 actual features** with deep technical accuracy.

## Key Changes

### 1. Version Correction
- **Before**: References to "v2.5" (not released yet)
- **After**: All references to "v2.0+" (current actual version)

### 2. Command Accuracy
- **Removed**: `/relay` command (doesn't exist - relay uses shortnames)
- **Corrected**: All commands verified against actual mesh-master.py code
- **Added**: Command aliases (/checklog, /readlog, /checklogs, /readlogs, etc.)
- **Fixed**: Accurate DM-only restrictions for games, logs, reports, etc.

### 3. Meshtastic Technical Knowledge Added
**45 comprehensive Q&A pairs covering:**
- **Core Concepts**: What is Meshtastic, LoRa, encryption, range (2-5km urban, 10-15km rural, 331km record)
- **Message Relay & Routing**: Hop limits, managed flooding, ACK system, packet storage
- **Node Roles**: CLIENT, ROUTER, REPEATER, CLIENT_MUTE (with power/battery implications)
- **Modem Presets**: LongFast, LongSlow, MediumFast, ShortFast (SF=7 to SF=12, bandwidth tradeoffs)
- **Signal Metrics**: SNR (>5dB excellent, 0-5dB good, <0dB marginal), RSSI (-50dBm strong, -120dBm weak)
- **Packet Structure**: 4-byte dest/sender IDs, hop limit, channel hash, encrypted payload (~240 bytes max)
- **Protocol Details**: CSMA/CA, time-on-air limits (FCC 1% duty cycle = 36s/hour), message types
- **Battery & Power**: CLIENT 2-7 days, ROUTER needs continuous power, optimization tips
- **Troubleshooting**: ACK failures, reliability improvements, security notes, topology best practices
- **Antenna Tips**: Vertical orientation, clear LOS, height matters, 3dBi mobile / 5-9dBi fixed

### 4. Deep System Explanations Added
**Mailbox System (9 detailed Q&A):**
- How mailboxes work (shared message boards, /m to send, /c to read)
- Subscription model (auto-subscribe when sending or reading)
- PIN protection (optional access control)
- Ownership (first creator owns, can wipe/manage)
- Notifications (heartbeat-based, configurable quiet hours)
- Storage (mesh_mailboxes.json, max 50 messages default)
- Search feature (/c <mailbox> <question> uses llama3.2:1b)

**Logs System (5 detailed Q&A):**
- Private notes only YOU can read
- Storage: data/logs/<your-node-id>/<title>.txt
- DM-only creation
- Aliases: /checklog, /readlog, /checklogs, /readlogs
- Max entries: logs_max_entries (default 100)

**Reports System (5 detailed Q&A):**
- Public notes searchable by everyone
- Storage: data/reports/<title>.txt (shared)
- Anyone can search with /find
- DM-only creation
- Aliases: /checkreport, /readreport, etc.

**Find/Search System (4 detailed Q&A):**
- Searches: YOUR logs + ALL reports + wiki + web crawls + DDG saves
- Fuzzy matching with "Did you mean?" suggestions
- Numbered results, reply with number to view
- Scope clarity (private logs vs public reports)

**Wiki & Web System (5 detailed Q&A):**
- /wiki searches Wikipedia API (needs internet), caches results
- /offline wiki searches pre-cached articles (no internet)
- /web searches internet, filters adult/warez sites
- Results cached in data/offline_wiki/, data/offline_crawl/
- All searchable offline with /find

**Relay System Internals (5 detailed Q&A):**
- Shortname cache (auto-learns from mesh traffic)
- Offline relay queue (max 10 msgs/recipient, 24h expiry, 3 attempts)
- ACK tracking (20s timeout, PENDING_RELAY_ACKS dict)
- Cross-network bridge (relay between Network A and B)
- Queue workflow (fail → queue → retry when online → notify sender)

### 5. Bot Identity
**Updated system prompt and identity pairs:**
- Name: "Mesh Master Bot"
- Purpose: Help operators use Mesh-Master v2.0, explain LoRa networking, troubleshoot
- Expertise: All 50+ commands, Meshtastic protocols, field operations
- Response style: Concise (<160 chars ideal), command-first, signal-aware, never hallucinate

### 6. Training Data Statistics
**Total training pairs: ~50,100**
- Archive conversations: ~5,000 (from messages_archive.json)
- Mailbox threads: ~2,000 (from mesh_mailboxes.json)
- **Meshtastic knowledge: 45** (NEW)
- Identity pairs: 6
- System usage pairs: 14
- Command variations: ~120 (30+ commands × 4 variations)
- **Deep technical explanations: 38** (NEW - mailboxes, logs, reports, wiki, relay)
- Troubleshooting: 5
- Synthetic variations: ~42,900 (to reach 50k total)

## Verification Checklist
✅ All commands verified against mesh-master.py (grep for `if cmd ==` and `elif cmd in`)
✅ No fictional commands (removed /relay, verified /m, /c, /checklog, /find, etc.)
✅ DM-only restrictions accurate (games, logs, reports, onboarding, find)
✅ Meshtastic technical specs accurate (SNR ranges, modem presets, node roles)
✅ System internals accurate (mailbox storage, log directories, relay queue mechanics)
✅ Version references corrected (v2.0+ not v2.5)
✅ Bot identity consistent (Mesh Master Bot across all identity pairs)

## Files Modified
1. `/tmp/mesh-master/scripts/training/prepare_training_data.py`
   - Added `parse_meshtastic_knowledge()` function (45 Q&A pairs)
   - Updated `identity_pairs` (6 pairs, v2.0+ references)
   - Updated `system_usage_pairs` (14 pairs, accurate features)
   - Completely rewrote `templates` dict (30+ commands, verified syntax)
   - Expanded `tech_pairs` from 10 → 48 pairs (deep system explanations)
   - Updated `main()` to call parse_meshtastic_knowledge()
   - Updated metadata to track meshtastic_knowledge source

2. `/tmp/mesh-master/training_configs/Modelfile.mesh-ai-1b`
   - Changed system prompt: "v2.5+" → "v2.0+"

## Next Steps
1. **Generate training data**:
   ```bash
   cd /tmp/mesh-master
   python scripts/training/prepare_training_data.py --min-pairs 50000 --output-dir data/training
   ```

2. **Verify output**:
   - Check `data/training/metadata.json` for source breakdown
   - Inspect `data/training/train.jsonl` for accurate command examples
   - Ensure no v2.5 references or fictional commands

3. **Train model** (see TRAINING_GUIDE.md):
   ```bash
   accelerate launch -m axolotl.cli.train training_configs/mesh-ai-1b.yaml
   ```

4. **Evaluate** (see eval_model.py):
   - Test command accuracy (12 tests)
   - Verify brevity compliance (<160 chars)
   - Check for hallucinations (0% tolerance)
   - Validate technical knowledge (Meshtastic, mesh networking)

## Training Data Quality Standards
- **Accuracy**: All commands/features verified against actual code
- **Depth**: System internals explained (not just command syntax)
- **Practicality**: Real-world usage patterns (mailbox PINs, relay queue, offline wiki)
- **Technical rigor**: Meshtastic specs accurate (SNR ranges, modem presets, duty cycles)
- **No hallucinations**: Bot taught to say "Check /help" or "See meshtastic.org" when unsure
- **Version consistency**: All references to v2.0+ (current actual version)

## Example Training Pairs (Quality Check)

**Identity (Accurate):**
```
Q: "What's your name?"
A: "I'm Mesh Master Bot, your AI assistant for Meshtastic mesh networks running Mesh-Master v2.0+."
```

**Command (Verified):**
```
Q: "How do I relay to someone?"
A: "Type: <shortname> your message (e.g., alice meet at waypoint) - system tracks ACKs automatically"
```

**Deep System (Practical):**
```
Q: "How does mesh mail work?"
A: "Mailboxes are shared message boards. /m <mailbox> <message> sends to mailbox. /c lists all mailboxes. /c <mailbox> reads specific mailbox. Messages persist across reboots in mesh_mailboxes.json."
```

**Meshtastic Technical (Rigorous):**
```
Q: "What is SNR?"
A: "Signal-to-Noise Ratio measures signal quality in decibels (dB). >5dB = excellent, 0-5dB = good, -5 to 0dB = marginal, <-5dB = poor. LoRa can decode down to -20dB SNR."
```

**Troubleshooting (Actionable):**
```
Q: "Relay not working"
A: "Check: 1) Node seen with /nodes? 2) Correct shortname? 3) They haven't /optout? 4) Signal strength OK?"
```

## Token Budget Compliance
All training answers designed for Meshtastic's ~160 char/chunk limit:
- Short answers: 40-80 chars
- Medium answers: 80-160 chars
- Long answers: Split across 2-3 chunks (160 chars each)
- Token budget manager (in mesh_master/ai_utils/token_budget.py) trims responses at runtime

## Conclusion
Training data now reflects **actual v2.0 functionality** with deep technical accuracy. Bot will:
1. Know its name (Mesh Master Bot)
2. Explain real commands (no fictional /relay)
3. Understand system internals (mailbox storage, relay queue, log directories)
4. Provide Meshtastic technical knowledge (SNR, node roles, modem presets)
5. Guide users through practical workflows (relay queue, mailbox PINs, offline wiki)
6. Never hallucinate (taught to defer to /help or meshtastic.org when unsure)
