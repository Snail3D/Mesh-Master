# Mesh Master Dashboard — UI Review & Improvement Report

**Reviewed:** 2026-06-22
**Reviewer:** Hermes Agent (auto-generated)
**Scope:** `~/clawd/Mesh-Master/static/` and the embedded dashboard template in `~/clawd/Mesh-Master/mesh-master.py`

---

## 0. Important clarification about the task scope

The task brief asked me to "read all the HTML/CSS/JS files in the `static/` directory." That directory is small and contains **only**:

```
static/
├── js/twemoji.min.js               (17 KB — Twemoji library, not used by dashboard)
├── mesh-master-banner.png          (logo, ~143 KB)
├── mesh-master-icon.{icns,ico,png,svg}
└── twemoji/svg/                    (3,691 emoji SVG files)
```

There are **no HTML or CSS files** in `static/`. The full dashboard — HTML, CSS, JavaScript, the login page, and a separate Command Builder page — lives inside `mesh-master.py` as Python `r"""..."""` template strings served via Flask's `render_template_string`. The active dashboard template spans:

| Page | Defined at | Approx. size |
|---|---|---|
| Root redirect `/` | `mesh-master.py:21380` | small |
| Login page `/login` | `mesh-master.py:22921` | ~200 lines |
| **Main dashboard `/dashboard`** | **`mesh-master.py:23225 → 25863`** | **~2,640 lines (HTML + CSS + JS)** |
| Command Builder `/command-builder` | `mesh-master.py:21960+` | ~250 lines |

Everything below references the **main dashboard** unless explicitly noted. The line numbers are inside `mesh-master.py`.

---

## TL;DR

**Visual design:** A polished "VS Code dark+" clone with hacker-terminal vibes — monospace everywhere, blue-cyan accent (#569cd6, exactly VS Code's `token` blue), the same success/warning/danger palette (`#6a9955 / #d7ba7d / #f44747`). It looks competent and on-brand for an ops console, but the entire UI is **monospace font + emoji icons**, which makes it feel dated by 2026 standards and conflicts with the futuristic SVG logo in `static/mesh-master-icon.svg`.

**Layout:** Three-column responsive grid (sidebar | panels | activity). Drag-to-reorder panels, collapse per-panel, persisted to `localStorage`. Decent for desktop, but **mobile UX is rough** (single column, large panels stack, log stream header is sticky).

**Color scheme:** Cohesive and dev-tools-appropriate, but has accessibility gaps: `--text-faint` (#7c8497 on #05070b) measures ~3.6:1 — below WCAG AA (4.5:1). The `outline: none` rules scattered throughout remove keyboard focus indicators.

**Feature gaps:** Major. The system has rich backend capabilities (GPS location, battery telemetry, signal metrics, message store, node registry) but the dashboard **never calls several of the endpoints** and exposes none of that data visually. No map, no node list, no battery widget, no signal/SNR view.

---

## 1. Visual design

### 1.1 What works

- **Cohesive theme.** The accent palette (`#569cd6`, `#6a9955`, `#d7ba7d`, `#f44747`) at `mesh-master.py:23262-23270` is a faithful reproduction of VS Code's "Dark+" syntax palette. If your audience is dev/ops, this is comfortable and recognizable.
- **Consistent panel rhythm.** The `panel` / `panel-header` / `panel-body` trio (`mesh-master.py:23453-23512`) gives every section a predictable shape with subtle hover (`box-shadow 0.2s`, `transform 0.2s` at line 23462).
- **Micro-interactions.** New log lines animate in with `@keyframes rise-in` (line 24606), the heartbeat pulses (`heartbeat-pulse` at 24680), scroll indicators bounce (`pulse-arrow` at 24675). The log panel has a gradient fade at the top edge (line 24573).
- **Draggable, collapsible panels.** Both visual + persistence to `localStorage` (see `applyPanelHiddenState`/`savePanelLayout` around line 27614 / 27520). Hidden panels can be re-shown from the sidebar menu.

### 1.2 What feels dated

- **Everything is monospace.** `mesh-master.py:23279`:
  ```
  font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
  ```
  Even panel titles like `<h2>Activity 📊</h2>` (line 25076) and the dashboard header logo (line 25058) render in monospace. Modern dashboards (Grafana 10+, Datadog, Linear, Vercel) pair a **sans-serif for UI** with monospace **only for code/data**. Recommendation: switch `--font-ui` to Rajdhani/Inter and keep `--font-mono` for code blocks, log lines, the CLI input, and serial port paths.

- **Loaded fonts are never used.** Line 23254 imports **Orbitron + Rajdhani** from Google Fonts:
  ```
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  ```
  But a global grep shows these families are **never referenced anywhere in the CSS**. Wasted ~50 KB request + the 200-500 ms TTFB to fonts.googleapis.com on every dashboard load. Either use them (Rajdhani for headings, Orbitron as a brand accent) or drop the `<link>`.

- **Emoji icons everywhere.** Headers and inline labels use emoji (📊 📡 📻 🛠️ ⚙️ 📱 🧠 📜 🔑 🔨 🎓 🌤️ 📦 🚀 🗑️ ⚠️ 🔐 📍 📶 🏓). They render inconsistently across OSes (Apple Color Emoji vs Segoe UI Emoji vs Noto Color Emoji). Also: the `/static/twemoji/svg/` folder ships 3,691 SVGs (118 KB just the directory entries) but **only the log renderer uses Twemoji** (`_render_log_line_html` in `mesh-master.py`); the dashboard chrome does not. Pick one icon system: emoji (cheap, inconsistent) OR an icon font OR inline SVG.

- **Two "Activity" panels.** Line 25076 calls the stats panel "Activity 📊" and line 25857 calls the log panel "Activity" — same name, two completely different things. Rename to **"Network Stats"** and **"Live Log"**.

- **Banner uses `mix-blend-mode: screen` (line 25060).** This makes the logo bright on dark but invisible on a light screenshot, and breaks in some PDF exports. Use a normal blend with a slight glow.

### 1.3 Code-level refresh recommendations

1. **Split the embedded CSS out of `mesh-master.py`.** Move it to `static/css/dashboard.css` and reference it via `<link href="/static/css/dashboard.css">`. Same for JS → `static/js/dashboard.js`. This single change makes the UI themeable, diffable, and far easier to lint. The 2,600-line `r"""..."""` block at line 23247 is the single biggest maintainability pain in this file.

2. **Tokenize the color system once.** Currently there are **two** near-identical `:root` blocks (dashboard at 23256, login at 22934). Move to `static/css/tokens.css` and `<link>` both pages.

3. **Replace `font-family: "JetBrains Mono"…` for body text** with a sans-serif system stack:
   ```css
   --font-ui: 'Rajdhani', system-ui, -apple-system, 'Segoe UI', sans-serif;
   --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
   body { font-family: var(--font-ui); }
   code, .log-line, #cliInput, .config-key-code { font-family: var(--font-mono); }
   ```

4. **Drop the Google Fonts link for Orbitron** unless you actually apply it. If you want a futuristic brand accent, apply `font-family: 'Orbitron', var(--font-mono);` to `h1, h2, .brand-title` only.

5. **Replace emoji icons** with inline SVG sprite (one file, 24×24 glyphs for 📊📡📻🛠️⚙️📱🧠📜). Cleaner, sharper, single color via `currentColor`.

---

## 2. Layout & UX

### 2.1 Information hierarchy

The main grid is defined at `mesh-master.py:23363-23372`:

```
grid-template-columns: minmax(160px, 220px) minmax(0, 1fr) minmax(320px, 34vw);
grid-template-areas: "menu panels activity";
```

So you get (left → right):

1. **Sidebar (220px):** "Sections" header + auto-generated menu of 9 panel buttons (`#panelMenu`, line 25071). The menu is **the only persistent navigation** — clicking a button hides/shows a panel.
2. **Panel grid (fluid center):** The 9 `<article class="panel">` cards (snapshot, meshcore-status, radio-settings, operations, config-overview, telegram, offline-knowledge, commands, log).
3. **Right column (34vw, sticky top: 92px):** A CLI input (`#cliInput`, line 25841) + the `log-panel`.

This is a sensible layout for ≥1320px screens. Issues:

- **The CLI is hidden until you scroll past several panels** because it's pinned to the bottom of the activity column but the activity column is just one card (the log). It would be more discoverable as a **floating action button** or a header bar input.
- **The "Sections" sidebar lists panel names with hide/show badges** (`panel-menu-badge` at line 23431). Good idea, but the labels are bare (no icons, no counts), so they read like an HTML sitemap rather than navigation.
- **The sidebar doesn't indicate which panel is currently in view.** As you scroll panels, the sidebar doesn't update. For 2,600+ lines of dashboard, this becomes painful.

### 2.2 Responsiveness

Three breakpoints, all reasonable:

| Breakpoint | Effect | Defined at |
|---|---|---|
| `≤ 1320px` | shrink sidebar to 150-200px; panels auto-fit | line 24995 |
| `≤ 960px` | single column; activity moves to top, then menu, then panels | line 25003 |
| `≤ 720px` | header stacks vertically | line 25024 |
| `≤ 1200px` | ops panel body collapses from 2-col to 1-col | line 23562 |
| `≤ 768px` | config-row stacks vertically | line 23833 |
| `≤ 480px` | mini-chart popups shrink | line 24443 |
| `hover: none` (touch) | disable chart popups | line 24434 |

This is **good coverage** for tablet/phone. But mobile users hit a wall:

- **Log panel is sticky on desktop** (`top: 92px`, line 23449) but on mobile it just becomes the **first** card (line 25006-25009). That means on a phone, you scroll past the entire live log before you reach any of the controls. Reverse it for mobile.
- **Panels remain 9 deep on mobile** with no tabs/accordion grouping. A long-press or "Compact Mode" toggle that collapses the config/operations/telegram panels into a tab bar would dramatically reduce mobile scrolling.
- **The config panel (25610) and operations panel (25443)** alone contain 10+ inline-style forms. On mobile, every input is a full-width 28-pixel monospace text field. Serviceable but cramped.

### 2.3 Drag-and-drop panels

Implemented with native HTML5 DnD. CSS for placeholders at lines 23481-23494 (`panel-placeholder`, `[data-panel-zone].drop-active`). The drag handle is the panel header (line 23467). State is persisted to `localStorage` under `PANEL_VISIBILITY_STORAGE_KEY` (referenced at line 27599). Works in browsers that support HTML5 DnD, which is all modern ones — but **fails on touch devices**. Recommend adding `@media (hover: none)` to disable drag and add an explicit "Reorder" mode.

### 2.4 UX recommendations

1. **Add a sticky toolbar above the panel grid** with quick filters: "Show: All / Config / Status / AI" and a search box that filters panels by header text.
2. **Sticky "Currently viewing" highlight** in the sidebar as the user scrolls.
3. **Move the CLI input to the header bar** (right side, next to "verbose logs" link at line 25065). One-line global input is more discoverable than buried in a column.
4. **Group the 9 panels by intent** in the sidebar: Status (snapshot, meshcore), Radio (radio-settings), Config (config-overview, operations), Integrations (telegram, offline-knowledge), Activity (commands, log). Use visual separators.
5. **Add a "Reset layout" button** to the sidebar (currently only `localStorage` — if a user hides everything and reloads, they're stuck; the only escape is DevTools).
6. **Mobile:** add a hamburger that opens the sidebar as a slide-in drawer instead of a stacked list (line 25011).
7. **Stop using `mix-blend-mode: screen`** on the banner logo (line 25060). Replace with `filter: brightness(1.1)` and a thin glow.

---

## 3. Color scheme & accessibility

### 3.1 Palette

Defined at `mesh-master.py:23256-23272` (dashboard) and `22934-22951` (login). Note the two blocks are **slightly different**:

| Token | Dashboard | Login |
|---|---|---|
| `--bg` | `#05070b` | `#040608` |
| `--accent` | `#569cd6` | `#3c92ff` |
| `--accent-strong` | `#007acc` | `#569cd6` |

This is a real inconsistency — clicking "Login" on the dashboard would feel like a different product.

### 3.2 WCAG contrast ratios

Run these against the dashboard background `#05070b`:

| Element | Color | Ratio | WCAG AA pass? |
|---|---|---|---|
| `--text-primary` body | `#d7deed` | 14.4:1 | ✅ AAA |
| `--text-secondary` labels | `#9aa4ba` | 7.4:1 | ✅ AAA |
| `--text-faint` muted | `#7c8497` | 4.7:1 | ✅ AA (just) |
| `--success` pill on dark | `#6a9955` | 5.9:1 | ✅ AA |
| `--warning` on dark | `#d7ba7d` | 10.0:1 | ✅ AAA |
| `--danger` on dark | `#f44747` | 5.6:1 | ✅ AA |
| `--accent` link on dark | `#569cd6` | 7.4:1 | ✅ AAA |
| `--text-faint` inside `#0b1018` panel | `#7c8497` | 4.4:1 | ⚠️ **AA fail** |

So `--text-faint` inside panel bodies (used heavily in config-key-code at line 23870, config-info, model-result-meta, and log timestamps) is borderline-to-failing. Bump it to `#9aa4ba` (same as secondary).

### 3.3 Focus management

There are **at least 12** `outline: none;` rules in the dashboard CSS (line 21460, 21612, 21809, 21823, 21956, 23336, 23418, 23537, 23694, 23758, 23925, 24060, 24199). Most of them are paired with `:focus-visible` styles (good) but some are bare `:focus { outline: none; }` (bad — keyboard users lose all focus indication).

For example, `mesh-master.py:23756-23760`:
```css
.config-select:focus {
  border-color: var(--accent);
  outline: none;
  box-shadow: 0 0 0 2px rgba(86, 156, 214, 0.22);
}
```
This is fine — uses box-shadow as the focus ring. But `mesh-master.py:24196-24200` removes outline on focus-without-replacement. Audit every `outline: none` and ensure there's an alternative focus indicator (border-color + box-shadow is a fine pattern, just don't remove outline AND box-shadow together).

### 3.4 Other accessibility observations

- **No skip-link.** A user navigating by keyboard has to tab past the entire panel menu on every page.
- **Color is the only signal in many places.** The "connected" / "degraded" / "disconnected" states (lines 23345-23362) rely on background color + text color only. Add a shape or icon (✓ / ⚠ / ✕).
- **Twemoji log lines** use the `img.emoji` class (line 24599) with `width: 1em; height: 1em` — good — but no `alt` text in the rendered output would matter for screen readers; verify `_render_log_line_html` (around line 21343) actually populates `alt`.
- **`<html lang="en">`** at line 23248 — good. But the dashboard is multilingual (channels, reports, wiki all have language selectors); the page lang never updates when the user switches UI language.
- **No reduced-motion handling.** The `@keyframes rise-in` (line 24606) and `heartbeat-pulse` (line 24680) animate unconditionally. Add `@media (prefers-reduced-motion: reduce)` to disable them.

### 3.5 Color recommendations

1. **Unify dashboard and login palettes.** Pick one `--accent` value.
2. **Bump `--text-faint` to `#9aa4ba`** (same as secondary) to clear WCAG AA on all backgrounds.
3. **Add shape-coded status indicators** (✓ ⚠ ✕ ● ◆) alongside color.
4. **Audit every `outline: none`** and add `@media (prefers-reduced-motion: reduce)` rules.

---

## 4. Feature gaps

This is the biggest section. The Mesh Master backend has **considerable** capabilities that the dashboard does **not expose**.

### 4.1 Backend endpoints the dashboard ignores

| Endpoint | Returns | Used by dashboard? |
|---|---|---|
| `GET /dashboard/battery` (line 19739) | battery %, voltage, charging state, radio name, connection type | ❌ **Never polled** |
| `GET /nodes` (line 19719) | list of node IDs with short/long names | ❌ **Never polled** |
| `GET /messages` (line 19712) | snapshot of recent messages | ❌ **Never polled** |
| `GET /mesh_locations.kml` (line 12387, route @ 21030+) | KML of GPS-located nodes | ❌ **No map view exists** |
| `GET /dashboard/metrics` | the rolling snapshot (used) | ✅ polled every 10s |
| `GET /connection_status` | `{status, error}` | ✅ indirectly via metrics |
| `GET /logs_stream` | SSE of new log lines | ✅ active |
| `GET /dashboard/wiki/list`, `/get`, `/delete`, `/prune` | wiki cache | ✅ via Offline Knowledge panel |

So **three major endpoints** (`/dashboard/battery`, `/nodes`, `/messages`) are wired up in Python but have **zero UI consumers**. That is a maintenance trap waiting to bite — a future developer refactoring those endpoints will see no test coverage and no UI breakage to warn them.

### 4.2 Critical missing panels for a mesh ops suite

In rough priority order:

#### 4.2.1 **Node registry / table** (P0)
A table view of every known node with: short name, long name, hardware model, battery %, last-heard timestamp, SNR, hop count. Should sort by last-heard descending and color rows by status (green <5 min, yellow <1 h, gray older).

*Backend signal already exists:* `_format_location_reply` at `mesh-master.py:12439`, the `nodes` dictionary on `interface`, `deviceMetrics` (line 19767), and the `last_heard` field already surfaced via `/nodes` (extend it).
*Frontend work:* new panel `data-panel-id="nodes"` between snapshot (25073) and radio-settings (25184). Reuse the `snapshot-grid` layout pattern.

#### 4.2.2 **Map view with live GPS nodes** (P0)
Mesh nodes frequently publish position packets. The backend already has `_collect_recent_locations` (line 10991) and `_build_locations_kml` (line 12387). The dashboard should show a Leaflet or MapLibre map (no API key needed) with markers for each recently-located node, colored by last-seen age, with a click → node detail popup.

*Add at line ~25142 (between MeshCore and Radio Settings).* Add `<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">` to the head and the corresponding JS. **Cache tiles via service worker** since this is an "off-grid" product.

#### 4.2.3 **Radio battery & status widget in header** (P0)
The `connectionBanner` at line 25069 only shows connection type + name. Extend it to show **battery icon + percentage + voltage** on the right side. Add a `GET /dashboard/battery` poll at the same cadence as metrics (10 s).

*Implementation:* add `updateBatteryBadge()` in the JS, parallel to `updateConnectionBanner()` at line 30209. Render in the `activity-header-meta` div (line 25858) or as a third cell in the banner.

#### 4.2.4 **Signal/SNR charts and link-quality table** (P1)
Per-neighbor SNR/RSSI history. Shows which links are degrading. Backend likely has the data already (line 2360: `snr = node_data.get("snr")`).

#### 4.2.5 **Recent messages panel** (P1)
A virtualized scroll list of the last 200 messages (incoming + outgoing) with: timestamp, from shortname, channel/DM indicator, snippet. Filter by channel, sender, or text. The `/messages` endpoint already returns the full list; just don't re-fetch it every 10 s — fetch on panel-open and append via SSE.

#### 4.2.6 **Offline queue visibility** (P1)
`relay_manager.py` supports a per-user offline message queue (max 10, 24 h expiry). Expose a panel: "Pending deliveries" with sender, recipient, age, attempts. Critical UX for an "off-grid AI operations suite" — currently invisible.

#### 4.2.7 **Mailbox notifications** (P1)
`mail_manager.py` has mailboxes and PIN protection. There is **no UI surface** at all. Add a small badge in the header (e.g. "📬 3 unread") + a panel listing recent mail.

#### 4.2.8 **Network health score** (P2)
Composite indicator: weighted average of "nodes active / total", "DM success rate", "queue depth", "battery". Single 0-100 number, color-coded, in the snapshot panel header.

#### 4.2.9 **Service / health controls** (P2)
Currently there are install/uninstall buttons (lines 25591-25606) but no "Restart Mesh Master", "View process logs", "Check disk space", "Test Ollama connection". The `/health` endpoint exists (referenced in `health_check.sh`) — surface it.

#### 4.2.10 **Alerting rules** (P3)
A simple "alert me when X" panel: e.g. "Alert on Telegram if radio battery < 20%", "Alert if no nodes seen for 1 h". Currently only hardcoded in config.

### 4.3 Minor UX gaps

- **No theme toggle.** The dark-only design is on-brand but a light mode for daylight field ops would be welcome. Could be a single CSS class swap on `<body>` plus a stored preference.
- **No "copy log" button.** Long debugging sessions often need to share the live log. One button → clipboard.
- **No fullscreen for the log panel.** The `resize: both` at line 24547 lets you drag but a "maximize" button would help.
- **No pause log button.** The auto-scroll behavior is great but you can't read a line that's actively pushing new ones in. Add a pause toggle next to the queue badge.
- **No export of stats** (CSV of the 24-hour counters, or PDF of the dashboard). Useful for incident reports.
- **No command palette** (Cmd-K to jump to any panel/action). Common in modern dashboards (Linear, Vercel, Sentry).
- **The "Buy me a pizza" footer** (line 25871-25875) is below the entire dashboard. Fine, but it's the only footer — consider making it a small button in the header to reduce visual weight.

---

## 5. Specific, actionable recommendations (ranked)

| # | Change | Effort | Impact | Where |
|---|---|---|---|---|
| 1 | **Extract dashboard CSS/JS** out of `mesh-master.py` into `static/css/dashboard.css` and `static/js/dashboard.js` | M | **High** — unlocks every other refactor | `mesh-master.py:23247-...` |
| 2 | **Build a Nodes panel** that polls `/nodes` (extended with battery/SNR) every 15 s | M | **Critical** — fills a major gap | new article in `.panel-grid` |
| 3 | **Add Leaflet map panel** for live GPS nodes | M-L | **Critical** — flagship feature | new article in `.panel-grid` |
| 4 | **Wire `/dashboard/battery` into the header banner** | S | **High** — uses existing endpoint | `connectionBanner` at line 25069 + new `updateBatteryBadge()` near line 30209 |
| 5 | **Switch body font to sans-serif**, keep monospace for code/data | S | High — modernizes look | `mesh-master.py:23279` |
| 6 | **Use Rajdhani/Orbitron** for headings (or remove the Google Fonts link) | S | Medium — improves brand | `mesh-master.py:23254` |
| 7 | **Unify login + dashboard color tokens** | S | Medium — consistency | move both `:root` blocks to a shared `tokens.css` |
| 8 | **Add "Reset layout"** button in sidebar | XS | Medium — rescue hatch | in `buildPanelMenu()` at line 27680 |
| 9 | **Rename the two "Activity" panels** to "Network Stats" / "Live Log" | XS | Medium — eliminates confusion | line 25076 + line 25857 |
| 10 | **Bump `--text-faint`** to clear WCAG AA on panel backgrounds | XS | Medium — accessibility | `mesh-master.py:23267` |
| 11 | **Add `prefers-reduced-motion`** overrides for animations | XS | Medium — accessibility | new media query at bottom of `<style>` |
| 12 | **Audit every `outline: none`** and ensure `:focus-visible` exists | S | High — accessibility | search for `outline: none` |
| 13 | **Add Recent Messages panel** | M | High — major gap | new article |
| 14 | **Add Offline Queue panel** (pending relay deliveries) | M | High — major gap | new article |
| 15 | **Replace emoji icons** with an inline SVG sprite | M | Medium — sharper look | replace in `<h2>` headers across dashboard |
| 16 | **Add "Reset layout" + status icons (shape)** | XS | Medium — UX | sidebar + banner |
| 17 | **Mobile: collapse panel grid into tab bar** | L | High — mobile UX | rework `.content` grid at `≤ 720px` |
| 18 | **Add light theme toggle** | M | Medium — opt-in audience expansion | new CSS class + toggle in header |
| 19 | **Add command palette (Cmd-K)** | L | Medium — power-user delight | new script in dashboard JS |
| 20 | **Add pause-log + copy-log buttons** to log panel | S | Medium — debugging UX | inside `.log-panel .panel-header` (line 25856) |

Legend: XS = <30 min, S = 1-2 h, M = half-day, L = 1-2 days.

---

## 6. Quick-win starter patch (proposed)

If you only do **one thing**, do this. Replace the dashboard font-family and add a battery poll:

```diff
--- a/mesh-master.py
+++ b/mesh-master.py
@@ -23255,7 +23255,9 @@
     <style id="dashboardStyles">
       :root {
         --bg: #05070b;
+        --font-ui: 'Rajdhani', system-ui, -apple-system, 'Segoe UI', sans-serif;
+        --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
         --bg-alt: #07090c;
         --bg-panel: #0b1018;
         --border: #111722;
@@ -23279,7 +23281,7 @@
       margin: 0;
       padding: 0;
       background: var(--bg);
       color: var(--text-primary);
-      font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
+      font-family: var(--font-ui);
       font-size: 13px;
       line-height: 1.6;
     }
@@ -25069,3 +25071,15 @@
-    <div id="connectionBanner" class="connection-banner is-unknown">Checking connection…</div>
+    <div id="connectionBanner" class="connection-banner is-unknown">
+      <span id="connectionBannerText">Checking connection…</span>
+      <span id="batteryBadge" class="queue-meta" hidden>🔋 —</span>
+    </div>
@@ -30209,3 +30217,28 @@
+    async function pollBattery() {
+      try {
+        const res = await fetch('/dashboard/battery', { cache: 'no-store' });
+        if (!res.ok) return;
+        const data = await res.json();
+        const badge = document.getElementById('batteryBadge');
+        if (!badge || !data || !data.success) return;
+        const lvl = data.battery_level;
+        const charging = data.is_charging ? '⚡' : '';
+        const volt = data.voltage ? ` · ${data.voltage.toFixed(2)}V` : '';
+        badge.textContent = `🔋 ${lvl}%${charging}${volt}`;
+        badge.hidden = false;
+        badge.dataset.tone = lvl > 50 ? 'fall' : (lvl > 20 ? 'steady' : 'rise');
+      } catch (err) {}
+    }
+    pollBattery();
+    setInterval(pollBattery, 30000);
```

This is ~40 lines of diff and immediately surfaces battery info that the backend already computes but the UI hides.

---

## 7. File-by-file review summary

| File | Status | Notes |
|---|---|---|
| `static/js/twemoji.min.js` | ✅ Kept | Not actually loaded by dashboard (line 23255 has no `<script src>`); log emoji rendering uses `_render_log_line_html` with inline `<img>` tags. Could be deleted unless CLI messages use it. |
| `static/twemoji/svg/*.svg` | ✅ Kept | Used by log line renderer at line 21343. |
| `static/mesh-master-banner.png` | ⚠️ | 143 KB PNG used in dashboard header. Could be optimized (PNGs compress better with oxipng); or replaced with inline SVG matching the icon style. |
| `static/mesh-master-icon.{icns,ico,png,svg}` | ✅ | Used for app/desktop integration, not dashboard. |
| `mesh-master.py:23225-25863` (dashboard) | ⚠️ Major refactor candidate | Extract CSS/JS, fix feature gaps. |
| `mesh-master.py:22921-23220` (login) | ⚠️ | Separate, duplicate CSS. Unify tokens. |
| `mesh-master.py:21960+` (command builder) | ⚠️ | Not reviewed in depth. Likely shares same monospace + inline-style patterns. Apply same treatment as dashboard. |

---

## 8. What I did NOT review

- The Command Builder page (`/command-builder`, line 21960+) — assumed similar style, recommend same treatment.
- Backend endpoint behavior — only inspected signatures, not responses.
- The 50+ Python helper functions referenced in the dashboard JS (only looked at the dashboard-side handler functions).
- Mobile-native performance (only static responsiveness was checked).
- Accessibility for screen readers beyond focus rings and color contrast.

---

## 9. Closing notes

The Mesh Master dashboard is **functionally rich but visually frozen in 2018** — and it has backend capabilities it never exposes. The two highest-leverage changes are:

1. **Extract the embedded CSS/JS** to `static/` so it's editable without touching 35,000-line Python.
2. **Build the Nodes + Map + Battery panels** — three missing pieces that turn the dashboard from "config + log viewer" into a true ops console.

Everything else is polish. Doing items 1 and 2 will likely take 3-5 working days and will change the product from "I check it occasionally" to "I leave it open on a second monitor during field ops" — which is what the project name promises.