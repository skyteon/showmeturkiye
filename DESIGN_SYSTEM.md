# Show Me Türkiye - Design System

**Reference document for all pages**
*Last updated: 2026-05-09*

---

## PHILOSOPHY

Premium editorial travel guide. Cereal Magazine + Off Paris adjacent. Six Senses krem palette + Türkiye karakteri (pomegranate red, brass gold accent, sandstone tones).

**Brand strategy: A%70 + B%30**
- A (%70) = "Show Me Türkiye" brand voice, kollektif "we", content-first
- B (%30) = Halil Bekar founder voice, only in Cities Spotlight quote (anlamlı kişisel observation)
- SEO/JSON-LD/Twitter cards retain founder info (background authority)

---

## 1. COLOR PALETTE

8 colors, 3 families. Premium minimal scale (Aman, Six Senses, Cereal Magazine pattern).

### Variables (`:root`)
```css
--cream:#F4EFE5;            /* Six Senses krem - main bg */
--cream2:#E8DFCD;           /* Yalı cephe sıvası - alternating sections */
--white:#FAF5EA;            /* Mermer iç ışık - cards */
--gold:#C9A75D;             /* Brass gold - dark bg italic em ONLY (3 places) */
--black:#1a0e0a;            /* Deepest wine - footer */
--text:#2A1410;             /* Deep wine - body + headlines */
--text-muted:#5C3530;       /* Wine-stone - secondary (AAA contrast) */
--text-inv:rgba(244,239,229,0.55);   /* Footer secondary on dark */
--text-inv2:rgba(244,239,229,0.78);  /* Footer body on dark */
--brown:#C0392B;            /* Pomegranate - all reds (45+ uses) */
--serif: 'Playfair Display', Georgia, serif;
--sans: 'Poppins', system-ui, sans-serif;
```

### Hardcoded backgrounds (not in `:root`)
- Cinematic guide section: `#E5DBC0` (açık taş)
- Routes section: `#D9CCB1` (koyu sand)
- Hero: `#1C1814` (cinematic photo overlay)

### Color usage rules

**Pomegranate `#C0392B` (brand red, single accent)**
- All buttons (primary + ghost hover)
- All italic em vurgular on light bg
- All link hovers
- Cinematic guide pattern stroke
- Map dots/icons
- "Long read" badge, IG handle, progress bars
- Logo brand red `#9E1012` lives ONLY in logo image, NEVER in CSS

**Brass gold `#C9A75D`** — Türkiye karakter parıltısı
- ONLY 3 places (all on dark backgrounds):
  1. Hero h1 italic em "easier"
  2. Slide num em
  3. Footer newsletter h3 em "the road"
- Never on light bg, never elsewhere

**Italic em on light bg:** `color: var(--brown)` (pomegranate)
**Italic em on dark bg:** `color: var(--gold)` (brass gold) — Türkiye parıltısı

### Section background mapping
| # | Section | Background | Karakter |
|---|---------|------------|----------|
| 1 | Hero | `#1C1814` | Cinematic dark photo (1. dramatic moment) |
| 2 | Cinematic guide | `#E5DBC0` | Açık taş (ferah karakterli) |
| 3 | Routes | `#D9CCB1` | Koyu sand (alternating) |
| 4 | Cities | `var(--cream)` | Six Senses krem |
| 5 | Films/Projects | `var(--cream2)` | Yalı cephe sıvası |
| 6 | Blog/Journal | `var(--cream)` | Six Senses krem |
| 7 | Instagram | `var(--cream2)` | Yalı cephe sıvası |
| 8 | Footer | `var(--black)` | Deepest wine (2. dramatic moment) |

**2 dark moment kuralı:** Hero + Footer. Sayfanın 2 ucu dark, ortası ferah krem editorial flow. Cinematic guide artık dark değil — ferah taş zemin.

### Opacity scale (premium consistency)

**Cream on dark bg (footer, hero):**
| Opacity | Usage |
|---------|-------|
| 0.95 | Primary text |
| 0.78 | Body text |
| 0.55 | Secondary, captions |
| 0.40 | Tertiary, slide num |
| 0.18 | Border on dark |
| 0.10 | Hairline divider on dark |

**Wine ink on light bg:**
| Opacity | Usage |
|---------|-------|
| 0.18 | Strong border |
| 0.12 | Standard border, card edge, stat divider |
| 0.08 | Hairline divider, subtle |
| 0.05 | Bottom gradient overlay |

---

## 2. TYPOGRAPHY

### Fonts (only 2)
- `--serif: 'Playfair Display'` (headlines, italic em)
- `--sans: 'Poppins'` (body, UI, eyebrows, CTAs)

### Size scale
| Level | Size | Use |
|-------|------|-----|
| Hero h1 | `clamp(44px, 6.8vw, 96px)` | Hero only |
| Section h2 | `clamp(32px, 4vw, 52px)` | All section headers |
| Cinematic guide h3 | `clamp(48px, 5.4vw, 76px)` | Cinematic guide section only |
| Featured h3 | `clamp(28px, 3vw, 38px)` | Blog featured, route titles |
| Card title | 22-24px | Cards |
| Body large | 16-17px | Hero sub, intro |
| Body | 14-15px | Default |
| Body small | 13px | Card descriptions |
| Eyebrow | 11px | All eyebrows, labels |
| Meta | 10-11px | Tracking, metadata |

### Weight
- 400 (regular) - body, italic em
- 500 (medium) - eyebrows, CTAs, nav, headlines
- Skip 300 (poor readability) and 600+ (too heavy)

### Letter-spacing
- Headlines: `-0.012em` to `-0.018em` (tight)
- Body: `0`
- Eyebrows: `0.22em`
- CTA buttons: `0.18em` to `0.30em`

### Line-height
- Headlines: `1.04` to `1.10`
- Body: `1.65` to `1.75`
- Cards: `1.45` to `1.60`

### Italic em rules
- **Min size 22px** for Playfair italic. Below that use Poppins italic OR no italic.
- **`white-space: nowrap`** ALWAYS on italic em phrases (prevents ugly mid-phrase line breaks).
- Italic em never on CTA buttons (always Poppins uppercase).

---

## 3. CTA STANDARDIZATION

**Tek standart**: Poppins, uppercase, never italic.

### Primary pill (filled)
```css
display: inline-flex;
align-items: center;
gap: 14px;
padding: 18px 44px;
background: var(--text);  /* veya var(--brown) */
color: var(--cream);
border-radius: 999px;
font-family: var(--sans);
font-size: 12px;
font-weight: 500;
letter-spacing: 0.30em;
text-transform: uppercase;
```

### Ghost pill (outline)
```css
border: 1px solid var(--text);
background: transparent;
color: var(--text);
/* hover: */
background: var(--brown);
color: var(--cream);
border-color: var(--brown);
```

### Inline link CTA
```css
font-family: var(--sans);
font-size: 13px;
font-weight: 500;
letter-spacing: 0.18em;
text-transform: uppercase;
color: var(--text);
/* hover: color var(--brown) */
```

### Arrow (`<span class="arr">→</span>`)
- Always `→` (right arrow), no other glyphs
- Hover: `transform: translateX(4px)` (gap increases)
- Transition: `0.35s ease`

---

## 4. BRAND VOICE & WRITING

### Voice hierarchy (3 tiers)
1. **1st person plural "we"** (brand collective)
   - "We've gathered them all..."
   - "Our travel"
   - "we'd send a friend"
2. **2nd person "you"** (direct user)
   - "Your questions, local answers"
   - "before you arrive"
   - "Pick your Türkiye"
3. **3rd person observational** (premium publication)
   - "From across Türkiye"
   - "Built on the road"
   - "Hidden gems"

**Halil quote** = single founder voice instance (Cities Spotlight only).

### NO PROMISES rule (premium pattern)
Show Me Türkiye delivers when content earns publish, not on schedule.

❌ NEVER use:
- "Updated weekly", "Daily posts", "Monthly stories"
- "Every day/week/month/year"
- "Guarantee", "Promise", "Always"
- "Forever", "365 days"

✓ Use flexible, samimi:
- "Updated as we travel"
- "From the field"
- "When we're moving"
- "Stories from across Türkiye"
- "Built on the road"

### Halil mention rules (A%70+B%30)
✓ Cities quote attribution: "Halil Bekar · Founder, Show Me Türkiye" (1 yer, founder voice)
✓ JSON-LD founder, meta author, Twitter creator (background SEO)
❌ Blog byline "By Halil Bekar" — DON'T USE
❌ Footer credit "by Halil Bekar" — use "by Show Me Türkiye Team"
❌ Hero "filming Türkiye" / "years of experience" — use "across Türkiye" or content-first

### Word substitutions
| ❌ Avoid | ✓ Prefer |
|---------|----------|
| Tourist | Traveler / visitor / you |
| Discover, embark on, immerse | (just say it directly) |
| Dive into our cinematic universe | Films from across Türkiye |
| Updated weekly | Updated as we travel |
| Daily frames | Stories |
| Filming Türkiye | Across Türkiye / on the road |
| For the slow traveler (niche label) | For travelers (inclusive) |

### Brand pillars (3 ürün tipi)
**Routes / Films / Guides** — sayfada her yerde tutarlı:
- Hero eyebrow: "Routes · Films · Guides from Türkiye · Since 2018"
- Hero sub: "Routes, guides, and films from years of travel across Türkiye."

**Stories** ≠ brand pillar. Stories = **content tipi** (blog narrative içerik):
- Blog masthead "told in stories"
- Blog archive "All stories · City guides · Field notes"
- IG section "Stories from across Türkiye"

### Forbidden punctuation
- ❌ Em dash (—) anywhere
- ❌ En dash (–) anywhere
- ✓ Hyphen (-)
- ✓ Middle dot (·) for separators (premium editorial pattern)
- ✓ Period (.)

### Number rule
**No specific numbers in marketing copy.**
- ❌ "26 cities", "Twelve routes", "Seven years"
- ✓ "Curated routes", "city guides", "years of travel across Türkiye"
- Exception: article meta ("8 min read", "3 days · 4 cities") tied to specific content

### Niche audience labels rule
**No "for the X traveler" framings.**
- ❌ "For the slow traveler", "For digital nomads", "Adventure seekers"
- ✓ "For travelers", "For your trip", "Stories from across Türkiye"
- Inside specific routes/articles you can speak to specific audiences ("best for families"), but homepage/intros stay broad.

---

## 5. SPACING SYSTEM

### Section padding (vertical)
- Desktop: `130px` top/bottom (premium dense pacing)
- Mobile: `64-96px`
- Cinematic guide bottom: `140px`
- IG section: `140px`

### Section header → content
- Desktop: `80-96px` margin-bottom
- Mobile: `48-64px`

### Component spacing (8px base)
- Tight: 8px
- Default: 16px
- Comfortable: 24px
- Generous: 32px
- Section: 48-64px
- Hero: 80-120px

### Container max-widths
- Tight (text content): `680-780px`
- Standard: `1320px`
- Wide (carousels): `1400-1600px`

---

## 6. BORDER-RADIUS

3 değer (Linear-style restraint):
- `4px` - chips, small UI
- `12px` - cards, modals
- `999px` - pills (buttons, dots, badges)

---

## 7. SHADOWS

### Card on cream bg (3-layer warm)
```css
box-shadow:
  inset 0 0 0 1px rgba(42,20,16,0.06),
  0 1px 2px rgba(42,20,16,0.05),
  0 8px 24px rgba(42,20,16,0.07),
  0 24px 56px rgba(42,20,16,0.05);
```

### Hover (deeper + accent ring)
```css
box-shadow:
  inset 0 0 0 1.5px var(--brown),
  0 2px 4px rgba(42,20,16,0.06),
  0 20px 48px rgba(42,20,16,0.14),
  0 48px 112px rgba(42,20,16,0.12);
transform: translateY(-8px);
```

### Subtle UI (nav buttons, pills)
```css
box-shadow:
  0 2px 4px rgba(42,20,16,0.06),
  0 8px 20px rgba(42,20,16,0.08);
```

---

## 8. ANIMATION

### Easing
- Premium: `cubic-bezier(.22,.61,.36,1)` (Apple/Linear)
- Default: `cubic-bezier(0.4,0,0.2,1)`

### Duration
- Micro (hover): `0.25-0.35s`
- Transition: `0.4-0.6s`
- Reveal: `0.9-1.0s`

### Reveal classes
- `.reveal-up` - single block fade up (28px translate)
- `.reveal-stagger > *` - children stagger (80ms delay each, max 720ms)
- `.reveal-header` - eyebrow → title → subtitle cascade

### IntersectionObserver
```js
threshold: 0.12,
rootMargin: '0px 0px -8% 0px'
```

### `prefers-reduced-motion`
All animations have `@media (prefers-reduced-motion: reduce) { ... }` fallback.

---

## 9. CORE COMPONENTS

### Eyebrow
```html
<div class="eyebrow">CATEGORY · CONTEXT</div>
```
```css
font-family: var(--sans);
font-size: 11px;
font-weight: 500;
letter-spacing: 0.22em;
text-transform: uppercase;
color: var(--text-muted);
margin-bottom: 24px;
```

### Section header pattern
```html
<div class="section-header reveal-header">
  <div class="eyebrow">Section · Subtitle</div>
  <h2>Headline with <em>italic emphasis</em>.</h2>
  <p>One-sentence subtitle (max 50ch).</p>
</div>
```

### Card (premium)
- Background: `var(--white)` (cream-white, never pure white)
- Border-radius: 12px
- 3-layer warm shadow
- Hover: 8px lift + pomegranate inset ring + deeper shadow

### Carousel dot indicator (Films pattern)
```html
<div class="carousel-dots">
  <button class="carousel-dot is-active"></button>
  <button class="carousel-dot"></button>
</div>
```
```css
.carousel-dot {
  width: 8px; height: 8px;
  border-radius: 999px;
  background: rgba(42,20,16,0.18);
}
.carousel-dot.is-active {
  background: var(--brown);
  width: 28px;  /* expand on active */
}
```

---

## 10. PATTERN USAGE (Türkiye motifs)

Cinematic guide section'da SVG repeating pattern var:
- Türk objeler: nazar, lale, çay bardağı, kubbe (cami), kedi, kahve fincanı, balık
- Stroke: `#C0392B` pomegranate brand red
- Stroke-width: `1.2`
- Opacity: `0.10` (subtle, fark edilir ama göz yormaz)
- Background-size: 800px × 800px, repeating

**Pattern kuralı:** Sadece **cinematic guide section'ında** kullanılır. Diğer section'lar pattern'siz, temiz tipografi + whitespace.

---

## 11. ACCESSIBILITY

### Required
- `<html lang="en">` veya appropriate
- All `<img>` have `alt` (decorative: `alt=""`)
- Interactive elements have `aria-label` if no visible text
- Min font-size 11px (eyebrows), 13px (body) on cream bg
- Contrast: text on cream `15.8:1`, text-muted on cream `7.8:1` (AAA)
- Focus states visible
- `prefers-reduced-motion` honored
- **Touch targets min 44x44px** (Apple HIG, see Section 12 Mobile)

---

## 12. MOBILE OPTIMIZATION

Premium responsive design. Mobile-first değil, **mobile-respected** (desktop-designed, mobile-optimized).

### Viewport meta (required)
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### Breakpoint system (3 tier)
| Breakpoint | Use case |
|-----------|----------|
| `max-width: 900px` | Tablet portrait, asymmetric grids → 1 column |
| `max-width: 768px` | Mobile landscape, default mobile |
| `max-width: 480px` | Small mobile, edge cases (iPhone SE) |

**Tutarlılık kuralı:** Yeni component'ler bu 3 breakpoint'i kullanır. 600px, 640px, 760px, 1024px gibi rastgele değerler **kullanma**.

### Body & html mobile setup
```css
html { scroll-behavior: smooth; }
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-tap-highlight-color: transparent;  /* iOS gri kutuyu kaldır */
}
```

### Touch targets (Apple HIG / Material)
- **Minimum 44x44px** tüm interactive elementlerde
- Hamburger: `min-width: 44px; min-height: 44px`
- Carousel dots (görsel 8px) → padding ile **36x36 tap area**:
```css
.carousel-dot {
  width: 8px;
  height: 8px;
  padding: 14px;
  background-clip: content-box;  /* görsel 8px, tap 36x36 */
  box-sizing: content-box;
}
```
- Buttons min height 44px (mevcut pill button'lar 48-52px ✓)

### Form inputs — iOS zoom önle
**iOS Safari `font-size < 16px` olan input'larda otomatik zoom yapar.** Bu **bilinen UX sorunu**.

```css
/* TÜM input/textarea minimum 16px font-size */
input[type="text"],
input[type="email"],
input[type="search"],
textarea {
  font-size: 16px;
}
```

### Padding ölçek (mobile-down)
| Section element | Desktop | Mobile (768px) | Small (480px) |
|----------------|---------|----------------|---------------|
| Section padding (top/bottom) | 130px | 80-96px | 64px |
| Section horizontal | 40px | 16-24px | 16px |
| Card padding | 32px | 24px | 16-20px |
| Hero | 0 7% 110px | 0 7% 90px | 0 7% 80px |

### Typography mobile scale
| Level | Desktop | Mobile (768px) |
|-------|---------|----------------|
| Hero h1 | `clamp(44px, 6.8vw, 96px)` | `clamp(40px, 9vw, 60px)` |
| Section h2 | `clamp(32px, 4vw, 52px)` | `clamp(28px, 7vw, 36px)` |
| Cinematic guide h3 | `clamp(48px, 5.4vw, 76px)` | `clamp(34px, 8.5vw, 52px)` |
| Body | 14-16px | 14-15px |
| Body small | 13px | 12-13px |

**Body asla 12px altına inmez.** Eyebrow 10-10.5px sınırlı durumlarda kabul edilir.

### Layout mobile-down patterns

**Asymmetric grid → single column (`max-width: 900px`):**
```css
.cities-spotlight {
  grid-template-columns: 1.45fr 1fr;
}
@media (max-width: 900px) {
  .cities-spotlight {
    grid-template-columns: 1fr;
    gap: 48px;
  }
}
```

**3D carousel → single card (`max-width: 768px`):**
```css
@media (max-width: 768px) {
  #leftCard, #rightCard { display: none !important; }
  #centralCard { width: 88% !important; }
}
```

**Stats row → vertical stack (`max-width: 760px`):**
```css
@media (max-width: 760px) {
  .guide-stats {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .guide-stat:not(:last-child)::after { display: none; }  /* dikey divider sil */
  .guide-stat:not(:last-child) {
    border-bottom: 1px solid rgba(42,20,16,0.12);
    padding-bottom: 20px;
  }
}
```

**Footer grid → 2 column (`max-width: 768px`):**
```css
.footer-content {
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}
```

### Mobile navigation
- **Hamburger always visible** (desktop + mobile, premium pattern)
- Fullscreen overlay menu on click
- Escape key closes menu
- Logo + Hamburger only on scroll (compact)

### Mobile testing checklist
- [ ] Hero h1 readable (40-60px range)
- [ ] All inputs `font-size: 16px+` (no iOS zoom)
- [ ] Tap targets min 44x44px
- [ ] Carousels swipeable / draggable
- [ ] Carousel dots tap-targetable (padded)
- [ ] No horizontal overflow at 320px width
- [ ] Reveal animations work but not too jumpy
- [ ] `prefers-reduced-motion` respected
- [ ] Hamburger menu opens/closes smoothly
- [ ] All section padding tightens (130 → 80-96)
- [ ] Image aspect ratios preserved
- [ ] Text doesn't truncate / overflow
- [ ] Italic em phrases use `white-space: nowrap` (no mid-phrase break)

### Common mobile pitfalls (avoid)
1. **`!important` overuse** — only use when overriding 3rd party. Mevcut kod 768px'de `!important` kullanıyor (ai chat kalıntısı), audit edilebilir
2. **Tiny fonts** — eyebrow 10px sınırı, body 12px sınırı
3. **Hover-only interactions** — mobile no hover, ensure tap-equivalent
4. **Fixed widths** — use `clamp()`, `min()`, `max()`, vw/vh
5. **Disabled zoom** — never `user-scalable=no` (accessibility violation)

---

## 13. SEO + META TAGS (per-page)

```html
<title>Page Title | Show Me Türkiye</title>
<meta name="description" content="...">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:image" content="https://img.showmeturkiye.com/og/page-name.jpg">
<meta property="og:url" content="...">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="...">
<meta name="author" content="Halil Bekar">
```

OG image: **1200×630px**. Custom one per page (don't reuse hero).

---

## 14. STICKY NAVIGATION

`.site-nav` on every page:
- Logo (left)
- Desktop menu: Home, Cities, Routes, Journal, Films, About
- "Plan a trip" CTA pill (right)
- Mobile hamburger
- `.scrolled` class after 80px scroll
- Default: transparent + cream text (cinematic hero compatibility)
- Scrolled: cream bg + deep wine text + soft shadow

For pages without dark hero: add `.site-nav.scrolled` by default in HTML.

---

## 15. INNER PAGE PATTERNS

### Page hero (non-homepage)
- Height: 50vh (not 100vh)
- Single eyebrow + h1 + intro
- Optional bg photo or solid sandstone
- Ghost pill CTA below

### Breadcrumb
```html
<nav class="breadcrumb">
  <a href="/">Home</a> <span>·</span>
  <a href="/cities">Cities</a> <span>·</span>
  <span>Istanbul</span>
</nav>
```

### Footer
Standardized footer block (copy-paste):
- Newsletter signup band (dark bg, brass gold em "the road")
- Brand pillars + links
- Copyright "by Show Me Türkiye Team"

---

## 16. CINEMATIC GUIDE SECTION BLUEPRINT

Reusable on inner pages? **No** — homepage only. Inner pages get their own cinematic moment via hero.

### Structure
```html
<section class="guide-sec">
  <div class="guide-cta-wrap">
    <div class="guide-cta-body">
      <div class="eyebrow">First time in Türkiye</div>
      <h3>
        <span class="lead">Coming to Türkiye?</span>
        <em>Read before you arrive.</em>
      </h3>
      <p>Visas, money, transport, food, etiquette. The kind of things a local friend would tell you over a slow coffee.</p>
      <div class="guide-stats">
        <div class="guide-stat"><span class="v">Built on the road</span></div>
        <div class="guide-stat"><span class="v">Updated as we travel</span></div>
        <div class="guide-stat"><span class="v">Your questions, local answers</span></div>
      </div>
      <a href="/guide" class="guide-cta-link">
        Read the full guide <span class="arr">→</span>
      </a>
    </div>
  </div>
</section>
```

### Voice notes
- H3 lead = soru (Coming to Türkiye?)
- H3 italic em = dramatic answer (Read before you arrive.)
- Body = somut açıklama (visas, money, transport...)
- Stats = 3 farklı voice tier (3rd person / 1st we / 2nd you)
- CTA = clear action

---

## 17. CITIES SPOTLIGHT SECTION

### Structure
```html
<div class="cities-spotlight">
  <div class="cities-map-wrap">
    <div class="cities-map-eyebrow">From sea to sea, region by region</div>
    <div class="cities-map-subtitle">
      <em>From the Aegean coast to the Caucasus border. Many worlds, one country.</em>
    </div>
    <svg class="cities-map">...</svg>
  </div>

  <blockquote class="cities-quote">
    <span class="cities-quote-mark">"</span>
    <p>Türkiye doesn't have <em>one story</em>. Every region brings...</p>
    <footer class="cities-quote-footer">
      <span class="cities-quote-author">Halil Bekar</span>
      <span class="cities-quote-role">Founder, Show Me Türkiye</span>
    </footer>
  </blockquote>
</div>
```

### Layout
- Desktop: `grid-template-columns: 1.45fr 1fr` (map left, quote right)
- Mobile (< 900px): single column, quote stacks below map
- Gap: 72px

### Map decluttering rules
Two-tier hierarchy:
- **Region label** (MARMARA, EGE, etc.): 10px, weight 500, uppercase, opacity 0.7 (ana)
- **Product label** ("mosques & the strait", "olives & sun"): 9px italic, opacity 0.5 (alt katman, subtle)
- Region icons: brand red `#C0392B`
- City dots: brand red, hover scale 1.4

---

## 18. FILMS SECTION (3D carousel)

### Header voice
- Eyebrow: "Field films · A selection" (premium travel publication term)
- H2: "Films that take you *there*."
- Body: "Short cinematic films from across Türkiye. Each one a place worth knowing."

### Components
- 3D carousel (left card / central card / right card)
- Prev/Next nav buttons (absolute positioned)
- 5-dot indicator below (`carousel-dots` component)
- "Watch more films →" CTA at bottom (links to films.html when ready)

### JS contract
- `currentIndex` state
- `updateCarousel()` - updates 3 card images + active dot
- `changeVideo(direction)` - prev/next button handler
- `goToVideo(index)` - dot click handler

---

## 19. NOTES FOR IMPLEMENTATION

1. **Single source of truth**: `:root` variables in main CSS. Don't duplicate hex values.
2. **No CSS variables in SVG attributes**: SVG `fill="..."` doesn't support `var()`. Use hex.
3. **Class naming**: BEM-light (e.g. `route-card`, `route-card-image`, `route-card-title`).
4. **JavaScript modules**: keep init functions named (`initHeroSlideshow`, `initCitiesRail`, `updateCarousel`, etc.) for reuse.
5. **Reveal classes**: apply `.reveal-up`, `.reveal-stagger`, `.reveal-header` liberally on dynamic content.
6. **Always check live**: After every change, view in browser before declaring done.

---

## 20. CHECKLIST FOR NEW PAGES

### Visual / Brand
- [ ] `:root` variables match this spec exactly
- [ ] Section bg follows mapping (cream / cream2 alternating)
- [ ] Only 1 dark moment (hero or footer, not both unless homepage)
- [ ] All CTAs Poppins uppercase, never italic
- [ ] Italic em has `white-space: nowrap`
- [ ] Pomegranate brand red `#C0392B` only red on page
- [ ] Brass gold only on dark bg italic em (rarely used)

### Voice / Content
- [ ] No em dash, no en dash, no specific numbers, no niche labels
- [ ] No promises (weekly/daily/monthly)
- [ ] Halil ismi yalnız Cities quote'da (or remove if Cities not used)
- [ ] Footer credit "by Show Me Türkiye Team"
- [ ] Brand pillars consistent: Routes / Films / Guides

### Mobile (CRITICAL)
- [ ] Viewport meta tag present
- [ ] Body has `-webkit-tap-highlight-color: transparent`
- [ ] All inputs `font-size: 16px+` (no iOS zoom)
- [ ] Touch targets min 44x44px (Apple HIG)
- [ ] Carousel dots padded for tap area (36x36 effective)
- [ ] Hamburger min 44x44px
- [ ] Use 3 standard breakpoints: 900px, 768px, 480px
- [ ] Asymmetric grids stack at 900px
- [ ] No `user-scalable=no` (accessibility violation)
- [ ] No hover-only interactions (mobile equivalent)
- [ ] Test at 320px width (no horizontal overflow)

### Accessibility
- [ ] AA contrast minimum, AAA preferred
- [ ] All images have `alt` attribute
- [ ] Interactive elements have `aria-label` if no text
- [ ] Focus states visible
- [ ] Reveal animations + reduced-motion fallback

### SEO / Meta
- [ ] OG image custom 1200×630
- [ ] Site-nav with proper scrolled class
- [ ] Canonical URL set
- [ ] JSON-LD structured data where applicable

---

*This document is the canonical reference for Show Me Türkiye visual identity. All new pages must conform.*
