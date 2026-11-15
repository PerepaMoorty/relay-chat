# Relay — Features List (MoSCoW)

| | |
|---|---|
| **Project** | Relay: real-time chat application (Problem Statement: Chat Application, Socket Programming) |
| **Owner** | Naivadh Shrivastava (Product Owner) |
| **Status** | Approved baseline for Sprints 1 & 2 (aligned with Control v1.0 and SRS v2.0) |

---

## One-Line Pitch

> **Relay** is a lightweight, zero-configuration real-time chat platform engineered on Flask and Socket.IO that delivers persistent room-based messaging, live presence, direct messaging, read receipts, file sharing, and robust moderation over persistent WebSocket connections.

---

## 1. MoSCoW Feature Breakdown

### 1.1 Must Have (Sprint 1 — Core Chat Engine)
*Non-negotiable functional requirements delivering end-to-end real-time communication.*

- **E1: Connection & Session Lifecycle**
  - **F-001 (Connect):** Persistent WebSocket connection over configured IP and port.
  - **F-013 (Survive Disconnects):** Graceful recovery from abrupt network termination without server instability.
  - **F-014 (Graceful Termination):** Explicit session logout triggering socket cleanup and presence update.
  - **F-015 (Username ↔ Socket Mapping):** Thread-safe in-memory mapping between active session identities and socket IDs (`sid`).
  - **F-017 (Error Handling):** Standardized acknowledgement error envelope with consistent domain error codes.

- **E2: User Identity & Accounts**
  - **F-002 (Username Prompt):** Unauthenticated visitors are gated by the login/registration view before entering chat.
  - **F-003 (Unique Usernames):** Enforced unique username constraint with case-insensitive collision prevention.
  - **F-018 (Registration):** New user onboarding with secure salted scrypt password hashing.
  - **F-019 (Login & Session):** Session cookie issuance and automatic Socket.IO session authentication.

- **E3: Messaging**
  - **F-004 (Send Text):** Instant text transmission with client-side deduplication key (`client_id`).
  - **F-005 (Public Broadcast):** Automatic subscription to `#general` where public messages broadcast to all members.
  - **F-006 (Private Messages):** Direct 1:1 messaging isolated strictly to two participants via deterministic pair rooms.
  - **F-007 (Live Display):** Asynchronous live DOM updates upon incoming message push without page reload.
  - **F-008 (Timestamps):** Canonical server-assigned UTC timestamps displayed in user-local time.
  - **F-016 (Reject Invalid):** Rejection of empty messages, strings exceeding 4,000 characters, or unprintable control codes.
  - **F-020 (History Pagination):** Cursor-based backward message history scrolling (50 messages per page).
  - **F-029 (Edit Message):** Real-time in-place message modification restricted to author with update broadcasts.
  - **F-030 (Delete Message):** Soft deletion of messages preserving chronological ordering and receipts.

- **E4: Presence & Notifications**
  - **F-009 (Online List):** Real-time online/offline member roster updated via presence events.
  - **F-010 (Join Notice):** Ephemeral system notice broadcast when a user transitions online.
  - **F-011 (Leave Notice):** Ephemeral system notice broadcast after grace period expiration when a user disconnects.
  - **F-021 (Offline Delivery):** Delivery of missed messages upon client re-authentication.
  - **F-027 (Read Receipts):** Monotonic delivery and read watermarks (`delivered_up_to`, `read_up_to`).
  - **F-028 (Reconnect & Sync):** Auto-reconnection with catch-up synchronization using room message cursors.
  - **F-040 (Unread Counts):** Real-time badge tracking unread message count per conversation.

- **E5: Rooms**
  - **F-022 (Create Room):** User creation of custom group channels (public or private with invite code).
  - **F-023 (Browse/Join/Leave):** Room directory exploration, room membership joining, and voluntary leaving.

---

### 1.2 Should Have (Sprint 2 — Real-World Chat Enhancements)
*High-value operational, media, and moderation capabilities scheduled for Sprint 2.*

- **E1: Connection Scalability**
  - **F-012 (Concurrent Clients):** Concurrent client handling scaling reliably up to 20+ simultaneous connections.

- **E4: Presence & Interaction**
  - **F-026 (Typing Indicators):** Live typing indicator broadcast with debounce and auto-expiration (3 seconds).

- **E6: File Sharing**
  - **F-037 (Share Files):** Safe document and media file upload up to 10 MB with MIME verification.
  - **F-038 (Image Preview):** Inline visual thumbnail/preview rendering for image uploads (`.png`, `.jpg`, `.gif`, `.webp`).
  - **F-039 (Members-Only Download):** Protected download endpoints enforcing room membership before file serving.

- **E7: Search**
  - **F-041 (Search):** Full-text message search scoped strictly across rooms accessible to the caller.

- **E8: Administration & Moderation**
  - **F-046 (Report Message):** Member flagging of objectionable messages with mandatory reason.
  - **F-047 (Review Reports):** Admin moderation dashboard to inspect reports, dismiss, or soft-delete messages.
  - **F-048 (Ban/Unban User):** Admin capability to ban accounts, revoke sessions immediately, and terminate live sockets.
  - **F-049 (Mute/Unmute User):** Time-bound sender muting restricting message creation while preserving read access.
  - **F-051 (Audit Log):** Immutable append-only log recording every administrative action for accountability.
  - **F-052 (Monitor Clients & Activity):** Administrative monitoring of active socket connections and server operational events.

---

### 1.3 Could Have (Backlog — Future Considerations)
*Deferred features retained in the project backlog; out of scope for v1.0 release.*

- **CHAT-F-024:** Advanced invite-code management (revoking and regenerating invite codes).
- **CHAT-F-025:** Room management by owner (room renaming, ownership transfer, explicit member expulsion).
- **CHAT-F-031 — F-036:** Interactive message decorations: emoji reaction picker, threaded replies, message pinning, `@mentions`, and slash commands.
- **CHAT-F-042:** Browser native push notifications and granular per-room audio mute settings.
- **CHAT-F-043:** End-user conversation export to JSON/text archive.
- **CHAT-F-044:** Custom user profiles, bios, and avatar image uploads.
- **CHAT-F-045:** Peer-to-peer user blocking.
- **CHAT-F-050:** Permanent administrative room deletion.

---

### 1.4 Won't Have (Out of Scope by Architecture)
- Distributed multi-process broker clustering (Redis/RabbitMQ).
- End-to-end message payload encryption (E2EE).
- Password recovery via external SMTP email service.
- Third-party OAuth2/OIDC social login integrations.
