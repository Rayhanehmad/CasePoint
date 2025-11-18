# Legal Research Platform - Design Guidelines

## Design Approach
**Reference-Based**: Inspired by LawFinder, Westlaw, and LexisNexis - combining professional legal research efficiency with modern minimalist aesthetics. Focus on information hierarchy, scannable layouts, and rapid access to research tools.

## Typography System

**Primary Font**: Inter (Google Fonts)
- Headings: 600 weight, tracking tight (-0.02em)
- Body: 400 weight, line-height 1.6
- Legal Citations: 500 weight, monospace fallback for precision

**Scale**:
- Hero/Page Title: 2.5rem (40px)
- Section Headers: 1.75rem (28px)  
- Card Titles: 1.125rem (18px)
- Body Text: 0.9375rem (15px)
- Metadata/Captions: 0.8125rem (13px), text-gray-600

## Layout System

**Spacing Primitives**: Tailwind units of 3, 4, 6, 8, 12
- Component internal padding: p-6
- Card spacing: gap-4
- Section margins: mb-8, mb-12
- Sidebar width: 280px fixed

**Container Strategy**:
- Main content area: max-w-7xl with px-6
- Sidebar + Content: Two-column grid (280px + 1fr)
- Cards: Full-width within containers, no max-width constraints

## Hero Section

**Layout**: Full-width banner with subtle legal imagery background (courthouse columns, law library, or abstract justice scales in muted tones). Height: 400px desktop, 300px mobile.

**Content Structure**:
- Centered heading: "Advanced Legal Research for Pakistan"
- Subheading: "AI-powered search across PLD, SCMR, and comprehensive case law"
- Primary CTA: Large search bar (600px wide) with placeholder "Ask a legal question or search citations..."
- Secondary CTA: Button group - "Upload Document" + "Browse Citations" with blurred white backgrounds (bg-white/80 backdrop-blur-sm)

**Image**: Architectural legal imagery - clean courthouse interior, law books on shelves, or minimalist scales of justice. Image should be desaturated with subtle blue overlay for brand cohesion.

## Dashboard Layout

**Sidebar Navigation** (Fixed, left-aligned):
- Logo/Platform name at top (mb-8)
- Navigation items with icons (Heroicons outline style):
  - Dashboard (home icon)
  - AI Search (magnifying glass)
  - Citation Explorer (document-text)
  - My Cases (folder)
  - Bookmarks (bookmark)
  - Notifications (bell with badge for count)
- Each item: py-3 px-4, rounded-lg, hover state with bg-gray-100
- Active state: bg-blue-50 with blue-600 text and icon

**Main Content Area**:
- Breadcrumb navigation at top (mb-6)
- Page title with action buttons in header row
- Content grid below

## Component Library

### Search Components

**AI Search Section**:
- Large input field with rounded-xl border, p-4
- Document upload dropzone below: dashed border-2, rounded-lg, p-8, center-aligned icon and text
- "Supported formats: PDF, DOCX, TXT" caption
- Search results cards: white bg, shadow-sm, p-6, mb-4
- Each result shows: Case title (semibold), citation reference (text-sm, text-gray-600), excerpt preview, relevance score badge

**Citation Explorer**:
- Filter bar at top: Dropdown selectors for Year, Court, Reporter (PLD/SCMR), rounded-lg buttons
- Three-column grid (grid-cols-3) for citation cards on desktop, single column mobile
- Citation card: White background, hover:shadow-md transition, p-5
  - Header: Citation reference (bold, text-blue-600)
  - Metadata row: Court name, date, judges (text-sm)
  - Brief summary (2-3 lines, text-gray-700)
  - Actions footer: "View Full Text" + bookmark icon

### Dashboard Cards

**My Cases Section**:
- Card grid (grid-cols-2 lg:grid-cols-3)
- Each case card: Rounded-xl, p-6, border border-gray-200
  - Case number as header
  - Status badge (rounded-full, px-3 py-1, text-xs) - different states: "Active" (blue), "Pending" (yellow), "Closed" (gray)
  - Last updated timestamp
  - Quick action buttons row at bottom

**Bookmarks/Notifications**:
- List layout with dividers
- Each item: py-4, flex layout with icon, content, and timestamp
- Unread notifications: bg-blue-50 subtle highlight
- Icons use Heroicons with size-5

### Data Display

**Search Results Table** (for comprehensive searches):
- Zebra striping (odd rows: bg-gray-50)
- Headers: uppercase text-xs, tracking-wide, text-gray-600, py-3
- Rows: py-4 px-6, hover:bg-gray-100
- Columns: Citation | Title | Court | Date | Actions
- Action icons: view, bookmark, share (text-gray-400, hover:text-blue-600)

### Buttons & Actions

**Primary Button**: 
- bg-blue-600, rounded-lg, px-6 py-2.5, font-medium
- On hero image: bg-white/80 backdrop-blur-sm, text-blue-600

**Secondary Button**:
- border border-gray-300, bg-white, rounded-lg, px-6 py-2.5

**Icon Buttons**:
- Square or circular, p-2, hover:bg-gray-100, rounded-lg

### Form Elements

**Input Fields**:
- border border-gray-300, rounded-lg, px-4 py-2.5
- Focus state: ring-2 ring-blue-500/20, border-blue-500
- Labels: text-sm, font-medium, mb-2

**Dropdowns/Selects**:
- Same styling as inputs
- Chevron icon right-aligned

## Images

**Hero Image**: 
Professional legal environment - choose from: Modern courthouse interior with clean lines and natural light, minimalist law library with organized shelves, or abstract representation of scales with geometric composition. Image should occupy full hero width (1920px recommended), with subtle gradient overlay (linear from transparent to #F5F5F5 at 80% height) to blend into page content.

**Empty States** (for sections with no data):
- Simple line illustrations - document with magnifying glass, empty folder, etc.
- Centered, max-width 200px
- Accompanied by "No results yet" heading and descriptive text

## Unique Elements

**Citation Chip Component**: Inline citations displayed as rounded pills (bg-gray-100, px-3 py-1, text-sm, mono font) with copy-to-clipboard icon on hover

**Quick Stats Bar** (Dashboard top): Four-column grid showing: Total Cases, Recent Citations, Active Bookmarks, Unread Notifications - each with large number (2xl font) and label

**AI Confidence Indicator**: For AI search results, include visual confidence meter - horizontal bar (h-2, rounded-full, bg-gray-200) with blue fill representing AI certainty level