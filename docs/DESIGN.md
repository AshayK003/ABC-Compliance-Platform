---
name: Digital Sovereign
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#bcc9c6'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#879391'
  outline-variant: '#3d4947'
  surface-tint: '#6bd8cb'
  primary: '#6bd8cb'
  on-primary: '#003732'
  primary-container: '#29a195'
  on-primary-container: '#00302b'
  inverse-primary: '#006a61'
  secondary: '#b9c7e0'
  on-secondary: '#233144'
  secondary-container: '#3c4a5e'
  on-secondary-container: '#abb9d2'
  tertiary: '#bec6e0'
  on-tertiary: '#283044'
  tertiary-container: '#8990a8'
  on-tertiary-container: '#22293d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  code-sm:
    fontFamily: monospace
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  element-gap: 8px
  table-cell-padding: 12px 16px
---

## Brand & Style

This design system is built for mission-critical government compliance and high-density data monitoring. The brand personality is authoritative, transparent, and unwavering. It prioritizes information throughput over aesthetic flourish, ensuring that compliance officers can identify irregularities at a glance.

The design style is **Modern Corporate** with a heavy emphasis on **Functional Minimalism**. It utilizes a dark, high-contrast environment to reduce eye strain during long shifts and to make status-driven color indicators (alerts, warnings) pop with maximum visual urgency. The aesthetic is "Tool-first," favoring precision, structured grids, and a systematic density that feels reliable and institutional.

## Colors

The palette is anchored by **Deep Teal (#0D9488)**, chosen for its association with stability and sophisticated governance. The background architecture uses a tiered Slate scale to create environmental depth without relying on shadows.

- **Primary:** Deep Teal for primary actions and active states.
- **Surface Levels:** The base background is `#020617`. Elevated surfaces like tables or cards use `#0F172A`.
- **Borders:** Subtle borders use `#1E293B` to define zones without creating visual noise.
- **Status Colors:** Standardized Green/Amber/Red are used exclusively for compliance status and system health to maintain their semantic power.

## Typography

The system utilizes **Inter** for its exceptional legibility in high-density data environments.

- **Scale:** Type sizes are kept relatively small (13px–14px for body) to maximize the information visible on-screen at once.
- **Hierarchy:** High-contrast weighting (Semibold/Bold) is used for headers to clearly distinguish sections in a complex dashboard.
- **Data Display:** For tabular data and numerical figures, tabular lining (tnum) should be enabled to ensure numbers align vertically for easy comparison.
- **Labels:** Small caps with slight tracking are used for secondary metadata to differentiate it from primary body text.

## Layout & Spacing

This design system uses a **Fluid Grid** with a 4px baseline rhythm. The layout is designed for 1440px+ screens but scales down to 1024px for tablet use.

- **Density:** High-density spacing is the priority. Margins between data elements are kept tight (8px-12px) to reduce scrolling.
- **Grid:** A 12-column grid system is used for dashboard layouts. Sidebars are fixed at 240px to maximize the flexible workspace for data tables.
- **Alignment:** All elements are strictly aligned to the grid to project a sense of order and institutional precision.
- **Reflow:** On smaller viewports, cards move from horizontal multi-column layouts to single-column stacks, but data tables maintain horizontal scroll to preserve row integrity.

## Elevation & Depth

In this dark government theme, elevation is communicated through **Tonal Layers** rather than shadows. This minimizes visual clutter and maintains a "flat" professional look.

- **Base Layer:** Background (`#020617`).
- **Surface Layer:** Cards, table headers, and sidebar navigation use `#0F172A`.
- **Interactive Layer:** Hover states use a slightly lighter `#1E293B` or a low-opacity Deep Teal overlay.
- **Separators:** 1px solid borders in `#1E293B` are the primary method of separation.
- **Shadows:** Avoid shadows on standard UI elements. Use a single, high-blur ambient shadow only for floating modals or dropdown menus to distinguish them from the main layout.

## Shapes

The shape language is **Soft/Precise**. A 4px (0.25rem) radius is the standard for almost all components, providing a subtle modern feel without looking "bubbly" or informal.

- **Small Components:** Buttons, inputs, and checkboxes use a 4px radius.
- **Containers:** Dashboard cards and modals use an 8px (0.5rem) radius to provide a clear container hierarchy.
- **Status Badges:** Use a "Pill" shape (fully rounded) to differentiate them from interactive buttons.

## Components

- **Data Tables:** The core of the system. Rows have 1px bottom borders. Headers are sticky with a distinct `#0F172A` background. Text is high-contrast white/off-white for readability.
- **Stat Cards:** Feature a large "Display" value, a small "Label-bold" title, and a trend indicator (Green/Red text). No background icons; keep them strictly numerical.
- **Buttons:**
    - *Primary:* Solid Deep Teal with white text.
    - *Secondary:* Outline (1px) in Slate-700.
    - *Destructive:* Solid Red only for irreversible compliance actions.
- **Status Badges:** Subtle background tint (10% opacity) with high-contrast text of the same hue (e.g., Light Green text on Dark Green tint).
- **Input Fields:** Dark backgrounds (`#020617`) with 1px borders. Focused state uses a 2px Deep Teal border.
- **Lists:** Clean, no-bullet style. Items are separated by 8px of vertical space or 1px dividers in high-density views.
