# Design System & UI Guidelines (`design.md`)

## 1. Aesthetic Direction
- **Vibe:** High-craft dark UI, sleek, engineering-grade, modern SaaS/Portfolio aesthetic (inspired by Linear, Vercel, and Raycast).
- **Core Principles:** Subtle depth over loud colors, crisp 1px borders, atmospheric radial glows, Bento-grid layouts, and tactile micro-interactions.

## 2. Color Palette (Dark Mode First)
- **Background Primary:** `#09090B` (Deep Zinc)
- **Background Elevated / Surface:** `#121215` (Card & container background)
- **Glass Surface:** `rgba(24, 24, 27, 0.65)` with `backdrop-filter: blur(12px)`
- **Text Primary:** `#FAFAFA` (Crisp alabaster for headings and key copy)
- **Text Secondary:** `#A1A1AA` (Muted zinc for body text and descriptions)
- **Text Muted:** `#52525B` (Captions, metadata, disabled states)
- **Accent Primary:** `#6366F1` (Indigo) to `#8B5CF6` (Violet) subtle gradients
- **Accent Secondary / Glow:** `#38BDF8` (Sky cyan for highlights, badges, and active indicators)
- **Borders:** `rgba(255, 255, 255, 0.08)` default; `rgba(255, 255, 255, 0.18)` on hover.

## 3. Typography
- **Headings:** `'Inter'`, `'Plus Jakarta Sans'`, or `'Geist'` — SemiBold/Bold (`600`/`700`), tight letter-spacing (`-0.03em`), line-height `1.15`.
- **Body:** `'Inter'` — Regular (`400`), line-height `1.6`, max line width `65ch` for readability.
- **Monospace (Code, tags, metrics, timestamps):** `'JetBrains Mono'` or `'Fira Code'` — `0.85rem`, uppercase tracking (`0.05em`) for badges.
- **Scale:**
  - Hero Title: `clamp(2.5rem, 5vw, 4.25rem)`
  - Section Header: `clamp(1.75rem, 3vw, 2.5rem)`
  - Card Title: `1.25rem` (`20px`)
  - Body: `1rem` (`16px`)

## 4. Layout & Spatial Architecture
- **Container:** Max-width `1200px`, centered, with `1.5rem` (`24px`) horizontal padding on mobile and `3rem` (`48px`) on desktop.
- **Grid System:** Asymmetric Bento Grid (`grid-template-columns: repeat(12, 1fr)`, gap `1.5rem`) for features, projects, or stats instead of uniform 3-column rows.
- **Whitespace:** Minimum `6rem` (`96px`) vertical padding between major sections.
- **Visual Anchors:** Place a subtle background radial gradient (`radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.14), transparent 60%)`) at the top of the viewport and behind key focal sections.

## 5. Component Specifications
- **Navigation Bar:** Sticky top, floating pill or full-width glass bar (`backdrop-filter: blur(16px)`), `1px solid rgba(255, 255, 255, 0.08)` bottom border.
- **Cards (Bento Cells):**
  - Border radius: `16px` (`1rem`)
  - Background: `linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.0) 100%)` over `#121215`
  - Border: `1px solid rgba(255, 255, 255, 0.07)`
  - Inner Padding: `1.75rem` (`28px`)
  - Hover State: `transform: translateY(-3px)`, border brightens to `rgba(255, 255, 255, 0.18)`, subtle box-shadow `0 20px 40px -15px rgba(0,0,0,0.6)`.
- **Buttons:**
  - *Primary:* Pill or `10px` radius, high-contrast `#FAFAFA` background with `#09090B` text, or Indigo accent with a subtle top inner-highlight (`box-shadow: inset 0 1px 0 rgba(255,255,255,0.25)`).
  - *Secondary:* Glass background `rgba(255,255,255,0.04)`, `1px solid rgba(255,255,255,0.1)`, `#FAFAFA` text, brightens on hover.
- **Badges / Pills:** Monospace font, `12px`, `padding: 4px 10px`, border-radius `9999px`, background `rgba(99, 102, 241, 0.12)`, border `1px solid rgba(99, 102, 241, 0.3)`, text `#818CF8`.

## 6. Motion & Micro-Interactions
- **Transitions:** Use smooth spring-like easing: `transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1)`.
- **Interactive Feedback:** Every clickable element must have a distinct `:hover`, `:focus-visible`, and `:active` (`scale(0.98)`) state.
- **Background Texture:** Optional subtle dot-matrix or 1px grid background pattern masked with a radial gradient so it fades out smoothly toward the edges.
