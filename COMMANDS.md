# Mesh Master Command Reference

Complete reference for all commands available in Mesh Master v2.0.

**Note:** All commands are case-insensitive. Commands can be sent via:
- Direct message to the Mesh Master node
- Broadcast on configured channels
- Telegram bot (if enabled)
- Dashboard web interface

---

## Table of Contents

- [Getting Started](#getting-started)
- [AI & Conversations](#ai--conversations)
- [Network & Relay](#network--relay)
- [Mesh Mail](#mesh-mail)
- [Logs & Reports](#logs--reports)
- [Knowledge & Research](#knowledge--research)
- [Games](#games)
- [Personality & Context](#personality--context)
- [Location & Status](#location--status)
- [Admin Commands](#admin-commands)

---

## Getting Started

### `/onboard`
**Aliases:** `/onboarding`, `/onboardme`
**Function:** Start interactive 9-step onboarding tour
**Scope:** DM only
**Example:**
```
/onboard
```
Guides new users through:
1. Welcome & features
2. Main menu
3. Mesh mail
4. Logs & reports
5. Games
6. AI assistance
7. Helpful tools
8. Getting help
9. Ready to go

---

### `/menu`
**Aliases:** None
**Function:** Display main menu with all available features
**Scope:** DM or broadcast
**Example:**
```
/menu
```
Shows organized list of commands by category.

---

### `/help`
**Aliases:** None
**Function:** Show help information and command reference
**Scope:** DM or broadcast
**Example:**
```
/help
```
Displays quick command reference and links to documentation.

---

## AI & Conversations

### `/ai`
**Aliases:** `/bot`, `/query`, `/data`
**Function:** Ask the AI assistant a question
**Scope:** DM or configured channels
**Example:**
```
/ai What's the weather forecast?
/bot Explain how LoRa works
/query What time is it?
```
Uses configured Ollama model (default: `llama3.2:1b` or `wizard-math:7b`).

---

### `/aipersonality`
**Aliases:** None
**Function:** Manage AI personality settings
**Scope:** DM only
**Usage:**
```
/aipersonality              # List available personalities
/aipersonality list         # List available personalities
/aipersonality trailscout   # Set to trail scout personality
/aipersonality prompt       # Show current custom prompt
/aipersonality reset        # Reset to default
```
Available personalities: `trail_scout`, `tech_expert`, `survival`, `casual`, etc.

---

### `/vibe`
**Aliases:** None
**Function:** Adjust conversation tone
**Scope:** DM only
**Example:**
```
/vibe casual
/vibe professional
/vibe friendly
```
Changes AI response style without changing full personality.

---

### `/reset`
**Aliases:** None
**Function:** Clear AI conversation history
**Scope:** DM only
**Example:**
```
/reset
```
Useful when starting a new conversation topic or if AI context becomes confused.

---

### `/chathistory`
**Aliases:** None
**Function:** View your conversation history with the AI
**Scope:** DM only
**Example:**
```
/chathistory
```
Shows recent AI conversation messages (configurable limit).

---

## Network & Relay

### `<shortname> <message>`
**Aliases:** `/<shortname> <message>`
**Function:** Relay message to specific node by shortname
**Scope:** Any channel or DM
**Example:**
```
snmo hello there
/snmo how are you?
base anyone home?
```
Sends message to node with that shortname, with ACK confirmation.

---

### `/nodes`
**Aliases:** None
**Function:** List all mesh nodes seen in last 24 hours
**Scope:** DM or broadcast
**Example:**
```
/nodes
```
Shows: shortname, long name, SNR, last heard, sorted newest first.

---

### `/node`
**Aliases:** None
**Function:** Show detailed signal info for specific node
**Scope:** DM or broadcast
**Example:**
```
/node snmo
```
Shows: SNR, signal strength, last heard, hops, battery %, power status.

---

### `/networks`
**Aliases:** None
**Function:** List all connected mesh networks/channels
**Scope:** DM or broadcast
**Example:**
```
/networks
```
Shows all channels Mesh Master is monitoring.

---

### `/optout`
**Aliases:** None
**Function:** Disable receiving relay messages
**Scope:** DM only
**Example:**
```
/optout
```
Prevents others from relaying messages to you. Preference persists across reboots.

---

### `/optin`
**Aliases:** None
**Function:** Re-enable receiving relay messages
**Scope:** DM only
**Example:**
```
/optin
```
Allows others to relay messages to you again.

---

## Mesh Mail

### `/m`
**Aliases:** `/mail`
**Function:** Send message to a mailbox
**Scope:** DM only
**Example:**
```
/m ops Mission briefing at 0600
/mail supplies Need more batteries
```
Creates mailbox if it doesn't exist (prompts for PIN setup).

---

### `/c`
**Aliases:** `/checkmail`
**Function:** Check mailbox(es) or ask AI question about content
**Scope:** DM only
**Usage:**
```
/c                          # Check all subscribed mailboxes
/c ops                      # Check specific mailbox
/c ops What's the mission?  # AI search within mailbox
/checkmail                  # Same as /c
```

---

### `/emailhelp`
**Aliases:** None
**Function:** Show Mesh Mail system help
**Scope:** DM only
**Example:**
```
/emailhelp
```
Displays detailed mail commands and usage instructions.

---

### `/wipe`
**Aliases:** None
**Function:** Delete data (mailbox, chat history, personality, etc.)
**Scope:** DM only
**Usage:**
```
/wipe mailbox ops           # Delete 'ops' mailbox (owner only)
/wipe chathistory           # Clear AI conversation history
/wipe personality           # Reset AI personality to default
/wipe all ops               # Wipe mailbox and all associated data
```

---

## Logs & Reports

### `/log`
**Aliases:** None
**Function:** Create private log entry (only you can see)
**Scope:** DM only
**Example:**
```
/log mission Reached checkpoint A at 1400 hours
/log notes Remember to check batteries
```
Creates/appends to private log file in `data/logs/your_shortname_mission.json`.

---

### `/checklog`
**Aliases:** `/readlog`, `/readlogs`, `/checklogs`
**Function:** View your private log entries
**Scope:** DM only
**Usage:**
```
/checklog                   # List all your logs
/checklog mission           # View specific log
/readlog mission            # Same as /checklog
```

---

### `/report`
**Aliases:** None
**Function:** Create public report (searchable by everyone)
**Scope:** DM only
**Example:**
```
/report weather Sunny, 75F, light breeze from north
/report sighting 3 hikers at waypoint B heading south
```
Creates/appends to public report file in `data/reports/weather.json`.

---

### `/checkreport`
**Aliases:** `/readreport`, `/readreports`, `/checkreports`
**Function:** View public reports
**Scope:** DM only
**Usage:**
```
/checkreport                # List all reports
/checkreport weather        # View specific report
/readreport sighting        # Same as /checkreport
```

---

### `/find`
**Aliases:** None
**Function:** Fuzzy search across logs, reports, wiki, and crawl data
**Scope:** DM only
**Example:**
```
/find weather
/find mission briefing
```
Searches:
- Your private logs
- Public reports
- Offline wiki articles
- Web crawl cache
- DDG search results

Provides "Did you mean?" suggestions for misspellings.

---

## Knowledge & Research

### `/bible`
**Aliases:** None
**Function:** Lookup Bible verses or topics
**Scope:** DM or broadcast
**Example:**
```
/bible John 3:16
/bible love
/bible random
```

---

### `/meshtastic`
**Aliases:** None
**Function:** Query curated Meshtastic knowledge base (~25k tokens)
**Scope:** DM or broadcast
**Example:**
```
/meshtastic What is SNR?
/meshtastic How do I improve range?
```
Uses warm cache for instant follow-up questions.

---

### `/wiki`
**Aliases:** None
**Function:** Search Wikipedia (online)
**Scope:** DM or broadcast
**Example:**
```
/wiki LoRa technology
/wiki Raspberry Pi
```
Auto-saves to offline cache if `offline_wiki_autosave_from_wiki: true`.

---

### `/offline`
**Aliases:** None
**Function:** Search offline Wikipedia mirror
**Scope:** DM or broadcast
**Usage:**
```
/offline wiki LoRa
/offline wiki Python PIN=1234
```
Searches locally cached Wikipedia articles (no internet required).

---

### `/web`
**Aliases:** None
**Function:** Web search with content filtering
**Scope:** DM or broadcast
**Example:**
```
/web latest weather forecast
/web Meshtastic firmware update
```
Blocks adult/warez sites automatically.

---

### `/weather`
**Aliases:** None
**Function:** Get weather information
**Scope:** DM or broadcast
**Example:**
```
/weather
/weather 90210
/weather New York
```

---

### `/drudge`
**Aliases:** None
**Function:** Fetch Drudge Report headlines
**Scope:** DM or broadcast
**Example:**
```
/drudge
```

---

### `/chucknorris`
**Aliases:** None
**Function:** Get a random Chuck Norris joke
**Scope:** DM or broadcast
**Example:**
```
/chucknorris
```

---

### `/elpaso`
**Aliases:** None
**Function:** Local El Paso information
**Scope:** DM or broadcast
**Example:**
```
/elpaso
```

---

## Games

### `/games`
**Aliases:** None
**Function:** List all available games with descriptions
**Scope:** DM or broadcast
**Example:**
```
/games
```

---

### `/hangman`
**Aliases:** None
**Function:** Play Hangman word guessing game
**Usage:**
```
/hangman start              # Start new game
/hangman guess e            # Guess letter 'e'
/hangman solve hello        # Attempt to solve
/hangman quit               # End game
```

---

### `/wordle`
**Aliases:** None
**Function:** Play Wordle word puzzle
**Usage:**
```
/wordle start               # Start new game
/wordle guess crane         # Guess a 5-letter word
/wordle quit                # End game
```

---

### `/wordladder`
**Aliases:** None
**Function:** Transform one word into another, one letter at a time
**Usage:**
```
/wordladder start cold warm # Start with cold → warm
/wordladder step cord       # Next step: cold → cord
/wordladder hint            # Get AI hint
/wordladder quit            # End game
```

---

### `/adventure`
**Aliases:** None
**Function:** Interactive text adventure with branching storylines
**Usage:**
```
/adventure start            # Begin adventure
/adventure 1                # Choose option 1
/adventure restart          # Start over
```

---

### `/cipher`
**Aliases:** None
**Function:** Practice encryption/decryption
**Usage:**
```
/cipher start               # Get encrypted message
/cipher solve HELLO         # Attempt decryption
/cipher hint                # Get hint
/cipher quit                # End game
```

---

### `/morse`
**Aliases:** None
**Function:** Morse code practice
**Usage:**
```
/morse start                # Start practice
/morse .... . .-.. .-.. --- # Decode morse
/morse encode hello         # Encode to morse
/morse quit                 # End game
```

---

### `/quizbattle`
**Aliases:** None
**Function:** Trivia quiz game
**Usage:**
```
/quizbattle start           # Start quiz
/quizbattle 3               # Answer question 3
/quizbattle score           # Check score
/quizbattle quit            # End quiz
```

---

### `/masterquiz`
**Aliases:** None
**Function:** Mesh Master features quiz (50 questions)
**Usage:**
```
/masterquiz start           # Start quiz
/masterquiz 2               # Answer with option 2
/masterquiz score           # Check score
```
Tests knowledge of relay, logs, reports, mail, commands, dashboard, etc.

---

### `/meshtasticquiz`
**Aliases:** None
**Function:** Meshtastic technology quiz (50 questions)
**Usage:**
```
/meshtasticquiz start       # Start quiz
/meshtasticquiz b           # Answer with option b
/meshtasticquiz score       # Check score
```
Tests knowledge of LoRa, mesh networking, SNR, modem presets, security, etc.

---

### `/chess`
**Aliases:** None
**Function:** Play chess against another player
**Usage:**
```
/chess start @opponent      # Challenge opponent
/chess move e2e4            # Make move
/chess board                # Show current board
/chess resign               # Resign game
```

---

### `/checkers`
**Aliases:** None
**Function:** Play checkers
**Usage:**
```
/checkers start @opponent   # Challenge opponent
/checkers move 12-16        # Make move
/checkers board             # Show board
```

---

### `/tictactoe`
**Aliases:** `/ttt`
**Function:** Play tic-tac-toe
**Usage:**
```
/tictactoe start @opponent  # Challenge opponent
/tictactoe 5                # Mark position 5
```

---

### `/blackjack`
**Aliases:** `/bj`
**Function:** Play blackjack/21
**Usage:**
```
/blackjack start            # Start game
/blackjack hit              # Draw card
/blackjack stand            # End turn
/blackjack quit             # End game
```

---

### `/yahtzee`
**Aliases:** None
**Function:** Play Yahtzee dice game
**Usage:**
```
/yahtzee start              # Start game
/yahtzee roll               # Roll dice
/yahtzee keep 1 2 5         # Keep dice 1, 2, 5
/yahtzee score ones         # Score in 'ones' category
```

---

### `/bingo`
**Aliases:** None
**Function:** Play bingo
**Usage:**
```
/bingo start                # Start game
/bingo card                 # Show your card
/bingo call                 # Call next number
/bingo mark 25              # Mark number
```

---

### `/rps`
**Aliases:** None
**Function:** Rock, Paper, Scissors
**Usage:**
```
/rps rock
/rps paper
/rps scissors
```

---

### `/coinflip`
**Aliases:** None
**Function:** Flip a coin
**Usage:**
```
/coinflip
/coinflip 5                 # Flip 5 times
```

---

## Personality & Context

### `/save`
**Aliases:** None
**Function:** Save current conversation context as a capsule
**Scope:** DM only
**Usage:**
```
/save                       # Save with auto-generated name
/save mission_briefing      # Save with specific name
```
Perfect for mission hand-offs - preserves conversation context.

---

### `/recall`
**Aliases:** None
**Function:** Load previously saved context capsule
**Scope:** DM only
**Usage:**
```
/recall                     # List saved capsules
/recall mission_briefing    # Load specific capsule
```

---

## Location & Status

### `/test`
**Aliases:** None
**Function:** Test system responsiveness
**Scope:** DM or broadcast
**Example:**
```
/test
```
Returns quick status message.

---

### `/motd`
**Aliases:** None
**Function:** Show Message of the Day
**Scope:** DM or broadcast
**Example:**
```
/motd
```

---

### `/about`
**Aliases:** None
**Function:** Show Mesh Master version and info
**Scope:** DM or broadcast
**Example:**
```
/about
```

---

## Admin Commands

**Note:** All admin commands are DM-only and restricted to authorized users.

### `/changemotd`
**Function:** Update the Message of the Day
**Example:**
```
/changemotd Welcome to Mesh Master v2.0!
```

---

### `/changeprompt`
**Function:** Update the AI system prompt
**Example:**
```
/changeprompt You are a helpful assistant for off-grid communications.
```

---

### `/showprompt`
**Aliases:** `/printprompt`
**Function:** Display current system prompt
**Example:**
```
/showprompt
```

---

### `/showmodel`
**Function:** Display current Ollama model
**Example:**
```
/showmodel
```

---

### `/selectmodel`
**Function:** Change Ollama model
**Example:**
```
/selectmodel llama3.2:3b
```

---

### `/hops`
**Function:** Set hop limit (0-7)
**Example:**
```
/hops 3
```
Controls max message retransmissions across mesh.

---

### `/stop`
**Aliases:** `/exit`
**Function:** Stop Mesh Master service
**Example:**
```
/stop
```
Gracefully shuts down the system.

---

### `/reboot`
**Function:** Reboot the host system
**Example:**
```
/reboot
```
Reboots Raspberry Pi or host machine.

---

## Command Syntax Notes

### Case Insensitivity
All commands work in any case:
```
/MENU = /menu = /MeNu
```

### Aliases
Commands with aliases accept any listed variation:
```
/ai = /bot = /query = /data
/onboard = /onboarding = /onboardme
```

### DM vs Broadcast
- **DM only:** Mail, logs, reports, some admin commands
- **DM or broadcast:** AI, games, knowledge lookups, network commands
- **Configurable:** Can restrict AI to DM-only via `feature_flags.json`

### Buffer Delay
Some commands buffer ~3 seconds before responding to reduce radio congestion:
- Knowledge lookups
- Long AI responses
- Multi-result commands

---

## Getting Help

- **In-app:** Send `/help` or `/menu` to Mesh Master node
- **Dashboard:** `http://localhost:5000/dashboard` → Operations Center
- **Documentation:** See [README.md](README.md) and [CLAUDE.md](CLAUDE.md)
- **Issues:** [GitHub Issues](https://github.com/Snail3D/Mesh-Master/issues)

---

**Mesh Master v2.0**
Complete command reference • Last updated: 2025-10-10
