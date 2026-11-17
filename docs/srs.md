# Relay — Software Requirements Specification (SRS v2.0)

| | |
|---|---|
| **Project** | Relay: real-time chat application (Problem Statement: Chat Application, Socket Programming) |
| **Course** | UE24CS341A Software Engineering — Section E, Team 8 |
| **Document Version** | **v2.0** (2026-11-16) |
| **Owner** | Naivadh Shrivastava (Product Owner, SRN PES2UG24CS297) |
| **Baseline** | Aligned with Team Control File v1.1 and Software Architecture Document (SAD) v1.0 |
| **Related Documents** | [Features List](features.md) · [SAD](architecture.md) · [Test Plan](test-plan.md) · [Sprint Plan](sprint-plan.md) |

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for **Relay**, a real-time multi-user web chat application built as part of the coursework for UE24CS341A Software Engineering. Version 2.0 refines the preliminary requirements submitted in SRS v1.0 into concrete, testable functional and non-functional specifications suitable for parallel implementation across two agile sprints.

### 1.2 Document Conventions
- **Requirement Identifiers:**
  - `CHAT-F-001` through `CHAT-F-052` denote Functional Requirements.
  - `CHAT-NF-001` through `CHAT-NF-011` denote Non-Functional Requirements.
  - `CHAT-SR-001` through `CHAT-SR-014` denote Security Requirements.
- **Requirement Weights (MoSCoW):**
  - **Must:** Essential core chat functionality.
  - **Should:** Highly desirable features.
  - **Could:** Backlog items deferred post-v1.0.
  - **Won't:** Explicitly excluded architectural boundaries.
- **Traceability Status:**
  - `N`: Not started / Backlog
  - `P`: In progress / Pending external evidence
  - `A`: Accepted

### 1.3 Intended Audience & Reading Suggestions
This specification is intended for course instructors, examiners, the development team members (Developer 1, Developer 2, Scrum Master, Product Owner), and evaluation reviewers. Readers seeking high-level scope should examine Section 2 and Section 4. Technical reviewers should focus on Section 3 (Interfaces), Section 4 (System Features), Section 7 (RTM), and Appendix A (Deviations).

### 1.4 Project Scope
Relay provides instantaneous bi-directional communication between concurrent browser clients through persistent WebSocket connections managed by a single Python server process. The system supports a persistent public lobby (`#general`), custom group channels, isolated 1:1 direct messaging, live typing indicators, presence tracking, read receipts, attachment sharing up to 10 MB, and administrative moderation tools (banning, muting, reporting, and immutable audit logs).

---

## 2. Overall Description

### 2.1 Product Perspective
Relay is a self-contained, monolithic web application engineered for zero-configuration local area network (LAN) and localhost operation. It relies on standard browser technologies (Vanilla ES modules and standard HTML5/CSS3) communicating over HTTP (for REST transactions and static assets) and WebSockets via Flask-SocketIO (for real-time duplex event streaming).

### 2.2 Product Functions
- **Real-Time Duplex Messaging:** Sending, editing, soft-deleting, and syncing messages across public, private group, and direct channels.
- **Presence & Session Management:** Tracking online status, connection grace periods, and instant session termination upon logout or ban.
- **Message Reliability:** Delivery and read receipt watermarks, offline catch-up synchronization, and idempotency guarantees using client tokens.
- **Rich Media & Discovery:** Scoped message text search and secure file attachment sharing with MIME verification.
- **Administrative Moderation:** Inappropriate message reporting, message purging, user muting, account banning, and tamper-resistant audit logs.

### 2.3 User Classes and Characteristics
1. **Visitor (Unauthenticated User):** Can view login and registration forms, submit credentials, and access basic health endpoints.
2. **Registered User:** Can join public rooms, create rooms, exchange direct messages, upload attachments, search history, and report violations.
3. **Room Owner:** The creator of a group room who holds administrative privileges over room membership and visibility.
4. **Administrator:** System operator capable of reviewing reports, executing bans and mutes, purging messages, and inspecting audit trails and active sockets.

### 2.4 Operating Environment
- **Server Platform:** Python 3.11+ on Windows, macOS, or Linux.
- **Data Persistence:** SQLite 3 with WAL mode enabled.
- **Client Runtime:** Modern web browsers (Chrome, Edge, Firefox at 360 px to 1920 px) with native ES module and WebSocket support.
- **Network Environment:** Localhost or LAN environments with configurable IP binding and CORS policies.

### 2.5 Design and Implementation Constraints
- Single Python server process with threading concurrency; zero external message brokers (e.g., Redis) or standalone DBMS installations.
- Plain JavaScript client without bundlers (e.g., Webpack, Vite) or front-end frameworks (e.g., React, Vue).
- All message inputs sanitized and rendered strictly via DOM text nodes to eliminate cross-site scripting vulnerabilities.

---

## 3. External Interface Requirements

### 3.1 User Interfaces
The user interface is a responsive, single-page application consisting of:
- **Authentication View:** Clean dual form for user login and registration.
- **Chat Workspace:** Two-column layout featuring a collapsible sidebar (conversations list, unread badges, active presence roster) and an active conversation pane.
- **Conversation Pane:** Chronological message list, status watermarks (sent, delivered, read), inline image previews, typing notice bar, and rich message composer.
- **Administrative Dashboard:** Dedicated management console displaying active socket clients, server activity logs, moderation queues, and audit tables.

### 3.2 Software Interfaces
- **Flask 3.0:** Web framework providing HTTP routing, session cookie handling, and static file serving.
- **Flask-SocketIO 5.3 & simple-websocket:** WebSocket protocol server engine supporting room-based multicast and acknowledgement callbacks.
- **Flask-SQLAlchemy 3.1:** Object-Relational Mapper abstracting SQLite storage with parameterized queries.
- **Werkzeug 3.0:** Cryptographic hashing implementing salted scrypt algorithms.

### 3.3 Communication Protocols
- **HTTP/1.1:** Used for initial document delivery, REST resource interactions under `/api/*`, and binary file transfer.
- **WebSocket (Socket.IO protocol v4):** Used for bi-directional event distribution, heartbeats, and client-server acknowledgements.

---

## 4. System Features (Functional Requirements)

### 4.1 Epic 1: Connection & Session Lifecycle

- **CHAT-F-001 (Connect to the chat server):** The system shall allow a client to establish a TCP connection with the chat server using a configured IP address and port.
  - *Acceptance / Measurement:* Valid server address establishes a connection.
  - *Test Case:* `TC-CON-01`

- **CHAT-F-012 (Concurrent clients):** The server shall support multiple clients connecting concurrently.
  - *Acceptance / Measurement:* Multiple clients connect and communicate simultaneously.
  - *Test Case:* `TC-SRV-01`

- **CHAT-F-013 (Survive unexpected disconnects):** The server shall handle unexpected client disconnections without terminating the server process.
  - *Acceptance / Measurement:* Disconnected client is removed and server continues.
  - *Test Case:* `TC-SRV-02`

- **CHAT-F-014 (Graceful session termination):** The system shall allow a user to terminate their chat session gracefully.
  - *Acceptance / Measurement:* Socket closes and active-user list updates.
  - *Test Case:* `TC-CON-02`

- **CHAT-F-015 (Username-to-socket mapping):** The server shall maintain the association between connected usernames and active socket connections.
  - *Acceptance / Measurement:* Username maps to correct socket.
  - *Test Case:* `TC-SRV-03`

- **CHAT-F-017 (Communication error handling):** The server shall handle communication errors and report an appropriate status to affected clients.
  - *Acceptance / Measurement:* Communication failure is handled without server crash.
  - *Test Case:* `TC-ERR-01`

### 4.2 Epic 2: User Identity & Accounts

- **CHAT-F-002 (Prompt for username on connect):** The system shall request a username when a client connects to the server.
  - *Acceptance / Measurement:* Username prompt appears before chat access.
  - *Test Case:* `TC-AUTH-01`

- **CHAT-F-003 (Unique usernames):** The system shall ensure that each connected user has a unique username.
  - *Acceptance / Measurement:* Duplicate username is rejected.
  - *Test Case:* `TC-AUTH-02`

- **CHAT-F-018 (Register an account with a password):** The system shall allow a visitor to register an account with a unique username (3-20 characters: letters, digits, underscore) and a password of at least 8 characters.
  - *Acceptance / Measurement:* Valid username and password create an account and log the user in. Duplicate usernames are rejected with USERNAME_TAKEN; invalid usernames or short passwords with VALIDATION_ERROR.
  - *Test Case:* `TC-ACC-01`

- **CHAT-F-019 (Log in with a session bound to the socket):** The system shall authenticate users by username and password, create a server-side session, and accept a socket connection only for an authenticated session, attributing every message to that session's user.
  - *Acceptance / Measurement:* Correct credentials open the chat; wrong ones show a generic error. A socket without a valid session is refused; a forged sender field in a payload is ignored.
  - *Test Case:* `TC-ACC-02`

- **CHAT-F-044 (Profile and avatar):** *(Backlog)* The system shall let a user set a display name (1-40 chars), status text (≤100 chars) and avatar (PNG/JPEG ≤2 MB).
  - *Acceptance / Measurement:* Changes show to others on their next render; invalid avatars are rejected.
  - *Test Case:* `TC-PROF-01`

- **CHAT-F-045 (Block a user):** *(Backlog)* The system shall let a user block and unblock another user; a blocked user cannot send private messages to the blocker.
  - *Acceptance / Measurement:* After A blocks B, B's private messages to A fail with BLOCKED until unblocked.
  - *Test Case:* `TC-PROF-02`

### 4.3 Epic 3: Messaging

- **CHAT-F-004 (Send a text message):** The system shall allow a connected user to send a text message to the chat.
  - *Acceptance / Measurement:* Valid message is transmitted to server.
  - *Test Case:* `TC-MSG-01`

- **CHAT-F-005 (Broadcast public messages):** The server shall broadcast public messages to all eligible connected users.
  - *Acceptance / Measurement:* Public message appears for all eligible users.
  - *Test Case:* `TC-MSG-02`

- **CHAT-F-006 (Private (1:1) messages):** The system shall allow a user to send a private message to another connected user.
  - *Acceptance / Measurement:* Private message is delivered only to sender and recipient.
  - *Test Case:* `TC-PRV-01`

- **CHAT-F-007 (Live display without refresh):** The system shall display received messages without requiring manual refresh.
  - *Acceptance / Measurement:* Received message automatically appears.
  - *Test Case:* `TC-MSG-03`

- **CHAT-F-008 (Message timestamps):** The system shall attach a timestamp to each successfully processed chat message.
  - *Acceptance / Measurement:* Displayed message contains timestamp.
  - *Test Case:* `TC-MSG-04`

- **CHAT-F-016 (Reject empty or invalid messages):** The system shall reject empty or invalid chat messages.
  - *Acceptance / Measurement:* Invalid message is not transmitted as valid chat.
  - *Test Case:* `TC-VAL-01`

- **CHAT-F-020 (Persistent history with pagination):** The system shall persist every message and, when a conversation is opened, show the 50 most recent messages, loading older pages of 50 on scroll-up.
  - *Acceptance / Measurement:* Messages survive a server restart. With 120 messages, the latest 50 show; scrolling up loads the next 50 in order without duplicates.
  - *Test Case:* `TC-HIST-01`

- **CHAT-F-029 (Edit own message):** The system shall allow a sender to edit their own message, updating it for all members and marking it '(edited)'.
  - *Acceptance / Measurement:* Edits appear live everywhere with '(edited)'; editing another user's message fails with FORBIDDEN.
  - *Test Case:* `TC-RICH-01`

- **CHAT-F-030 (Delete own message):** The system shall allow a sender to delete their own message, replacing it for all members with 'message deleted'.
  - *Acceptance / Measurement:* All clients show the placeholder and the history API no longer returns the text.
  - *Test Case:* `TC-RICH-02`

- **CHAT-F-031 (Emoji picker):** *(Backlog)* The system shall provide an emoji picker in the composer and store and display Unicode emoji correctly.
  - *Acceptance / Measurement:* A picked emoji is inserted at the cursor and round-trips unchanged.
  - *Test Case:* `TC-RICH-03`

- **CHAT-F-032 (Message reactions):** *(Backlog)* The system shall let a member toggle emoji reactions on messages, showing live aggregated counts.
  - *Acceptance / Measurement:* Clicking a reaction toggles it for me and updates every client.
  - *Test Case:* `TC-RICH-04`

- **CHAT-F-033 (Reply to a message):** *(Backlog)* The system shall let a member reply to a specific earlier message, showing a quoted preview that links to the original.
  - *Acceptance / Measurement:* The reply shows the quoted snippet; clicking it scrolls to the original.
  - *Test Case:* `TC-RICH-05`

- **CHAT-F-034 (Pin messages):** *(Backlog)* The system shall let a room owner pin and unpin messages, shown in a pinned panel to all members.
  - *Acceptance / Measurement:* Pinned messages show for all members; only the owner can pin.
  - *Test Case:* `TC-RICH-06`

- **CHAT-F-035 (@mentions):** *(Backlog)* The system shall highlight @username mentions of conversation members and notify the mentioned user.
  - *Acceptance / Measurement:* '@medha' is highlighted and Medha is notified even if the conversation is muted.
  - *Test Case:* `TC-RICH-07`

- **CHAT-F-036 (Slash commands):** *(Backlog)* The system shall support the composer commands /help, /me <action>, /clear, /join <invite-code> and /dm <username>.
  - *Acceptance / Measurement:* Each command acts as described; unknown commands show /help instead of being sent.
  - *Test Case:* `TC-RICH-08`

- **CHAT-F-043 (Export a conversation):** *(Backlog)* The system shall let a member export a conversation as .txt or .json.
  - *Acceptance / Measurement:* The export contains every non-deleted message with sender and ISO-8601 timestamp, in order.
  - *Test Case:* `TC-SRCH-02`

### 4.4 Epic 4: Presence & Notifications

- **CHAT-F-009 (Online users list):** The system shall maintain a list of currently connected users.
  - *Acceptance / Measurement:* List matches active connections.
  - *Test Case:* `TC-USER-01`

- **CHAT-F-010 (Join notifications):** The system shall notify connected users when a new user joins the chat.
  - *Acceptance / Measurement:* Join notification is displayed.
  - *Test Case:* `TC-USER-02`

- **CHAT-F-011 (Leave notifications):** The system shall notify connected users when an active user leaves the chat.
  - *Acceptance / Measurement:* Leave notification is displayed.
  - *Test Case:* `TC-USER-03`

- **CHAT-F-021 (Offline message delivery):** The system shall keep messages sent to a member while they are offline and show them, marked unread, at their next login.
  - *Acceptance / Measurement:* B logs out; A sends 3 private messages; on login B sees all 3 and the conversation is marked unread.
  - *Test Case:* `TC-HIST-02`

- **CHAT-F-026 (Typing indicators):** The system shall show '<name> is typing…' to other members while a member is composing in that conversation.
  - *Acceptance / Measurement:* Indicator appears within 1 s of typing and clears within 3 s of stopping or sending.
  - *Test Case:* `TC-PRES-01`

- **CHAT-F-027 (Delivered and read receipts):** The system shall track per-member delivered and read positions and show the sender sent/delivered/read for private messages and 'read by N' in rooms.
  - *Acceptance / Measurement:* A private message shows 'delivered' on receipt and 'read' once viewed; room read counts update live.
  - *Test Case:* `TC-PRES-02`

- **CHAT-F-028 (Auto-reconnect with missed-message sync):** The system shall automatically re-establish a dropped connection and fetch every message created since the client's last received message, without a page reload.
  - *Acceptance / Measurement:* After 30 s offline while 5 messages are sent, reconnecting shows all 5 in order with no duplicates; a 'reconnecting…' banner shows meanwhile.
  - *Test Case:* `TC-PRES-03`

- **CHAT-F-040 (Unread counts):** The system shall show an unread-message count per conversation, cleared when the user reads it and persisted across logins.
  - *Acceptance / Measurement:* 3 messages in a closed conversation show a badge of 3; opening clears it.
  - *Test Case:* `TC-PRES-04`

- **CHAT-F-042 (Browser notifications and muting):** *(Backlog)* The system shall show a browser notification for new messages while the tab is hidden (with permission), and let a user mute notifications per conversation.
  - *Acceptance / Measurement:* Hidden tab + new private message → desktop notification; muted conversations stay silent except @mentions.
  - *Test Case:* `TC-PRES-05`

### 4.5 Epic 5: Rooms

- **CHAT-F-022 (Create a group room):** The system shall let a user create a named group room (public or private); the creator becomes its owner and first member.
  - *Acceptance / Measurement:* A 1-40 character name creates the room with the creator as owner; empty or longer names are rejected.
  - *Test Case:* `TC-ROOM-01`

- **CHAT-F-023 (Browse, join and leave public rooms):** The system shall list public rooms, let a user join any of them, and let a member leave a room they belong to.
  - *Acceptance / Measurement:* Public rooms are listed with member counts; private rooms never appear. Joining adds the room and posts a join notice; leaving stops further messages from it.
  - *Test Case:* `TC-ROOM-02`

- **CHAT-F-024 (Private rooms with invite codes):** *(Backlog)* The system shall allow private rooms to be joined only with a valid invite code, which the owner can regenerate to invalidate the old one.
  - *Acceptance / Measurement:* A valid code joins; an invalid or rotated code fails with INVALID_INVITE.
  - *Test Case:* `TC-ROOM-03`

- **CHAT-F-025 (Owner room management):** *(Backlog)* The system shall let a room owner rename the room and remove members, who lose access immediately.
  - *Acceptance / Measurement:* Non-owners get FORBIDDEN; a removed member stops receiving the room's messages at once.
  - *Test Case:* `TC-ROOM-04`

### 4.6 Epic 6: File Sharing

- **CHAT-F-037 (Share files and images):** The system shall let a member send a file of an allowed type (images, PDF, text, Office documents, ZIP) up to 10 MB to a conversation.
  - *Acceptance / Measurement:* Allowed files up to 10 MB arrive as messages with name and size; larger or disallowed files fail with PAYLOAD_TOO_LARGE / UNSUPPORTED_TYPE before storage.
  - *Test Case:* `TC-FILE-01`

- **CHAT-F-038 (Inline image preview):** The system shall show shared PNG, JPEG, GIF and WebP images as inline thumbnails that open full size on click.
  - *Acceptance / Measurement:* A PNG shows as a thumbnail at most 320 px wide; clicking opens it full size.
  - *Test Case:* `TC-FILE-02`

- **CHAT-F-039 (Members-only file download):** The system shall serve an attachment only to authenticated members of the conversation it was shared in.
  - *Acceptance / Measurement:* Members download; logged-in non-members get 403; anonymous requests get 401.
  - *Test Case:* `TC-FILE-03`

### 4.7 Epic 7: Search

- **CHAT-F-041 (Search messages):** The system shall let a user search messages by keyword across their own conversations, optionally filtered by conversation or sender, returning at most 50 results newest first.
  - *Acceptance / Measurement:* Results come only from the user's conversations and link to the message in context.
  - *Test Case:* `TC-SRCH-01`

### 4.8 Epic 8: Administration & Moderation

- **CHAT-F-046 (Report a message):** The system shall let a member report a message with a reason, creating a report visible to administrators.
  - *Acceptance / Measurement:* A report is created as 'open'; the same user cannot report the same message twice.
  - *Test Case:* `TC-ADM-01`

- **CHAT-F-047 (Review reports and remove messages):** The system shall give administrators a list of open reports with context and let them delete the reported message and resolve or dismiss the report.
  - *Acceptance / Measurement:* Deleting removes the message from all clients and resolves the report; non-admins get 403.
  - *Test Case:* `TC-ADM-02`

- **CHAT-F-048 (Ban and unban users):** The system shall let an administrator ban and unban users; a ban immediately ends the user's sessions and connections and blocks future logins.
  - *Acceptance / Measurement:* A banned online user's tabs disconnect within 2 s with a notice; logins are refused until unbanned.
  - *Test Case:* `TC-ADM-03`

- **CHAT-F-049 (Mute users):** The system shall let an administrator mute a user for 15 minutes to 7 days, during which their messages are rejected.
  - *Acceptance / Measurement:* A muted user's send fails with MUTED and the remaining time; it works again after expiry.
  - *Test Case:* `TC-ADM-04`

- **CHAT-F-050 (Delete a room):** *(Backlog)* The system shall let an administrator delete any group room, removing it for all members.
  - *Acceptance / Measurement:* The room disappears from all members' lists live and its history becomes inaccessible.
  - *Test Case:* `TC-ADM-05`

- **CHAT-F-051 (Audit log of admin actions):** The system shall record every administrative action (ban, unban, mute, message deletion, room deletion, report resolution) with actor, action, target, reason and timestamp, viewable by administrators.
  - *Acceptance / Measurement:* Each admin action creates exactly one entry, listed newest first; entries cannot be edited or deleted through the app.
  - *Test Case:* `TC-ADM-06`

- **CHAT-F-052 (Monitor clients and server activity):** The system shall give administrators a live view of connected clients and a server activity log of connections, disconnections and errors.
  - *Acceptance / Measurement:* The admin view lists connected users with connect time; the activity log records each connect, disconnect and handled error.
  - *Test Case:* `TC-ADM-07`

---

## 5. Non-Functional Requirements (NFRs)

- **CHAT-NF-001 (Performance):** The system shall deliver a successfully transmitted message to connected recipients within 2 seconds under normal LAN conditions.
  - *Acceptance / Measurement:* 90% of test messages delivered within 2 seconds.
  - *Test Case:* `TC-PERF-01`

- **CHAT-NF-002 (Reliability):** The server shall remain operational when multiple clients are connected simultaneously.
  - *Acceptance / Measurement:* Server continues operating during concurrent-client testing.
  - *Test Case:* `TC-REL-01`

- **CHAT-NF-003 (Usability):** The system shall provide a simple interface allowing a new user to connect and send a message without specialized training.
  - *Acceptance / Measurement:* Test users complete basic chat operations.
  - *Test Case:* `TC-UX-01`

- **CHAT-NF-004 (Robustness):** The system shall handle invalid input and communication failures without terminating unexpectedly.
  - *Acceptance / Measurement:* Failure tests do not crash the application.
  - *Test Case:* `TC-ROB-01`

- **CHAT-NF-005 (Scalability):** The server shall support at least 20 simultaneous client connections under the defined test environment.
  - *Acceptance / Measurement:* 20 clients connect and communicate during load testing.
  - *Test Case:* `TC-SCALE-01`

- **CHAT-NF-006 (Reliability):** The system shall maintain consistent message ordering for messages processed sequentially by the server.
  - *Acceptance / Measurement:* Test messages appear in expected processing order.
  - *Test Case:* `TC-ORD-01`

- **CHAT-NF-007 (Reliability):** After a network drop or server restart, clients shall reconnect automatically within 10 seconds of the server becoming reachable, and no message acknowledged to its sender shall be lost.
  - *Acceptance / Measurement:* Restart the server mid-conversation: all acknowledged messages persist; clients reconnect ≤ 10 s.
  - *Test Case:* `TC-REL-02`

- **CHAT-NF-008 (Compatibility):** The web client shall work on the two latest versions of Chrome, Edge and Firefox at widths from 360 px to 1920 px.
  - *Acceptance / Measurement:* Acceptance suite passes on each browser at 360/1366/1920 px.
  - *Test Case:* `TC-COMP-01`

- **CHAT-NF-009 (Maintainability):** The code shall follow the layered architecture (handlers → services → models), pass ruff lint in CI, and keep line coverage of relay/services at or above 70%.
  - *Acceptance / Measurement:* CI shows ruff clean and coverage ≥ 70% on relay/services.
  - *Test Case:* `TC-MAINT-01`

- **CHAT-NF-010 (Portability):** The system shall install and start on Windows, macOS or Linux with Python 3.11 using only the README commands, with no external database or broker.
  - *Acceptance / Measurement:* Fresh clone runs on two OSes in under 10 minutes.
  - *Test Case:* `TC-PORT-01`

- **CHAT-NF-011 (Data retention):** Messages and attachments shall be retained until deleted by the sender or an administrator; audit entries shall be retained for at least 90 days and cannot be modified through the application.
  - *Acceptance / Measurement:* No update/delete path exists for audit_log; retention verified by inspection.
  - *Test Case:* `TC-DATA-01`

---

## 6. Security Requirements (SRs)

- **CHAT-SR-001 (Security: Reject invalid connections):** The system shall reject clients that fail to establish a valid connection with the chat server.
  - *Acceptance / Measurement:* Invalid connection attempts are rejected.
  - *Test Case:* `TC-SEC-01`

- **CHAT-SR-002 (Security: No duplicate usernames):** The system shall prevent two simultaneously connected clients from using the same username.
  - *Acceptance / Measurement:* Duplicate username attempt is rejected.
  - *Test Case:* `TC-SEC-02`

- **CHAT-SR-003 (Security: Private-message routing):** The server shall ensure that private messages are delivered only to the intended recipient and sender.
  - *Acceptance / Measurement:* Third-party client does not receive private message.
  - *Test Case:* `TC-SEC-03`

- **CHAT-SR-004 (Security: Validate message data):** The system shall validate user-provided message data before processing it.
  - *Acceptance / Measurement:* Malformed or invalid message input is rejected safely.
  - *Test Case:* `TC-SEC-04`

- **CHAT-SR-005 (Security: No use of dead sockets):** The server shall prevent a disconnected client from continuing to use an inactive socket connection.
  - *Acceptance / Measurement:* Messages from terminated connection are not processed.
  - *Test Case:* `TC-SEC-05`

- **CHAT-SR-006 (Security: Salted password hashing):** Passwords shall be stored only as salted adaptive hashes (Werkzeug scrypt/PBKDF2) and never logged or returned by any API.
  - *Acceptance / Measurement:* DB shows only hashes; logs captured during login tests contain no password.
  - *Test Case:* `TC-SEC-06`

- **CHAT-SR-007 (Security: Session-authenticated sockets):** Every socket connection shall be authenticated from the server-side session at handshake; session cookies shall be HttpOnly and SameSite=Lax.
  - *Acceptance / Measurement:* Connect without a cookie or with a banned user's cookie is refused; cookie flags verified.
  - *Test Case:* `TC-SEC-07`

- **CHAT-SR-008 (Security: Server-side authorisation):** Every endpoint and socket event touching a conversation shall verify server-side that the actor is a member (or owner/admin as required); the sender identity shall come only from the session.
  - *Acceptance / Measurement:* Requests for rooms the user is not in return FORBIDDEN; spoofed sender fields are ignored.
  - *Test Case:* `TC-SEC-08`

- **CHAT-SR-009 (Security: XSS-safe rendering + CSP):** User content shall be rendered as text only (never interpreted as HTML), and pages shall carry a Content-Security-Policy of default-src 'self'.
  - *Acceptance / Measurement:* <script> and <img onerror> payloads render literally without executing; CSP header present.
  - *Test Case:* `TC-SEC-09`

- **CHAT-SR-010 (Security: Upload validation):** Uploads shall be accepted only for allow-listed types verified by content signature, at most 10 MB, stored under random names outside the web root, and served with X-Content-Type-Options: nosniff (non-images as attachments).
  - *Acceptance / Measurement:* Renamed .exe/.html uploads are rejected; stored names are random; headers verified.
  - *Test Case:* `TC-SEC-10`

- **CHAT-SR-011 (Security: ORM-only SQL, length limits):** All database access shall use parameterised ORM queries, and inputs shall be length-limited (message ≤ 4000 chars, room name ≤ 40, username pattern).
  - *Acceptance / Measurement:* Over-length input fails with VALIDATION_ERROR; SQL metacharacters in search have no effect.
  - *Test Case:* `TC-SEC-11`

- **CHAT-SR-012 (Security: Admin role + audit):** Administrative operations shall require the admin role and each shall write an immutable audit record.
  - *Acceptance / Measurement:* Non-admin calls to /api/admin/* get 403; each admin action yields one audit row.
  - *Test Case:* `TC-SEC-12`

- **CHAT-SR-013 (Security: Revocation on ban/logout):** When a user is banned or logs out, all of their sessions shall be invalidated and their sockets disconnected within 2 seconds.
  - *Acceptance / Measurement:* Ban a user with 2 tabs: both disconnect ≤ 2 s; the old cookie is rejected.
  - *Test Case:* `TC-SEC-13`

- **CHAT-SR-014 (Security: Origin-restricted WebSocket):** Socket connections shall be accepted only from configured application origins, preventing cross-site WebSocket hijacking.
  - *Acceptance / Measurement:* A handshake with a foreign Origin header is refused.
  - *Test Case:* `TC-SEC-14`

---

## 7. Requirements Traceability Matrix (RTM)

The matrix below maps each requirement across the software lifecycle.

| ID | Title | SRS § | Design Ref (SAD §) | Module | Test Case | Sprint | Registry PRs | Status |
|---|---|---|---|---|---|---|---|---|
| CHAT-F-001 | Connect to the chat server | 4.1 | 5.1, 5.8 | `relay/events/connection.py` | TC-CON-01 | Sprint 1 | B7, F2, T6 | A |
| CHAT-F-002 | Prompt for username on connect | 4.2 | 5.8, 6 | `relay/static/js/views/login.js` | TC-AUTH-01 | Sprint 1 | F4, T3 | A |
| CHAT-F-003 | Unique usernames | 4.2 | 5.8, 7 | `relay/models/user.py` | TC-AUTH-02 | Sprint 1 | B4, T3 | A |
| CHAT-F-004 | Send a text message | 4.3 | 5.4, 5.8 | `relay/events/chat.py` | TC-MSG-01 | Sprint 1 | B5, B8, F7, T6 | A |
| CHAT-F-005 | Broadcast public messages | 4.3 | 5.1, 5.8 | `relay/events/chat.py` | TC-MSG-02 | Sprint 1 | B8, T6 | A |
| CHAT-F-006 | Private (1:1) messages | 4.3 | 5.1, 5.8, 7 | `relay/services/rooms.py` | TC-PRV-01 | Sprint 1 | B5, B6, F5, T5, T6 | A |
| CHAT-F-007 | Live display without refresh | 4.3 | 5.8, 9 | `relay/static/js/views/conversation.js` | TC-MSG-03 | Sprint 1 | F6, F9, T6 | A |
| CHAT-F-008 | Message timestamps | 4.3 | 5.8, 9 | `relay/static/js/dom.js` | TC-MSG-04 | Sprint 1 | F3, F6, T5 | A |
| CHAT-F-009 | Online users list | 4.4 | 5.1, 5.8 | `relay/services/presence.py` | TC-USER-01 | Sprint 1 | B7, F5, T6 | A |
| CHAT-F-010 | Join notifications | 4.4 | 5.8 | `relay/events/connection.py` | TC-USER-02 | Sprint 1 | B7, F6, T6 | A |
| CHAT-F-011 | Leave notifications | 4.4 | 5.8 | `relay/events/connection.py` | TC-USER-03 | Sprint 1 | B7, F6, T6 | A |
| CHAT-F-012 | Concurrent clients | 4.1 | 5.8, 13 | `relay/events/connection.py` | TC-SRV-01 | Sprint 2 | B7, T6 | A |
| CHAT-F-013 | Survive unexpected disconnects | 4.1 | 5.3, 5.8 | `relay/events/_ack.py` | TC-SRV-02 | Sprint 1 | B3, B7, T6 | A |
| CHAT-F-014 | Graceful session termination | 4.1 | 5.8, 6 | `relay/api/auth.py` | TC-CON-02 | Sprint 1 | B4, B7, F9, T3 | A |
| CHAT-F-015 | Username-to-socket mapping | 4.1 | 4.2, 5.8 | `relay/services/presence.py` | TC-SRV-03 | Sprint 1 | B2, T2 | A |
| CHAT-F-016 | Reject empty or invalid messages | 4.3 | 5.8 | `relay/services/messages.py` | TC-VAL-01 | Sprint 1 | B5, F7, T4 | A |
| CHAT-F-017 | Communication error handling | 4.1 | 5.3, 5.6 | `relay/events/_ack.py` | TC-ERR-01 | Sprint 1 | B3, F2, T6 | A |
| CHAT-F-018 | Register an account with a password | 4.2 | 6, 10 | `relay/api/auth.py` | TC-ACC-01 | Sprint 1 | B4, F4, T3 | A |
| CHAT-F-019 | Log in with a session bound to the socket | 4.2 | 5.2, 6 | `relay/api/auth.py` | TC-ACC-02 | Sprint 1 | B4, B7, F4, T3, T6 | A |
| CHAT-F-020 | Persistent history with pagination | 4.3 | 6, 7 | `relay/api/rooms.py` | TC-HIST-01 | Sprint 1 | B6, F6, T5 | A |
| CHAT-F-021 | Offline message delivery | 4.4 | 5.4, 5.7 | `relay/services/sync.py` | TC-HIST-02 | Sprint 1 | B5, B6, T5 | A |
| CHAT-F-022 | Create a group room | 4.5 | 6, 7 | `relay/api/rooms.py` | TC-ROOM-01 | Sprint 1 | B6, F8, T5 | A |
| CHAT-F-023 | Browse, join and leave public rooms | 4.5 | 6 | `relay/api/rooms.py` | TC-ROOM-02 | Sprint 1 | B6, F8, T5 | A |
| CHAT-F-024 | Private rooms with invite codes | 4.5 | 14 | `relay/services/rooms.py` | TC-ROOM-03 | Backlog | - | N |
| CHAT-F-025 | Owner room management | 4.5 | 14 | `relay/services/rooms.py` | TC-ROOM-04 | Backlog | - | N |
| CHAT-F-026 | Typing indicators | 4.4 | 5.4 | `relay/events/presence.py` | TC-PRES-01 | Sprint 2 | B9, F6, F7, T7 | A |
| CHAT-F-027 | Delivered and read receipts | 4.4 | 5.4, 5.7 | `relay/services/receipts.py` | TC-PRES-02 | Sprint 1 | B5, B8, F6, T6 | A |
| CHAT-F-028 | Auto-reconnect with missed-message sync | 4.4 | 5.4, 5.7 | `relay/services/sync.py` | TC-PRES-03 | Sprint 1 | B8, F2, F9, T6 | A |
| CHAT-F-029 | Edit own message | 4.3 | 5.4 | `relay/events/chat.py` | TC-RICH-01 | Sprint 1 | B5, B8, F6, T6 | A |
| CHAT-F-030 | Delete own message | 4.3 | 5.4, 7 | `relay/events/chat.py` | TC-RICH-02 | Sprint 1 | B5, B8, F6, T6 | A |
| CHAT-F-031 | Emoji picker | 4.3 | 14 | `relay/services/messages.py` | TC-RICH-03 | Backlog | - | N |
| CHAT-F-032 | Message reactions | 4.3 | 14 | `relay/services/messages.py` | TC-RICH-04 | Backlog | - | N |
| CHAT-F-033 | Reply to a message | 4.3 | 14 | `relay/services/messages.py` | TC-RICH-05 | Backlog | - | N |
| CHAT-F-034 | Pin messages | 4.3 | 14 | `relay/services/messages.py` | TC-RICH-06 | Backlog | - | N |
| CHAT-F-035 | @mentions | 4.3 | 14 | `relay/static/js/views/conversation.js` | TC-RICH-07 | Backlog | - | N |
| CHAT-F-036 | Slash commands | 4.3 | 14 | `relay/events/chat.py` | TC-RICH-08 | Backlog | - | N |
| CHAT-F-037 | Share files and images | 4.6 | 6, 10 | `relay/api/files.py` | TC-FILE-01 | Sprint 2 | B11, F6, F7, T7 | A |
| CHAT-F-038 | Inline image preview | 4.6 | 6, 9 | `relay/static/js/views/conversation.js` | TC-FILE-02 | Sprint 2 | B11, F6, T7 | A |
| CHAT-F-039 | Members-only file download | 4.6 | 6, 10 | `relay/api/files.py` | TC-FILE-03 | Sprint 2 | B11, T7 | A |
| CHAT-F-040 | Unread counts | 4.4 | 5.7 | `relay/services/receipts.py` | TC-PRES-04 | Sprint 1 | B5, B6, F3, F5, T5 | A |
| CHAT-F-041 | Search messages | 4.7 | 6, 7 | `relay/api/search.py` | TC-SRCH-01 | Sprint 2 | B10, F8, T7 | A |
| CHAT-F-042 | Browser notifications and muting | 4.4 | 14 | `relay/static/js/app.js` | TC-PRES-05 | Backlog | - | N |
| CHAT-F-043 | Export a conversation | 4.3 | 14 | `relay/services/messages.py` | TC-SRCH-02 | Backlog | - | N |
| CHAT-F-044 | Profile and avatar | 4.2 | 14 | `relay/services/auth.py` | TC-PROF-01 | Backlog | - | N |
| CHAT-F-045 | Block a user | 4.2 | 14 | `relay/services/auth.py` | TC-PROF-02 | Backlog | - | N |
| CHAT-F-046 | Report a message | 4.8 | 6 | `relay/api/admin.py` | TC-ADM-01 | Sprint 2 | B12, F10, T8 | A |
| CHAT-F-047 | Review reports and remove messages | 4.8 | 6 | `relay/api/admin.py` | TC-ADM-02 | Sprint 2 | B12, F10, T8 | A |
| CHAT-F-048 | Ban and unban users | 4.8 | 6, 8.2 | `relay/api/admin.py` | TC-ADM-03 | Sprint 2 | B12, F10, T8 | A |
| CHAT-F-049 | Mute users | 4.8 | 6 | `relay/api/admin.py` | TC-ADM-04 | Sprint 2 | B12, F10, T8 | A |
| CHAT-F-050 | Delete a room | 4.8 | 14 | `relay/services/rooms.py` | TC-ADM-05 | Backlog | - | N |
| CHAT-F-051 | Audit log of admin actions | 4.8 | 6, 7 | `relay/services/audit.py` | TC-ADM-06 | Sprint 2 | B12, F10, T8 | A |
| CHAT-F-052 | Monitor clients and server activity | 4.8 | 6 | `relay/services/activity.py` | TC-ADM-07 | Sprint 2 | B2, B12, F10, T8 | A |
| CHAT-NF-001 | Performance | 5.1 | 1, 13 | `relay/events/chat.py` | TC-PERF-01 | Sprint 2 | T9 | A |
| CHAT-NF-002 | Reliability | 5.1 | 2 | `relay/templates/index.html` | TC-REL-01 | Sprint 1 | T6 | A |
| CHAT-NF-003 | Usability | 5.1 | 5.2, 5.7 | `relay/events/_ack.py` | TC-UX-01 | Sprint 2 | T9 | P |
| CHAT-NF-004 | Robustness | 5.1 | 2 | `run.py` | TC-ROB-01 | Sprint 1 | T6 | A |
| CHAT-NF-005 | Scalability | 5.1 | 13 | `relay/events/connection.py` | TC-SCALE-01 | Sprint 2 | T9 | A |
| CHAT-NF-006 | Reliability | 5.1 | 5.7 | `relay/models/message.py` | TC-ORD-01 | Sprint 1 | T6 | A |
| CHAT-NF-007 | Reliability | 5.1 | 2, 4.3 | `run.py` | TC-REL-02 | Sprint 2 | T9 | P |
| CHAT-NF-008 | Compatibility | 5.1 | 4.3, 10 | `relay/services/files.py` | TC-COMP-01 | Sprint 2 | T9 | P |
| CHAT-NF-009 | Maintainability | 5.1 | 13 | `tests/` | TC-MAINT-01 | Sprint 2 | S5 | P |
| CHAT-NF-010 | Portability | 5.1 | 1 | `run-demo.bat` | TC-PORT-01 | Sprint 2 | T9, P3 | A |
| CHAT-NF-011 | Data retention | 5.1 | 7, 10 | `relay/services/audit.py` | TC-DATA-01 | Sprint 2 | B12 | A |
| CHAT-SR-001 | Security: Reject invalid connections | 6.1 | 5.2, 10 | `relay/events/_ack.py` | TC-SEC-01 | Sprint 1 | T6 | A |
| CHAT-SR-002 | Security: No duplicate usernames | 6.1 | 5.8, 7 | `relay/models/user.py` | TC-SEC-02 | Sprint 1 | T3 | A |
| CHAT-SR-003 | Security: Private-message routing | 6.1 | 5.1, 10 | `relay/services/rooms.py` | TC-SEC-03 | Sprint 1 | T6 | A |
| CHAT-SR-004 | Security: Validate message data | 6.1 | 5.6, 10 | `relay/services/messages.py` | TC-SEC-04 | Sprint 1 | T4 | A |
| CHAT-SR-005 | Security: No use of dead sockets | 6.1 | 5.2, 10 | `relay/events/_ack.py` | TC-SEC-05 | Sprint 1 | T6 | A |
| CHAT-SR-006 | Security: Salted password hashing | 6.1 | 10 | `relay/services/auth.py` | TC-SEC-06 | Sprint 1 | T3 | A |
| CHAT-SR-007 | Security: Session-authenticated sockets | 6.1 | 5.2, 10 | `relay/events/connection.py` | TC-SEC-07 | Sprint 1 | T6 | A |
| CHAT-SR-008 | Security: Server-side authorisation | 6.1 | 10 | `relay/services/` | TC-SEC-08 | Sprint 2 | T5, T8 | A |
| CHAT-SR-009 | Security: XSS-safe rendering + CSP | 6.1 | 9, 10 | `relay/static/js/dom.js` | TC-SEC-09 | Sprint 1 | T1, F3 | A |
| CHAT-SR-010 | Security: Upload validation | 6.1 | 10 | `relay/services/files.py` | TC-SEC-10 | Sprint 2 | T7 | A |
| CHAT-SR-011 | Security: ORM-only SQL, length limits | 6.1 | 10 | `relay/models/` | TC-SEC-11 | Sprint 2 | T4, T7 | A |
| CHAT-SR-012 | Security: Admin role + audit | 6.1 | 7, 10 | `relay/services/audit.py` | TC-SEC-12 | Sprint 2 | T8 | A |
| CHAT-SR-013 | Security: Revocation on ban/logout | 6.1 | 8.2, 10 | `relay/services/auth.py` | TC-SEC-13 | Sprint 2 | T3, T8 | A |
| CHAT-SR-014 | Security: Origin-restricted WebSocket | 6.1 | 4.3, 10 | `relay/__init__.py` | TC-SEC-14 | Sprint 2 | T9 | A |

---

## 8. Appendix A: Deviations from SRS v1.0

In accordance with course deliverable guidelines, all technical, architectural, and procedural deviations from the preliminary SRS v1.0 submitted at project inception are formally recorded below with technical rationales:

### 1. Transport Protocol: Raw Sockets to Flask-SocketIO (WebSocket)
- **v1.0 Proposal:** Custom low-level TCP socket server using Python standard library `socket` and threading (CHAT-F-001).
- **v2.0 Realization:** Standardized on Flask-SocketIO 5.3 over persistent WebSockets (`simple-websocket`).
- **Rationale:** Building a browser-accessible web application requires standard web transport protocols. WebSocket provides bidirectional frame multiplexing, automatic reconnection, heartbeat keep-alives, and room broadcasting out of the box, reducing boilerplate and improving stability.

### 2. Client Architecture: Desktop GUI / CLI to Web Application
- **v1.0 Proposal:** Native desktop client or terminal console interface.
- **v2.0 Realization:** Responsive browser client built with Vanilla ES modules and modern CSS.
- **Rationale:** A browser-based interface eliminates client installation hurdles, allows multi-device evaluation across local networks, and integrates seamlessly with standard web media rendering (inline image previews, responsive layouts).

### 3. Identity and Authentication: Ephemeral Nicknames to Salted Accounts
- **v1.0 Proposal:** Ephemeral nickname entry at runtime prompt without persistence.
- **v2.0 Realization:** Persistent user accounts with salted scrypt password hashing, session cookies, and role-based permissions (`user`, `admin`).
- **Rationale:** Necessary to support offline message delivery, deterministic direct message pairing, administrative bans/mutes, and tamper-resistant audit trails.

### 4. Scope Prioritization: MoSCoW Realignment
- **v1.0 Proposal:** Baseline feature set of 17 functional requirements without sprint partition.
- **v2.0 Realization:** Rigorous MoSCoW classification fixing 39 FRs across Sprint 1 and 2, while deferring 13 complex secondary features (reactions, threads, pins, mentions) to the backlog.
- **Rationale:** Adheres to course time constraints (two 1-week sprints) while delivering a bulletproof, fully tested core messaging and moderation product.

### 5. Persistence Subsystem: In-Memory / Flat Files to SQLite via SQLAlchemy
- **v1.0 Proposal:** Unstructured flat file logging or purely ephemeral in-memory structures.
- **v2.0 Realization:** Relational schema managed via Flask-SQLAlchemy 3.1 on SQLite 3 with WAL journal mode.
- **Rationale:** Guarantees ACID transactional semantics, autoincrement primary-key chronological ordering, indexing for rapid history pagination, and complete SQL injection immunity.

### 6. Team Role Allocation: Course Baseline
- **v1.0 Proposal:** Generic developer roles with overlapping responsibilities.
- **v2.0 Realization:** Specialized role distribution: Developer 1 (Backend & Repo Owner), Developer 2 (Frontend & QA), Scrum Master (Process & Governance), and Product Owner (Requirements & Acceptance).
- **Rationale:** Enforces clean separation of concerns, single-owner file boundaries, and prevents merge conflicts during rapid parallel development.

### 7. Requirement Classification and Identifiers
- **v1.0 Proposal:** 17 initial functional requirements (`CHAT-F-001` through `017`), 6 NFRs, and 5 SRs.
- **v2.0 Realization:** Maintained all original 17 FRs, 6 NFRs, and 5 SRs verbatim, while appending new concrete requirements to reach 52 FRs, 11 NFRs, and 14 SRs (77 total requirements).
- **Rationale:** Preserves historical traceability from SRS v1.0 without breaking existing requirement keys.

### 8. Tracking and Governance (Jira Dropped, Control v1.1)
- **v1.0 Proposal:** Informal task coordination or dual tracking via Jira.
- **v2.0 Realization:** Centralized tracking exclusively on GitHub Issues and one linked GitHub Project ('Relay') with Story Points, Sprint iteration, and Status per card, dropping external Jira synchronization as decided in Control v1.1. Branches, commits, and PRs track directly by Registry ID and issue numbers (`Closes #NN`).
- **Rationale:** Eliminates synchronization drift between disjoint platforms, integrates cleanly with GitHub Actions CI, and provides evaluators with a single source of truth.

### 9. Team Roles Re-Split (2026-11-07)
- **Initial Plan:** Developer 2 focused exclusively on frontend; testing distributed casually among members; Scrum Master and Product Owner writing peripheral application code.
- **v2.0 Realization:** Malepati Viswajith (Developer 2) combines frontend development with full test engineering ownership (all automated tests `T1`–`T9` and test records). Medha Singh (Scrum Master) and Naivadh Shrivastava (Product Owner) manage agile governance, specifications, acceptance, and releases with zero product code changes.
- **Rationale:** Streamlines automated testing under a single coordinated test harness, eliminates cross-member merge contention, and ensures dedicated leadership over verification and quality.

### 10. Sprint Schedule Realignment
- **Initial Plan:** Official course sprint windows were 19 Oct to 23 Oct 2026 (Sprint 1) and 26 Oct to 30 Oct 2026 (Sprint 2).
- **v2.0 Realization:** The team did not deliver within the preliminary course windows and conducted a team restart on 2026-11-07 under a single control file. Actual implementation and PR merges on the fresh repository took place between 12 Nov and 15 Nov 2026 (Sprint 1 merged 12–14 Nov, Sprint 2 merged 14–15 Nov, final acceptance on 16 Nov).
- **Rationale:** Honestly documents schedule slippage and recovery history for examiners as required by course rule 5 and the sprint plan.

### 11. Sprint Mapping Adjustments for F-038 and F-052
- **Initial Plan:** Inline image previews (F-038) and client/activity monitoring (F-052) were tentatively slated for Sprint 1.
- **v2.0 Realization:** Moved both to Sprint 2 because F-038 depends on file upload infrastructure (B11) and F-052 depends on the administrative moderation service (B12).
- **Rationale:** Aligns feature implementation with underlying service dependencies and prevents blocking Sprint 1 core chat deliverables.

### 12. Deferral of 13 Could-Tier Features to Backlog
- **Initial Plan:** Extended feature wishlist including invite code regeneration, owner room management, reactions, threads, pins, mentions, markdown, slash commands, notifications, export, profiles, blocking, and admin room deletion.
- **v2.0 Realization:** Formally categorized F-024, F-025, F-031–F-036, F-042–F-045, and F-050 as Could-tier and preserved in the backlog without active implementation.
- **Rationale:** Keeps team focus strictly on delivering rock-solid core real-time messaging, presence, file exchange, and moderation within two sprints.

### 13. Test-Case Identifier Standardization
- **Initial Plan:** Generic test case labels (`TC-01`, `TC-N01`, `TC-S01`).
- **v2.0 Realization:** Realigned to structured domain test case IDs matching the backlog and test plan (`TC-CON-01`, `TC-PERF-01`, `TC-SEC-14`, etc.).
- **Rationale:** Maintains 1:1 cross-referencing between test automation files, manual test records, and the requirements matrix.
