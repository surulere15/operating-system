# AGU Loop v0 (Sprint 0)

A minimal end-to-end loop with **no dependencies**.

## Run

```bash
cd /Users/sam/.openclaw/workspace/project/frontend
python3 -m http.server 5173
```

Open: http://localhost:5173

## What works
- Entry → Action → Feedback → Progress Memory
- Local persistence via `localStorage`
- Memory Shelf v0 (moments)

## What’s next
- Replace localStorage with backend persistence
- Add AGS event telemetry (Safety/Competence/Belonging)
- Implement worlds + quest system (after loop KPIs)
