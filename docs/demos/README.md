# Relay — Demonstration Records and Walkthrough Scripts

| | |
|---|---|
| **Project** | Relay: Real-Time Chat Application (UE24CS341A Team 8) |
| **Owner** | Naivadh Shrivastava (Product Owner) |
| **Deliverables** | Sprint 1 & Sprint 2 video recordings, scripts, and evaluation logs |

---

## 1. Sprint 1 Demo Video

- **File:** `docs/demos/sprint-1.mp4`
- **Duration:** 60 seconds (1080p, compressed < 50 MB)
- **Target Release:** `v0.1.0` (commit baseline on `main` / `develop`)
- **Focus:** *"The v1.0 chat works end to end"* (Core messaging, presence, direct messaging, rooms, reconnect).

### 60-Second Walkthrough Script
1. **0:00 – 0:08 | Authentication & Setup:**  
   Launch application with fresh demo seed data. Open two browser windows side by side. Window 1 logs in as `alice` (`password123`); Window 2 logs in as `bob` (`password123`).
2. **0:08 – 0:20 | Presence & Public Broadcast:**  
   Roster immediately displays both `alice` and `bob` online with active indicators. Ephemeral join notice renders in `#general`. Send public text messages bi-directionally between windows in real time with instantaneous DOM updates.
3. **0:20 – 0:32 | Direct Messaging & Privacy Isolation:**  
   `alice` initiates a direct message (1:1 DM) with `bob`. Show that communication is strictly contained in the two-user room. Demonstrate delivery and double-checkmark (✓✓) read receipt watermark updates.
4. **0:32 – 0:44 | Room Management & Message Editing:**  
   `alice` creates a custom group room `#study-group`. `bob` browses and joins the room. `alice` posts a message, then edits it live (status label reflects `(edited)`), and soft-deletes a message.
5. **0:44 – 0:54 | Disconnect Resilience & Auto-Sync:**  
   Simulate network disconnect by temporarily halting the server. Observe the "Reconnecting..." banner. Send a message while offline; restart server. The client automatically reconnects, issues a catch-up `sync` cursor request, and renders the missed message with zero duplicates.
6. **0:54 – 1:00 | History Pagination & Unread Badges:**  
   Scroll back through conversation history demonstrating cursor-based pagination (50 messages per page) and verify real-time unread count badges clearing upon viewing.

---

## 2. Sprint 2 Demo Video

- **File:** `docs/demos/sprint-2.mp4`
- **Duration:** 120 seconds (1080p, compressed < 50 MB)
- **Target Release:** `v1.0.0` (final release on `main`)
- **Focus:** *"Relay behaves like a real chat product"* (Typing indicators, search, file attachments, image previews, and admin moderation console).

### 120-Second Walkthrough Script
1. **0:00 – 0:20 | Sprint 1 Recap:**  
   Brief visual recap of end-to-end multi-user chat, presence, and direct messaging.
2. **0:20 – 0:35 | Live Typing Indicators:**  
   `alice` starts composing a message in `#general`. `bob`'s screen displays `"alice is typing..."` with debounce and 3-second auto-expiration upon idle or send.
3. **0:35 – 0:55 | File Attachments & Inline Previews:**  
   `alice` attaches and uploads an image (`.png`). Both participants view the rendered inline thumbnail preview. `alice` uploads a project PDF; `bob` downloads the attachment via the authenticated members-only route.
4. **0:55 – 1:10 | Scoped Full-Text Search:**  
   `bob` opens the search modal and searches for keywords across message history. Matches appear filtered strictly across rooms `bob` has joined.
5. **1:10 – 1:30 | Reporting & Content Moderation:**  
   `bob` flags an inappropriate message using the "Report" button, supplying a report reason. Open the Administrator console (`admin` user). Review the report queue, inspect details, and soft-delete the offending message. The message disappears instantaneously from both `alice`'s and `bob`'s screens.
6. **1:30 – 1:45 | User Muting & Account Banning:**  
   Administrator temporarily mutes `bob` (15 minutes). `bob` attempts to send a message and receives `"You are muted until..."`. Administrator executes an account ban on `carol`; her active WebSocket session terminates immediately, and her login access is revoked.
7. **1:45 – 2:00 | Audit Logs, Active Clients & Closing:**  
   Administrator inspects the *Audit Log* tab verifying immutable entries (`user.ban`, `user.mute`, `message.delete`), followed by the *Clients* and *Activity* tabs showing live socket metrics. Conclude on the clean one-click `run-demo` startup execution.
