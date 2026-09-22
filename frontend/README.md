# Circular Electronics Marketplace — Frontend

React + Vite single-page app. This is the **Phase 3 foundation**: the app runs
standalone (navigation shell, routing, auth context, dashboard skeleton) even
though the backend does not exist yet. Feature screens and real API calls arrive
in later phases.

## Tech stack
- React 18 + Vite
- React Router (client-side routing)
- Axios (single API client — the service-layer seam)
- lucide-react (icons)
- Plain CSS with design tokens (`src/index.css`)

## Getting started
```bash
cd frontend
npm install
cp .env.example .env      # Windows: copy .env.example .env
npm run dev
```
Open http://localhost:5173

## What works in Phase 3
- Login / Register (STUBBED — pick a demo role to preview the role-aware sidebar;
  real JWT auth is Phase 7)
- Protected routes + auth guard + session persistence (localStorage)
- App shell: role-aware sidebar, top bar, mobile bottom nav
- Dashboard skeleton with clearly-labelled preview data
- Every route is browsable (feature pages show a "built in Phase X" placeholder)

## Folder structure
```
src/
├── components/
│   ├── layout/   AppLayout, Navbar, Sidebar, BottomNav, ProtectedRoute
│   └── ui/       Button, StatCard, StatusBadge, LoadingState
├── config/       nav.config.js  (role-aware navigation, single source of truth)
├── context/      AuthContext.jsx (current user + login/logout)
├── pages/        one component per route
├── services/     apiClient.js   (axios instance + JWT interceptor)
├── App.jsx       router
└── main.jsx      entry point
```

## Build
```bash
npm run build     # outputs to dist/
npm run preview   # serve the production build locally
```
