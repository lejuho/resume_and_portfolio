# Workspace Design System

Status: implemented through Cycle 30
Last reviewed: 2026-06-05 (Cycle 31 audit)
Source of truth for token values: `scripts/templates/workspace.html` `:root` block
Related: `requirements-dashboard.md` §14, `docs/acceptance-studio.md` §Workspace

---

## 1. Design Principles

The Workspace follows the same five principles as the Career Studio design system plus one
Workspace-specific addition:

1. **One canonical source** — live cards are the only personal-fact source; the Workspace
   never creates or mutates them.
2. **Sentence case throughout** — labels, headings, and button text use sentence case.
   `text-transform: uppercase` is prohibited.
3. **400/500 weight only** — `font-weight: 600` and `font-weight: 700` are prohibited in
   Workspace CSS.
4. **Token-driven surfaces** — all repeated color, radius, and border values are expressed
   through `--ws-*` CSS custom properties; hard-coded color repetition outside `:root` is
   prohibited.
5. **Progressive disclosure** — card summaries are clamped; long text is revealed on
   explicit user action, not by default.
6. **Deterministic fit signals** — coverage percentage and matched terms are computed
   client-side from keyword overlap; no LLM or provider call is used for matching.

---

## 2. Token Registry

Tokens are defined in `scripts/templates/workspace.html` `:root {}`. Repeated and semantic
hex values live in that single source; one-off exceptions are documented in §8 Known
Exceptions. This registry records semantic role only.

| Token | Semantic role | Light | Dark |
|---|---|---|---|
| `--ws-bg` | Page background | neutral near-white | near-black |
| `--ws-surface` | Card/pane/section fill | white | dark navy |
| `--ws-text` | Primary readable text | dark navy | light grey |
| `--ws-text-muted` | Secondary labels, metadata | medium grey | medium grey |
| `--ws-text-secondary` | Tertiary context text | dark grey | light grey |
| `--ws-coverage-muted` | Coverage panel prose | blue-grey | light blue-grey |
| `--ws-accent` | Interactive / info highlight | muted blue | lighter muted blue |
| `--ws-accent-tint` | Accent background wash | low-alpha blue | low-alpha lighter blue |
| `--ws-accent-border` | Accent border / rule | medium-alpha blue | medium-alpha lighter blue |
| `--ws-accent-hover` | Accent interactive hover | darker blue | lighter hover blue |
| `--ws-disabled` | Disabled / placeholder | light grey | dark grey |
| `--ws-input-bg` | Input / textarea fill | near-white | near-black |
| `--ws-preview-bg` | Preview output fill | off-white tinted | very dark |
| `--ws-border` | General pane/section border | low-alpha black | low-alpha white |
| `--ws-border-thin` | Intra-list dividers | lighter-alpha black | lighter-alpha white |
| `--ws-border-strong` | Input / field border | medium-alpha black | medium-alpha white |
| `--ws-radius-md` | Default component radius | 8 px | 8 px |
| `--ws-radius-lg` | Section / card radius | 12 px | 12 px |

### 2.1 Dark Mode Strategy

Dark values are applied in two ways that cooperate without conflicting:

1. **OS preference** — `@media (prefers-color-scheme: dark) { :root:not([data-ws-theme="light"]) { … } }`
2. **Manual override** — `:root[data-ws-theme="dark"] { … }` applied via `localStorage`-backed
   `toggleWorkspaceTheme()` and `data-ws-theme` attribute on `<html>`.

The OS path is ignored when the user has set a manual preference. `Light mode` / `Dark mode`
button in the header reflects and stores the current state.

---

## 3. Information Architecture

### 3.1 Page Shell

```text
<header>
  Workspace · ← Dashboard · Studio · [spacer] · [Light/Dark mode]
<main class="ws-layout">
  <left-pane  id="ws-left-pane">   evidence cards
  <right-pane id="ws-right-pane">  target, coverage, preview
```

The two-pane grid is `320px | 1fr` on a viewport-height canvas.

### 3.2 Left Pane — Evidence Cards

```text
ws-pane-title  "Evidence cards"
ws-card-count  "{n} live cards"
ws-card-list   [ws-card-item …]
```

Each card item renders:

```text
[checkbox]  ws-card-content
              ws-card-body (label for checkbox)
                ws-card-pill    card.type
                ws-card-title   card.title
                ws-card-context card.summary  (clamped 2 lines)
                ws-card-meta    "{n} metrics · {n} evidence"
              ws-card-more    "Show full summary" / "Collapse summary"  (hidden if not truncated)
```

### 3.3 Right Pane — Target, Coverage, Preview

Three `ws-section` panels stacked vertically:

1. **Target** — organization, role, question/prompt, competency focus, job description
   (optional), output type radio (application answer / cover letter), char limit, blind hiring.
2. **Coverage** — `ws-coverage-panel` with:
   - `ws-coverage-value` — deterministic fit percentage or "—"
   - `ws-coverage-gap` — status/gap message
   - `ws-coverage-terms` — matched keyword excerpt (up to 6 terms)
3. **Preview** — `ws-generate-btn` and `ws-preview-out`.

---

## 4. Interaction States

| State | Trigger | Visual |
|---|---|---|
| Card hover | mouse enters `ws-card-item` | `--ws-accent-tint` background; `transition: background .12s` |
| Card selected | checkbox checked | `ws-card-selected` class; `--ws-accent-tint` background + `--ws-accent-border` border-color |
| Checkbox focus | keyboard tab | `outline: 2px solid var(--ws-accent)` on checkbox |
| Disclosure | `ws-card-more` button click | `.ws-card-context` gains `ws-card-context-expanded`; summary switches from `-webkit-line-clamp: 2` to `display: block` |
| Disclosure button | only when summary is truncated | hidden by default; revealed when `contextEl.scrollHeight > contextEl.clientHeight` |
| Generate button focus | keyboard tab | Browser default focus outline — no `.ws-generate-btn:focus-visible` rule exists; `.ws-theme-toggle:focus-visible` applies to the theme toggle only (see §8 Known Exceptions) |
| Theme toggle hover | mouse enters | border → `--ws-accent-border`; text → `--ws-accent` |

Card click propagation: `ws-card-more` calls `event.stopPropagation()` so disclosure does not trigger card-selection toggle.

---

## 5. Typography and Casing Rules

| Rule | Value |
|---|---|
| Font family | `system-ui, sans-serif` |
| Permitted weights | 400 (body), 500 (labels, titles, pills) |
| Prohibited weights | 600, 700 |
| Case | Sentence case throughout |
| Prohibited transform | `text-transform: uppercase` |
| Header font size | 0.95 rem (strong), 0.82 rem (links) |
| Pane title | 0.70 rem, weight 500, letter-spacing 0.03 em |
| Card title | 0.85 rem, weight 500 |
| Card context | 0.78 rem, weight 400 |
| Card meta / labels | 0.72 rem, weight 400 |

---

## 6. Accessibility Requirements

| Requirement | Implementation |
|---|---|
| Checkbox keyboard toggle | Native `<input type="checkbox">` — browser default |
| Checkbox focus ring | `:focus-visible` outline via CSS |
| Card label association | `<label for="ws-card-{id}">` sibling of checkbox |
| Disclosure button label | Text content: "Show full summary" / "Collapse summary" |
| Disclosure button `aria-controls` | References `ws-card-context-{id}` |
| Theme toggle `aria-pressed` | Reflects current `dark` / `light` state |
| Dark/light contrast | Token dark set targets acceptable contrast for primary text/surface pairs; not formally audited to WCAG AA yet |

---

## 7. Conformance Table (Cycle 30 baseline)

| Design rule | Implemented | Evidence |
|---|---|---|
| Sentence-case labels | ✅ | `test_workspace_html_no_uppercase_transform` |
| No font-weight 600/700 | ✅ | `test_workspace_html_no_font_weight_600/700` |
| `:root` token block | ✅ | `test_workspace_html_has_token_*` (Cycle 28) |
| All accent/surface values tokenized | ✅ (see §8 for one-off exception) | `test_workspace_html_no_raw_rgba_accent_outside_root` (Cycle 28) |
| Dark OS media query | ✅ | `test_workspace_html_has_dark_media_query` |
| Manual dark toggle | ✅ | `test_workspace_html_has_theme_toggle_button` / `test_workspace_js_theme_uses_local_storage` |
| Card hover state | ✅ | `test_workspace_html_card_hover_state_exists` |
| Card selected state | ✅ | `test_workspace_html_card_selected_state_exists` |
| Checkbox focus-visible ring | ✅ | `test_workspace_html_card_focus_visible_state_exists` |
| Card disclosure (line-clamp + toggle) | ✅ | `test_workspace_html_card_context_uses_line_clamp` |
| Disclosure stops propagation | ✅ | `test_workspace_js_disclosure_stops_selection_click` |
| Overflow containment | ✅ | `test_workspace_html_card_content_constrains_width` |
| Fit percentage formula | ✅ — source only | `test_workspace_js_has_update_coverage_function` |
| Matched-terms output | ✅ — source only | `test_workspace_html_has_coverage_terms_hook` |
| No-persistence guarantee | ✅ | `test_workspace_does_not_create_card_file` |
| WCAG AA contrast (dark) | ⏳ PENDING | Browser/manual check required |
| Keyboard navigation end-to-end | ⏳ PENDING | Browser/manual check required |

---

## 8. Known Exceptions (Documented Deviations)

| Exception | Scope | Rationale | Follow-up |
|---|---|---|---|
| `color: #fff` on `.ws-generate-btn` | Generate button foreground text | Single-use value (not a repeated color); white-on-accent is universally understood. `--ws-btn-text` token not yet added. | Add token in a future design-polish cycle (DEBT-006). |
| No `.ws-generate-btn:focus-visible` rule | Generate button keyboard focus | Browser default outline is visible; custom styling deferred. | Add rule alongside the token in a future cycle. |

These exceptions do not invalidate the token-driven principle — the principle targets
*repeated* color roles. They are documented here to prevent false conformance claims in
future audit cycles.

---

## 9. Future Direction (Not Yet Implemented)

The following capabilities are described in `landing.md` but are **not** part of the
current implementation. They must not be described as implemented in requirements or
acceptance documents.

| Feature | Planning reference |
|---|---|
| Theme / competency extraction from card text (S1 AI tagging) | `landing.md` §2 S1 |
| Set-coverage matching (`match = |covered_required_themes| / |required_themes|`) | `landing.md` §2 S2 |
| Gap-hint recommendation (missing theme → suggest card) | `landing.md` §7.1 |
| STAR card expansion (S/T/A/R 4-row disclosure) | `landing.md` §7.1 |
| Command palette for card search/select | `landing.md` §6 |
| Filter chips: All / Recommended only | `landing.md` §7.1 |
| Depth-driven slide count for portfolio | `landing.md` §4 |
| Resume / portfolio output from Workspace | future cycle |

`landing.md` remains an **untracked planning artifact**. It is not a canonical requirement
document and must not be staged or referenced as normative unless explicitly promoted.
