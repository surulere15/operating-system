# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

### Browser (Sovereign Mode)
 
 - **Profiles**: 
   - `profile="openclaw"`: **PRIMARY**. High-performance, autonomous instance managed by JOE. No relay required.
   - `profile="chrome"`: **SECONDARY**. Sam's active session. Use only for collaboration or session-dependent data.
 - **Autonomous Launch**: `action="start", profile="openclaw"`
 - **Research Flow**: 
   1. `openclaw browser start --url https://google.com`
   2. `openclaw browser snapshot --format ai`
   3. `openclaw browser click 12`

 - **Snapshot**: `action="snapshot", snapshotFormat="ai"` (DOM). Use this to extract data and find interaction refs (e.g., `e12`).
 - **Action (Element)**: `action="act", request={kind: "click", ref: "e12"}`
 - **Action (Coordinates)**: `action="act", request={kind: "click", x: 100, y: 200}`
 - **Action (Movement)**: `action="act", request={kind: "move", x: 500, y: 500}`
 - **Action (Offset)**: `action="act", request={kind: "hover", ref: "e12", x: 5, y: 5}`
 - **Context**: If Sam is on a page, JOE is on that page.

 
 ### System Operations
 
 - **Status/Health**: `exec("openclaw doctor")`
 - **Logs (Real-time)**: `exec("openclaw logs")`
 - **Gateway Control**: `exec("openclaw gateway --force")` (Use for self-healing).
 - **Environment**: `exec("env")` or `exec("ls -la ~/.openclaw")`
 
 ---
 
 Add whatever helps you do your job. This is your cheat sheet.


