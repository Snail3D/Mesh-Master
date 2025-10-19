# SECURITY INSTRUCTIONS - Mesh Master Project

> **FOR AI ASSISTANTS & DEVELOPERS**
> This document contains critical security guidelines for working on the Mesh Master project.

---

## ⚠️ CRITICAL: Read This First

This project handles **sensitive personal data** including:
- Private user conversations and chat histories
- Mailbox messages and PIN hashes
- User browsing history (offline wiki/web cache)
- Dashboard login credentials
- API keys and authentication tokens
- Private logs and reports

**NEVER commit sensitive data to git or push it to public repositories.**

---

## 🔒 Protected Files & Directories

### Files That MUST NEVER Be Committed:

#### 1. **Credentials & Configuration**
- `config.json` - Contains dashboard password, API keys, Tailscale auth keys
- `.env` files - Environment variables
- `*.pem`, `*.key` - SSH keys and certificates
- Any file containing passwords, tokens, or API keys

#### 2. **Personal User Data**
- `data/logs/` - Private user log entries (DM-only access)
- `data/reports/` - Public reports (still user-generated content)
- `data/saved_contexts.json` - User conversation history
- `data/mail_security.json` - Mailbox messages, PIN hashes, metadata
- `data/user_ai_settings.json` - User AI preferences
- `data/onboarding_state.json` - User onboarding progress
- `mesh_mail.db` - SQLite database with mail data

#### 3. **Cached/Temporary Data**
- `data/offline_wiki/*.json` - User's Wikipedia search history
- `data/offline_crawl/` - User's web browsing cache
- `data/offline_ddg/` - DuckDuckGo search cache
- `*.log` files - Application logs with user activity
- `messages.log`, `messages_archive.json` - Message history
- `stats_persistence.json` - Usage statistics with node IDs

#### 4. **Runtime State**
- `data/alarms_timers.json` - User alarms/timers
- `data/trivia_state.json` - Game state
- `data/wordle_state.json` - Game state
- `data/cavalry_game_states.json` - Game state
- `data/user_access.json` - User access control
- `data/user_languages.json` - User language preferences
- `data/weather_reports.json` - User weather data
- `data/relay_optout.json` - User privacy preferences
- `*.backup` files - Backup files may contain sensitive data

---

## ✅ What IS Safe to Commit

### Code Files:
- Python source files (`*.py`)
- Test files (`tests/*.py`)
- Documentation (`*.md`, except this file if it contains real credentials)

### Static Data Files:
- `data/bible_jesus_verses.json` - Public Bible verses
- `data/bible_web.json` - Public Bible content
- `data/yo_momma_jokes.json` - Public jokes
- `data/chuck_api_jokes.json` - Public jokes
- `data/blond_jokes.json` - Public jokes
- `data/el_paso_people_facts.json` - Public facts
- `data/mesh_master_quiz.json` - Quiz questions
- `data/meshtastic_quiz.json` - Quiz questions
- `data/meshtastic_knowledge.txt` - Public Meshtastic documentation

### Configuration Templates:
- `commands_config.json` - Command configuration (no secrets)
- `feature_flags.json` - Feature toggles
- `motd.json` - Message of the day
- `custom_commands.json` - Custom command definitions

---

## 🛡️ .gitignore Protection

The `.gitignore` file is configured to automatically protect sensitive files. However:

### ⚠️ Important Rules:

1. **NEVER use `git add -f` (force add)** on data files
2. **Always check `git status`** before committing
3. **Never commit files in `data/` unless you're certain they're static/public**
4. **When in doubt, ask the user or check this document**

### Verify Before Committing:
```bash
# Always run this before committing:
git status

# Check what will be committed:
git diff --cached --name-only

# Look for sensitive patterns:
git diff --cached | grep -i "password\|token\|key\|secret"
```

---

## 🚨 If You Accidentally Commit Sensitive Data

### Immediate Actions:

1. **STOP - Don't push to remote if you haven't already**

2. **If only in local commit (not pushed):**
   ```bash
   # Undo the last commit, keep changes
   git reset --soft HEAD~1

   # Remove sensitive files from staging
   git reset data/sensitive_file.json

   # Add to .gitignore if not already there
   echo "data/sensitive_file.json" >> .gitignore

   # Commit without sensitive files
   git add .gitignore
   git commit -m "Fix: Remove sensitive data"
   ```

3. **If already pushed to GitHub (CRITICAL):**
   ```bash
   # Back up the repository first
   cd ..
   tar -czf mesh-ai-backup-$(date +%Y%m%d).tar.gz mesh-ai/
   cd mesh-ai

   # Remove from git history using filter-repo
   git filter-repo --invert-paths --path data/sensitive_file.json --force

   # Restore remotes (filter-repo removes them)
   git remote add github-ssh git@github.com:Snail3D/Mesh-Master.git
   git remote add origin https://github.com/Snail3D/Mesh-Master.git

   # Force push (DESTRUCTIVE - rewrites public history)
   git push github-ssh main --force

   # NOTIFY THE USER to change exposed credentials immediately
   ```

4. **Notify the user to:**
   - Change any exposed passwords immediately
   - Rotate any exposed API keys/tokens
   - Review what data was exposed
   - Consider whether affected users need notification

---

## 📋 Security Checklist for AI Assistants

Before making any commit, verify:

- [ ] No `config.json` in staged files
- [ ] No files from `data/logs/` or `data/reports/`
- [ ] No `*.json` files from `data/` unless confirmed safe (jokes, Bible verses, etc.)
- [ ] No `.db`, `.log`, or `.backup` files
- [ ] No SSH keys, certificates, or credential files
- [ ] Ran `git status` and reviewed all staged files
- [ ] Checked for passwords/tokens with: `git diff --cached | grep -i "password\|token\|key\|secret"`

---

## 🔑 Password & Credential Guidelines

### For config.json:

1. **Dashboard Password (`admin_password`):**
   - Never use default "password"
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - Unique to this project
   - **NEVER commit to git**

2. **Tailscale Auth Key (`tailscale_auth_key`):**
   - Generate from https://login.tailscale.com/admin/settings/keys
   - Use ephemeral keys when possible
   - Rotate regularly
   - **NEVER commit to git**

3. **API Tokens:**
   - Telegram bot tokens
   - Home Assistant tokens
   - Any third-party API keys
   - **NEVER commit to git**

### Creating config.json on New Machines:

```bash
# Option 1: Copy from example (if you create one)
cp config.json.example config.json
nano config.json  # Add your credentials

# Option 2: Create from scratch
nano config.json
# Paste the template and fill in your values
```

**Template:**
```json
{
  "admin_password": "YOUR_SECURE_PASSWORD_HERE",
  "admin_password_hint": "your_hint_here",
  "serial_port": "/dev/serial/by-id/usb-RAKwireless_...",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "llama3.2:1b",
  "tailscale_auth_key": "tskey-auth-YOUR_KEY_HERE",
  "tailscale_enabled": true,
  "telegram_bot_token": "",
  "home_assistant_token": ""
}
```

---

## 📖 Common Scenarios

### Scenario 1: User Asks to "Commit Everything"

**DON'T:**
```bash
git add .  # This might add sensitive files!
git commit -m "Update"
```

**DO:**
```bash
# Check what's changed
git status

# Only add specific safe files
git add mesh-master.py
git add mesh_master/relay_manager.py
git add README.md

# Verify before committing
git status
git diff --cached --name-only

# Commit
git commit -m "Update relay manager logic"
```

### Scenario 2: User Made Changes to config.json

**Response:**
```
I see you've modified config.json. This file contains sensitive credentials
and is already gitignored. Your changes are saved locally but won't be
committed to git (which is correct for security).

If you want to share configuration structure, consider creating a
config.json.example file with placeholder values instead.
```

### Scenario 3: User Wants to Work on Another Computer

**Instructions:**
```
When you clone the repository on your other computer, you'll need to:

1. Clone: git clone git@github.com:Snail3D/Mesh-Master.git
2. Create config.json (it won't exist - it's gitignored for security)
3. Add your credentials to config.json
4. Run the application

Your personal data files (logs, mail, contexts) will regenerate as you use
the system. The .gitignore automatically protects them on all machines.
```

### Scenario 4: Debugging Requires Seeing Sensitive Data

**Safe Approach:**
```bash
# View file content without committing
cat data/mail_security.json

# Or in Python code, use clean_log() which redacts content
clean_log(f"Processing {len(messages)} messages", "📧")
# NOT: clean_log(f"Message content: {message_body}", "📧")
```

---

## 🔍 Security Audit Commands

### Check for Exposed Credentials:
```bash
# Search for common credential patterns in tracked files
git ls-files | xargs grep -i "password\|token\|secret\|api_key" | grep -v ".md:"

# Check what's currently staged
git diff --cached | grep -i "password\|token\|key\|secret"

# Find large data files that might be tracked
git ls-files | xargs ls -lh 2>/dev/null | awk '$5 ~ /M$/ {print $5, $NF}'
```

### Check Git History:
```bash
# See if config.json ever existed in history
git log --all --oneline -- config.json

# Check for sensitive files in history
git log --all --name-only --pretty=format: | sort -u | grep -E "data/(mail|saved|logs|offline)"
```

### Verify .gitignore is Working:
```bash
# Test if sensitive file would be ignored
git check-ignore -v config.json
git check-ignore -v data/mail_security.json
git check-ignore -v data/logs/test.json

# Should show the .gitignore rule that matches
```

---

## 📚 Additional Security Resources

### Key Files to Review:
- `.gitignore` - Protection rules
- `CLAUDE.md` - Project context (also gitignored to prevent accidental exposure)
- `SECURITY_REVIEW.md` - Security audit findings
- `README.md` - Project documentation

### Emergency Contacts:
- **User:** snailpi
- **GitHub Repo:** https://github.com/Snail3D/Mesh-Master
- **Issues:** Report security issues privately, not in public issues

---

## 🎯 Quick Reference: Safe vs Unsafe

### ✅ SAFE to Commit:
- Python source code (`*.py`)
- Documentation (`*.md` - except CLAUDE.md)
- Static data (jokes, Bible verses, quiz questions)
- Tests (`tests/*.py`)
- Scripts (`scripts/*.py`)
- Requirements (`requirements.txt`)

### ❌ NEVER Commit:
- `config.json`
- `data/logs/`, `data/reports/`
- `data/mail_security.json`
- `data/saved_contexts.json`
- `data/offline_wiki/*.json`
- `data/offline_crawl/`
- `*.log` files
- `*.db` files
- SSH keys (`*.pem`, `*.key`)
- Backup files (`*.backup`)

### ⚠️ VERIFY Before Committing:
- Any file in `data/` directory
- Any JSON file with user-generated content
- Configuration files
- Any file containing personal information

---

## 📝 Version History

- **2025-10-19:** Initial version after security incidents
  - Removed config.json from history (dashboard password exposed)
  - Removed personal data files from history (mail, contexts, cache)
  - Established gitignore protection rules

---

## ⚡ TL;DR for AI Assistants

1. **NEVER commit files in `data/` unless they're public static content (jokes, Bible verses)**
2. **NEVER commit `config.json` or any file with credentials**
3. **ALWAYS run `git status` before committing**
4. **WHEN IN DOUBT, ask the user or skip the file**
5. **IF you accidentally expose sensitive data, follow the emergency procedure above**

---

**Remember: It's better to under-commit than to accidentally expose user data!**

When working with this project, security and privacy come first. If you're unsure whether a file should be committed, err on the side of caution and ask the user.

---

**Last Updated:** 2025-10-19
**Maintainer:** snailpi
**Status:** Active - Review before every commit
