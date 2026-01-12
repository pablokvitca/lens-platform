# Visual Consistency Redesign

Date: 2026-01-12

## Goal

Make all pages visually consistent, add home navigation to all pages, and replace purple gradients with a distinctive color scheme.

## Design Decisions

### Color System

| Element | Old | New |
|---------|-----|-----|
| Primary accent | Violet/indigo gradient (`from-violet-600 to-indigo-600`) | Emerald-500 solid (`#10b981`) |
| Accent hover | Violet-700/indigo-700 | Emerald-600 (`#059669`) |
| Background base | Pure white | Stone-50 (`#fafaf9`) |
| Card/elevated surfaces | White | White (`#ffffff`) |
| Text primary | Slate-900 | Slate-900 (unchanged) |
| Text secondary | Slate-600 | Slate-600 (unchanged) |
| Borders | Slate-200 | Slate-200 (unchanged) |
| Links | Indigo-600 | Emerald-600 |
| Focus rings | Blue/indigo | Emerald-500 |

### Aesthetic Direction

- B2C SaaS feel (not academic)
- Light theme with warm off-white backgrounds
- Blend of approachable and technical modern
- Emerald accent ties subtly into "safety" connotations

### Navigation Header

All pages get consistent header:
- **Left**: "Lens Academy" wordmark (solid emerald-600, links to home)
- **Right**: "Course" link, "Login" button (or user state), "Join Our Discord Server" button

### Button Styles

- **Primary**: `bg-emerald-500 hover:bg-emerald-600 text-white rounded-full`
- **Secondary**: `border-2 border-slate-200 hover:border-slate-300 hover:bg-slate-50 rounded-full`

## Pages to Update

### landing.html
- Swap gradient buttons to solid emerald-500
- Wordmark: gradient text → solid emerald-600
- Add "Course" and "Login" links to navbar
- Change "Join Our Discord" → "Join Our Discord Server"

### Layout.tsx
- Same header treatment as landing
- Color updates to match new system
- "Join Our Discord" → "Join Our Discord Server"

### CourseOverview.tsx
- Add consistent nav header above breadcrumb
- Keep breadcrumb as secondary navigation below main nav
- Keep two-panel layout

### UnifiedLesson.tsx
- Add home link via "Lens Academy" wordmark in header
- Keep lesson title, progress bar, auth status
- Apply consistent brand styling

## Out of Scope

- Typography changes (keeping Tailwind defaults)
- Dark mode
- Major layout restructuring
