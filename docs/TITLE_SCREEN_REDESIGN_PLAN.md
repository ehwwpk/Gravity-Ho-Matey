# Title Screen (Nav Station) — Analysis & Redesign Plan

**Status:** Plan only — no implementation until approved.  
**Scope:** `TitleScreenOverlay` / main menu at 960×640 (Brigand Nav Station).  
**Goal:** Fix overlap, missing information, and amateur hierarchy; match holo-sci-fi identity with pro menu UX.

---

## 1. Executive summary

The title screen **draws successfully** but was built by **stacking independent regions with hard-coded Y coordinates** that were never reconciled. The bottom ~120px has **three competing UI layers** (shop bar, page-tab chips, footer panel) that **physically overlap**. The Deploy (Select Chart) page **extends chart rows into the shop zone**. Navigation is **duplicated three times** (top bar page name, footer PREV/NEXT, floating tab buttons). There are **no layout regression tests**—only “draws without error.”

This is fixable without changing game flow: one **layout grid**, one **navigation model**, **measured regions**, and **acceptance tests** for bounds.

---

## 2. Root cause analysis

### 2.1 No single layout contract

| Problem | Evidence |
|---------|----------|
| `body_top` / `body_h` computed in `draw()` but pages use `_center_panel()` which **ignores** them | Pages receive `body_top` unused; vertical centering uses its own `bottom_reserved` formula |
| Magic numbers scattered (`-18`, `-8`, `-22`, `-6`, `+14`) | No one source of truth for “chrome vs content” |
| Panel height caps differ per page (400, 340, 360, 380) | Inconsistent content footprint |

### 2.2 Measured vertical collisions (960×640)

Computed from current constants in `title_overlay.py`:

| Zone | Y range (px) | Height |
|------|----------------|--------|
| Top bar | 0–54 | 54 |
| Body (theoretical) | 68–518 | 450 |
| **Shop CTA** | **526–564** | 38 |
| **Page tab buttons** | **552–570** | 18 |
| **Page rail label** | **~542** (text) | — |
| **Footer panel** | **576–634** | 58 |

**Confirmed overlaps:**

1. **Tab buttons (552–570) inside shop bar (526–564)** — buttons drawn on top of bazaar CTA; hit targets compete (`shop_open` vs `tab:*`).
2. **Deploy last chart row ends ~527** — **1px into shop zone**; footnote at **y≈541** fully inside shop bar.
3. **Footer vs tabs** — only **6px** gap; visually reads as one muddy strip.
4. **Rail label at y=542** — text over shop CTA label.

### 2.3 Horizontal / text issues

| Issue | Detail |
|-------|--------|
| Tab labels truncated to 8 chars | `"SELECT CHART"` → `"SELECT C"`; `"COMBAT"` ok |
| `draw_fitted_text` | Single-line **character estimate** truncate—no wrap; silent ellipsis |
| Footer center hint | `max_width = WIDTH - 280` but PREV/NEXT occupy ~216px left—center text can **visually collide** with buttons on long strings |
| Top bar | 4 text lines in 54px (TAB, BRIGAND, page title, GRAVITY HO + optional DEV line)—**crowded** when `DEV_UNLOCK_ALL_LEVELS` |
| Shop CTA | Long string + `▶` glyph—center anchor fights right glyph for space |

### 2.4 Interaction / IA problems

| Issue | Detail |
|-------|--------|
| **Triple navigation** | (1) Top: page name (2) Footer: ← PREV / NEXT → (3) Bottom: 5 tab chips overlapping shop |
| **Shop placement** | Full-width bar **between** content and footer—feels bolted on; steals space from Deploy list |
| **Missing campaign state** | Jewels only inside shop CTA; **no lives**, **no hull**, **no weapon doctrine** on main station |
| **Welcome vs Deploy** | Two paths to launch (“SELECT CHART →” vs Deploy tab)—ok if clear; currently buried in tab overlap noise |
| **No focus ring system** | Keyboard ↑↓ on Deploy; mouse hover; tab clicks—three paradigms, weak visual focus on tabs |

### 2.5 What tests miss today

`test_title_overlay.py` only checks:

- Each page draws without exception
- Hit map has level rows / shop region

**Missing:**

- Region bounding boxes do not intersect (except intentional z-order)
- All interactive targets ≥ minimum size (e.g. 36×36)
- Deploy list fully above action dock
- Tab labels readable (not truncated below minimum)
- Footer hint fits without overlapping PREV/NEXT

---

## 3. Industry principles (applied to this project)

From common game UI guidance (hierarchy, grouping, progressive disclosure, 2–3 clicks to any action):

| Principle | Application here |
|-----------|------------------|
| **One primary action per screen** | Welcome → Launch; Deploy → Pick chart; others → Read |
| **3–7 top-level sections max** | 5 tabs is ok—but **one** tab control, not three navigators |
| **Visual hierarchy** | Size + contrast: Title > Section > Body > Hint |
| **Grouping / whitespace** | 8px grid; 16–24px between groups; **no touching** chrome bands |
| **Progressive disclosure** | Shop = overlay (already); don’t stack shop + tabs + footer in same band |
| **Safe areas** | Fixed chrome height; content **clips/fits** inside middle |
| **Consistency** | Chart briefing uses similar holo chrome—reuse spacing tokens |
| **Controller + mouse** | Clear selected row on Deploy; visible tab focus |
| **Feedback** | Hover/selected states exist—need **non-overlapping** hit regions |

References: StraySpark UI hierarchy; Hades-style bold selection; “define layout on paper before engine” (Respawn UI guide).

---

## 4. Target information architecture

### 4.1 User jobs on title screen

1. **Launch** a sector (primary)
2. **Upgrade** ship (shop / skill deck)
3. **Learn** controls & rules (briefing tabs)
4. **See progress** (unlocks, jewels, lives, doctrine)

### 4.2 Proposed nav model (single system)

**Replace:** footer PREV/NEXT + bottom tab chips + redundant top duplicate  
**With:** **Horizontal tab bar directly under header** (full labels, clickable, keyboard ←/→)

- Top bar = **brand + campaign vitals** only (not page title duplication)
- Tab bar = **5 tabs** with full names (or icons + short labels)
- Footer = **context hints only** (no PREV/NEXT buttons)
- Shop = **right side of tab bar** OR **dedicated dock row**—never overlapping tabs

### 4.3 Content priority by tab

| Tab | Primary | Secondary |
|-----|---------|-----------|
| Welcome | Launch CTA | Tagline, skiff preview |
| Mission | Objectives list | Link to Deploy |
| Controls | Key map | — |
| Combat | Damage rules | Lives/hull reminder |
| Deploy | Chart list | Unlock hints |

---

## 5. Proposed layout grid (960×640)

All Y positions from **top**. Use **8px base grid**.

```
┌──────────────────────────────────────────────────────────── 960 ─┐
│ HEADER                                    52px  y: 0–52         │
│  [GRAVITY HO, MATEY!]          ★ 42  ♥ 3  │ DOCTRINE: Scatter   │
├─────────────────────────────────────────────────────────────────┤
│ TAB BAR                                   40px  y: 52–92        │
│  Welcome │ Mission │ Controls │ Combat │ Deploy    [SKILL DECK] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ CONTENT (flex)                            468px y: 92–560       │
│  (single inset panel, 16px margin)                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ STATUS BAR                                32px  y: 560–592       │
│  ← → switch tabs · Enter launch · B shop   Cove · Solar open…  │
├─────────────────────────────────────────────────────────────────┤
│ (optional 8px breathing room)                                   │
└─────────────────────────────────────────────────────────────────┘
  Total chrome: 52+40+32+16 = 140px → content 468px (vs ~450 today but **no overlap**)
```

### Zone constants (implementation targets)

| Token | Value | Notes |
|-------|-------|-------|
| `HEADER_H` | 52 | Brand + vitals |
| `TAB_BAR_H` | 40 | Full tab labels; shop button right-aligned inside bar |
| `STATUS_H` | 32 | Hints + unlock strip only |
| `MARGIN_X` | 20 | |
| `CONTENT_PAD` | 16 | Inside panel |
| `GAP` | 8 | Grid unit |

**Remove entirely:** `_draw_page_rail`, footer PREV/NEXT buttons, separate `SHOP_CTA_H` row overlapping tabs.

**Shop access:** Compact **“SKILL DECK ★N”** button in tab bar (height 32, width ~140); full overlay unchanged on click/`B`.

---

## 6. Per-page content spec

### 6.1 Welcome

- **Layout:** 2-column inside panel (55% copy / 45% skiff vignette)—keep identity
- **Copy block:** Title 28px max (not 32 if tight), subtitle **max 2 lines** with wrap helper (future) or shorter copy
- **Primary CTA:** One button “OPEN CHART MANIFEST” → switches to Deploy tab (not separate nav concept)
- **Secondary:** Text hint “Skill Deck in tab bar · B shortcut”
- **Vertical budget:** ≤420px content—no footnote below panel

### 6.2 Mission / Controls / Combat

- **Single column** or **two column** only if measured to fit in 468px
- **Combat:** 4+3 blocks → reduce row stride from 52 to **44** OR use two-column card grid with **fixed card height 72**
- **Mission:** 5 rows × 46 → fits; keep
- **Controls:** 7 rows × 28 → fits; keep

### 6.3 Deploy (critical fix)

- **Row height:** 56px (down from 68) — still tappable
- **Row gap:** 8px
- **5 rows:** 5×56 + 4×8 = **312px**
- **Panel header:** 36px + list padding 12px → **~360px** total — fits in 468 with **108px** margin for footnote + panel chrome
- **Footnote:** Inside panel bottom, **above** panel border—not below panel
- **Right column:** Optional compact “last cleared” if space
- **Scroll (fallback):** If level count >6 later, clip with scroll arrows—defer until needed

### 6.4 Shop overlay

- Unchanged full-screen overlay
- Ensure `shop_open` clears/dims tab bar hits below (z-order already last-drawn)

---

## 7. Component standards

### 7.1 Typography scale (title screen)

| Role | Font | Max width behavior |
|------|------|-------------------|
| Game title | Courier 28 bold | One line |
| Panel title | FONT_SECTION | One line |
| Body | FONT_BODY | Fitted or wrap (see 7.2) |
| Hint | FONT_SMALL | One line, status bar only |
| Tab | FONT_BODY / BOLD selected | Full label or 12-char truncate min |

### 7.2 Text engine (follow-up)

Plan for `draw_fitted_text` limitations:

- **Phase 1:** Shorten copy strings to fit measured widths
- **Phase 2 (optional):** `draw_wrapped_text` with max lines for subtitles

### 7.3 Hit targets

- Minimum **44×32** for tabs and rows (WCAG-inspired touch target, scaled for mouse)
- **No overlapping** hit regions in `MenuHitMap` (assert in tests)

### 7.4 Campaign vitals (header right)

Display when available:

- `★ {jewels}` treasury
- `♥ {lives}` lives (campaign)
- Doctrine tag if chosen (`LANCE` / `SCATTER` / `NOVA` + advanced suffix)
- DEV badge only when flag set—**separate corner**, not stacked on page title

---

## 8. Visual hierarchy checklist (pro finish)

- [ ] One obvious primary action per tab
- [ ] Selected tab: filled background + accent underline (Hades-like)
- [ ] Deploy selected row: left accent bar + brighter border (already partial)
- [ ] Shop button: jewel color pulse—distinct from tabs but **same bar**
- [ ] Content panel: holo corners + scanlines (keep brand)
- [ ] Status bar: dimmer than content—never competes with CTA
- [ ] 8px grid alignment on all major edges

---

## 9. Implementation phases (when approved)

### Phase A — Layout engine (no visual redesign yet)

1. Add `TitleLayout` dataclass: computed rects for header, tab_bar, content, status
2. Single `compute_title_layout(W, H) -> TitleLayout`
3. Refactor `draw()` to use rects only—**delete** `_center_panel` magic
4. Add `tests/test_title_layout.py`: **zero intersection** between chrome rects; deploy list bottom ≤ content bottom

### Phase B — Navigation consolidation

1. Move tabs to tab bar; remove `_draw_page_rail` and footer PREV/NEXT
2. Wire ←/→ to tabs only; status bar hints updated
3. Move shop button into tab bar right slot

### Phase C — Content fit & copy

1. Deploy row height 56; footnote inside panel
2. Header campaign vitals
3. Shorten strings where truncation still happens
4. Combat/Mission spacing tune against layout rects

### Phase D — Polish

1. Tab underline animation (subtle, ≤200ms)
2. Welcome CTA → jump to Deploy tab
3. Optional: skiff vignette scale to content rect

---

## 10. Acceptance criteria (professional done checklist)

### Layout (automated)

- [ ] `header`, `tab_bar`, `content`, `status` rects pairwise non-overlapping (±1px tolerance)
- [ ] Deploy: every `level:*` hit region ⊆ `content` rect
- [ ] Shop button hit region ⊆ `tab_bar` rect
- [ ] No hit region with zero area

### Visual (manual QA at 960×640)

- [ ] Deploy: all 5 rows fully visible; footnote readable; no text over shop/tab area
- [ ] Welcome: title + CTA + 2 hint lines + skiff panel—no collision
- [ ] Combat: all 7 rule blocks visible
- [ ] Tabs: full labels readable (Deploy, Controls, Mission, Combat, Welcome)
- [ ] Header: jewels + lives visible without overlapping brand
- [ ] Shop overlay still opens/closes; hits on tree nodes work

### Interaction

- [ ] Click each tab → correct page; hover states correct
- [ ] ←/→ cycles tabs; ↑↓ on Deploy only changes focus
- [ ] B toggles shop; shop blocks tab clicks while open
- [ ] Enter on Deploy launches focused chart
- [ ] No click on tab registers as shop_open

### Regression

- [ ] Existing `test_title_overlay.py` cases pass
- [ ] Chart briefing shop path unchanged

---

## 11. ASCII before / after (bottom strip)

**Before (broken):**

```
  ... content ...
  [ chart row 5 bleeding here ]     y≈527
  footnote text here                y≈541
  ═══════ SHOP CTA ═══════════════  y=526–564
      [tab][tab][tab][tab][tab]     y=552–570  ← ON TOP OF SHOP
  ┌──── PREV NEXT │ hint... ────┐  y=576
  └─────────────────────────────┘
```

**After (planned):**

```
  ... content (clipped to y=92–560) ...
  ┌─ Welcome │ Mission │ ... │ Deploy ──── [SKILL DECK ★42] ─┐  y=52–92
  └───────────────────────────────────────────────────────────┘
  ← → tabs · Enter · B shop          Cove open · Solar open    y=560–592
```

---

## 12. Files to touch (implementation reference)

| File | Change |
|------|--------|
| `render/title_overlay.py` | Layout grid, tab bar, remove rail/footer buttons, page refit |
| `render/menu_ui.py` | Optional: compact tab button helper |
| `scenes/title.py` | Tab keys only if footer prev/next removed |
| `tests/test_title_layout.py` | **New** — bounds + overlap |
| `tests/test_title_overlay.py` | Update hit tests for new shop/tab positions |

**Out of scope:** Chart briefing layout (separate pass), shop skill tree interior (already redesigned).

---

## 13. Copy suggestions (shorter, fits layout)

| Current | Proposed |
|---------|----------|
| Shop CTA long string | Tab bar: `SKILL DECK · ★42` |
| Footer center (long) | Status: `Enter launch · B shop` |
| Welcome hint 3 lines | 2 lines max |
| Deploy footnote | Move inside panel: `Stacks persist for campaign.` |

---

*End of plan — review and approve before Phase A implementation.*
