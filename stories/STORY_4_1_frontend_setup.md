# STORY 4.1: Frontend Project Setup & Layout

## Overview
**Title:** Frontend Project Setup & Layout
**Phase:** 4 (Frontend MVP)
**Points:** 3
**Status:** Pending

---

## User Story

**As a** frontend developer
**I want** Next.js 14 project with TailwindCSS and base layout
**So that** I can build pages quickly

---

## Acceptance Criteria

- [ ] Next.js 14 with App Router initialized
- [ ] TailwindCSS configured
- [ ] Base layout with navbar and sidebar
- [ ] Authentication pages (login/signup) created
- [ ] Responsive design (mobile, tablet, desktop)

---

## Implementation Tasks

- [ ] Initialize Next.js 14 with create-next-app
- [ ] Install and configure TailwindCSS
- [ ] Install shadcn/ui components
- [ ] Create base layout component with navbar
- [ ] Create auth pages (placeholder)
- [ ] Add responsive design breakpoints
- [ ] Document setup in docs/FRONTEND_SETUP.md

---

## Test Cases

- [ ] App loads at localhost:3000
- [ ] Layout displays correctly on mobile
- [ ] Layout displays correctly on desktop
- [ ] Navbar is visible on all pages

---

## Dependencies

- STORY 1.1: Project Infrastructure Setup

---

## Technical Specifications

### Next.js Configuration
- **Version:** 14+
- **Router:** App Router (not Pages Router)
- **TypeScript:** Yes
- **ESLint:** Yes

### Styling Setup
- **Framework:** TailwindCSS 3+
- **Components:** shadcn/ui
- **CSS:** Tailwind utility classes
- **Dark Mode:** Supported (optional for MVP)

### Layout Structure

```
app/
├── layout.tsx           # Root layout with navbar
├── page.tsx             # Home/dashboard page
├── login/
│   └── page.tsx         # Login page
├── signup/
│   └── page.tsx         # Signup page
└── dashboard/
    └── layout.tsx       # Dashboard layout with sidebar
```

### Base Layout Components

1. **Navbar (Top Bar)**
   - Logo and brand name
   - Search/command palette placeholder
   - User menu
   - Responsive hamburger on mobile

2. **Sidebar (Dashboard)**
   - Navigation links (Dashboard, Analysis, Backtest, Watchlist, Settings)
   - Collapsible on mobile
   - Active page highlighting
   - User profile section at bottom

3. **Responsive Design**
   - Mobile: Stack layout, collapsible sidebar
   - Tablet: Narrow sidebar, adjusted spacing
   - Desktop: Full sidebar, optimal spacing

### Page Structure

```
pages/
├── Home/Dashboard
│   ├── Stock search input
│   ├── Quick actions
│   └── Recent activity

├── Stock Detail
│   ├── Price header
│   ├── Predictability score
│   ├── Prediction banner
│   ├── Analysis tabs
│   └── Historical analysis

├── Backtest
│   ├── Strategy builder
│   └── Results display

├── Watchlist
│   ├── Saved stocks list
│   └── Sorting/filtering

└── Settings
    ├── User preferences
    └── API key management
```

### Authentication Pages (Placeholder)

For MVP, create placeholder pages. Real authentication will be added later.

- **Login Page:** Email/password form
- **Signup Page:** Registration form

---

## Responsive Breakpoints

```typescript
// Mobile First Approach
sm: 640px   // Mobile
md: 768px   // Tablet
lg: 1024px  // Desktop
xl: 1280px  // Large Desktop
2xl: 1536px // Extra Large
```

---

## File Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── login/page.tsx
│   ├── signup/page.tsx
│   └── dashboard/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── [ticker]/page.tsx
│       ├── backtest/page.tsx
│       └── watchlist/page.tsx
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── MainLayout.tsx
│   ├── dashboard/
│   │   ├── StockSearch.tsx
│   │   └── StockCard.tsx
│   └── ui/ (shadcn components)
├── lib/
│   ├── utils.ts
│   └── constants.ts
├── hooks/
│   └── useNavigation.ts
├── styles/
│   └── globals.css
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

---

## Package Dependencies

```json
{
  "next": "^14.0.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "tailwindcss": "^3.3.0",
  "typescript": "^5.0.0",
  "@radix-ui/react-*": "latest",
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.0.0",
  "tailwind-merge": "^2.0.0"
}
```

---

## Acceptance Definition

Story is complete when:
1. Next.js 14 project is initialized
2. TailwindCSS is configured and working
3. shadcn/ui components are installed
4. Base layout with navbar is implemented
5. Sidebar component exists (collapsible)
6. Auth placeholder pages exist
7. Responsive design works on mobile, tablet, desktop
8. App loads without errors at localhost:3000
9. Documentation is written
