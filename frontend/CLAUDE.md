# CLAUDE.md (frontend — React/Vite)

## Commands
```bash
npm run dev      # Start Vite dev server on :5173
npm run build    # Type-check + build to frontend/dist/
npm run lint     # ESLint
```

## Architecture (`src/`)
- `App.tsx` — top-level state (selected album, photo list, map/list toggle)
- `api/client.ts` — all Axios calls, baseURL `/api`
- Map view uses Leaflet/react-leaflet; data fetched with TanStack React Query
