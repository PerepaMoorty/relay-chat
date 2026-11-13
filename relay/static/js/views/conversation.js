/**
 * F6: Conversation view.
 * Handles message rendering, history paging, receipts, edit/delete,
 * typing indicators, room notices and attachment previews.
 */

import { api } from "../api.js";
import { emitAck } from "../socket.js";
import {
    state,
    subscribe,
    addMessages,
    setHasMore,
    setReceipts,
    updateReceipt,
    removeRoom,
    setActiveRoom
} from "../store.js";
import { $, el, clear, formatTime, formatDay, formatSize } from "../dom.js";

const PAGE_SIZE = 50;
const SCROLL_THRESHOLD = 80;
const BOTTOM_THRESHOLD = 120;

let mounted = false;
let callbacks = {};

let activeRoomId = null;
let requestToken = 0;
let historyError = "";
let historyLoading = false;
let loadingOlder = false;
let olderSnapshot = null;
let editingMessageId = null;

const latestSeen = new Map();
const lastDelivered = new Map();
const lastRead = new Map();

function getElements() {
    return {
        panel: document.querySelector(".conversation-panel"),
        title: $("conversation-title"),
        subtitle: $("conversation-subtitle"),
        inviteChip: $("invite-code-chip"),
        leaveButton: $("leave-room-button"),
        searchButton: $("conversation-search-button"),
        messageList: $("message-list"),
        typingLine: $("typing-line")
    };
}

function text(value) {
    return value == null ? "" : String(value);
}

function roomKey(roomId) {
    if (roomId == null) return roomId;
    if (state.messages.has(roomId)) return roomId;
    if (state.rooms.has(roomId)) return roomId;

    const wanted = String(roomId);

    for (const map of [state.messages, state.rooms]) {
        for (const key of map.keys()) {
            if (String(key) === wanted) return key;
        }
    }

    return roomId;
}

function getRoom(roomId) {
    const key = roomKey(roomId);
    return state.rooms.get(key) ?? null;
}

function getRoomMessages(roomId) {
    const key = roomKey(roomId);
    return state.messages.get(key) ?? [];
}

function getRoomReceipts(roomId) {
    const key = roomKey(roomId);
    return state.receipts.get(key) ?? new Map();
}

function getMapValue(map, key) {
    if (map.has(key)) return map.get(key);

    for (const [candidate, value] of map) {
        if (String(candidate) === String(key)) return value;
    }

    return undefined;
}

function compareIds(left, right) {
    const a = Number(left);
    const b = Number(right);

    if (Number.isFinite(a) && Number.isFinite(b)) {
        return a - b;
    }

    return String(left).localeCompare(String(right), undefined, {
        numeric: true
    });
}

function isOwnMessage(message) {
    const me = state.me;
    if (!me || !message) return false;

    const senderId =
        message.sender?.id ??
        message.sender_id ??
        message.user_id;

    if (senderId != null && me.id != null) {
        return String(senderId) === String(me.id);
    }

    const username =
        typeof message.sender === "string"
            ? message.sender
            : message.sender?.username;

    return Boolean(username && username === me.username);
}

function getSenderName(message) {
    if (isOwnMessage(message)) return "You";

    if (typeof message.sender === "string") {
        return message.sender;
    }

    return message.sender?.username || "Unknown user";
}

function isVisibleAndFocused() {
    const { panel, messageList } = getElements();

    if (!panel || !messageList) return false;
    if (state.view !== "chat") return false;
    if (document.visibilityState !== "visible") return false;
    if (typeof document.hasFocus === "function" && !document.hasFocus()) {
        return false;
    }

    return messageList.getClientRects().length > 0 &&
        panel.getClientRects().length > 0;
}

function updateHeader(room) {
    const {
        title,
        subtitle,
        inviteChip,
        leaveButton,
        searchButton
    } = getElements();

    if (!room) {
        if (title) title.textContent = "Choose a conversation";

        if (subtitle) {
            subtitle.textContent =
                "Your team conversations, all in one place";
        }

        if (inviteChip) {
            inviteChip.textContent = "";
            inviteChip.hidden = true;
        }

        if (leaveButton) leaveButton.hidden = true;
        if (searchButton) searchButton.disabled = true;

        return;
    }

    if (title) {
        if (room.kind === "direct") {
            title.textContent =
                room.peer?.username || room.name || "Direct message";
        } else {
            title.textContent = `#${room.name || "room"}`;
        }
    }

    if (subtitle) {
        if (room.kind === "direct") {
            const peer = room.peer;
            const online = peer
                ? Boolean(getMapValue(state.online, peer.id))
                : false;

            if (online) {
                subtitle.textContent = "Online";
            } else if (peer?.last_seen_at) {
                subtitle.textContent =
                    `Last seen ${formatTime(peer.last_seen_at)}`;
            } else {
                subtitle.textContent = "Direct conversation";
            }
        } else {
            const count = Number(room.member_count);

            subtitle.textContent = Number.isFinite(count)
                ? `${count} ${count === 1 ? "member" : "members"}`
                : "Workspace conversation";
        }
    }

    if (inviteChip) {
        const hasInvite =
            room.kind === "group" &&
            Boolean(room.invite_code);

        inviteChip.textContent = hasInvite
            ? `Invite: ${room.invite_code}`
            : "";

        inviteChip.hidden = !hasInvite;
    }

    if (leaveButton) {
        leaveButton.hidden = room.kind !== "group";
    }

    if (searchButton) {
        searchButton.disabled = false;
    }
}

function appendDaySeparator(container, day) {
    container.appendChild(
        el("div", { class: "message-day-separator" },
            el("span", {}, day))
    );
}

function safeAttachmentUrl(rawUrl) {
    if (typeof rawUrl !== "string" || !rawUrl.startsWith("/")) {
        return null;
    }

    try {
        const url = new URL(rawUrl, window.location.origin);

        if (url.origin !== window.location.origin) return null;
        if (!url.pathname.startsWith("/api/files/")) return null;

        return url.href;
    } catch (_error) {
        return null;
    }
}

function renderAttachment(attachment) {
    if (!attachment) return null;

    const url = safeAttachmentUrl(attachment.url);
    const name = text(attachment.name || "Attachment");
    const size = formatSize(attachment.size);

    const wrapper = el("div", { class: "message-attachment" });

    if (!url) {
        wrapper.appendChild(
            el("span", {}, `${name} · ${size}`)
        );
        return wrapper;
    }

    const link = el("a", {
        href: url,
        target: "_blank",
        rel: "noopener noreferrer",
        class: "attachment-link"
    });

    if (attachment.is_image) {
        link.appendChild(
            el("img", {
                src: url,
                alt: name,
                width: "280",
                loading: "lazy",
                class: "message-attachment-image"
            })
        );

        link.appendChild(
            el("span", {}, name)
        );
    } else {
        link.textContent = `${name} · ${size}`;
        link.setAttribute("download", name);
    }

    wrapper.appendChild(link);
    return wrapper;
}

function receiptForMessage(message, room, receipts, isLatestOwn) {
    if (!isOwnMessage(message) || !room) return null;

    const receiptEntries = [...receipts.entries()];
    const meId = state.me?.id;

    if (room.kind === "direct") {
        const peerId = room.peer?.id;
        if (peerId == null) return el("span", {
            class: "message-receipt",
            "aria-label": "Sent"
        }, "✓ Sent");

        const peerReceipt = getMapValue(receipts, peerId);

        const delivered = Number(peerReceipt?.delivered_up_to ?? 0);
        const read = Number(peerReceipt?.read_up_to ?? 0);
        const messageId = Number(message.id);

        if (read >= messageId) {
            return el("span", {
                class: "message-receipt",
                "aria-label": "Read"
            }, "✓✓ Read");
        }

        if (delivered >= messageId) {
            return el("span", {
                class: "message-receipt",
                "aria-label": "Delivered"
            }, "✓✓ Delivered");
        }

        return el("span", {
            class: "message-receipt",
            "aria-label": "Sent"
        }, "✓ Sent");
    }

    if (room.kind === "group" && isLatestOwn) {
        const messageId = Number(message.id);

        const readers = receiptEntries.filter(([userId, receipt]) => {
            if (meId != null && String(userId) === String(meId)) {
                return false;
            }

            return Number(receipt?.read_up_to ?? 0) >= messageId;
        }).length;

        if (readers > 0) {
            return el("span", {
                class: "message-receipt",
                "aria-label": `Read by ${readers}`
            }, `Read by ${readers}`);
        }
    }

    return null;
}

function beginEdit(message, container) {
    editingMessageId = message.id;
    render(state);

    const editor = container.querySelector(".message-edit-input");
    if (editor) {
        editor.focus();
        editor.setSelectionRange(
            editor.value.length,
            editor.value.length
        );
    }
}

function renderEditForm(message, container) {
    const form = el("form", { class: "message-edit-form" });

    const textarea = el("textarea", {
        class: "text-input message-edit-input",
        rows: "3",
        maxlength: "4000",
        required: true,
        "aria-label": "Edit message"
    });

    textarea.value = message.body || "";

    const error = el("p", {
        class: "inline-error",
        role: "alert",
        hidden: true
    });

    const actions = el("div", { class: "message-actions" });
    const save = el("button", {
        type: "submit",
        class: "button button-primary"
    }, "Save");

    const cancel = el("button", {
        type: "button",
        class: "button button-quiet"
    }, "Cancel");

    cancel.addEventListener("click", () => {
        editingMessageId = null;
        render(state);
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();

        const body = textarea.value.trim();

        if (!body) {
            error.textContent = "Message cannot be empty.";
            error.hidden = false;
            return;
        }

        if (body.length > 4000) {
            error.textContent = "Message cannot exceed 4000 characters.";
            error.hidden = false;
            return;
        }

        save.disabled = true;
        error.hidden = true;

        try {
            const result = await emitAck("message:edit", {
                message_id: message.id,
                body
            });

            if (!result?.message) {
                throw new Error("The server did not return the updated message.");
            }

            editingMessageId = null;
            addMessages(message.room_id, [result.message]);
        } catch (editError) {
            error.textContent = editError.message ||
                "Could not update this message.";
            error.hidden = false;
            save.disabled = false;
        }
    });

    actions.append(save, cancel);
    form.append(textarea, error, actions);
    container.appendChild(form);
}

function renderMessageActions(message, bubble) {
    if (!isOwnMessage(message) || message.deleted) {
        // F10 can attach its report action to this message container.
        if (!isOwnMessage(message)) {
            bubble.setAttribute("data-report-message-id", text(message.id));
        }
        return;
    }

    const actions = el("div", { class: "message-actions" });

    const edit = el("button", {
        type: "button",
        class: "button button-quiet"
    }, "Edit");

    const remove = el("button", {
        type: "button",
        class: "button button-quiet button-danger-text"
    }, "Delete");

    edit.addEventListener("click", () => {
        beginEdit(message, bubble);
    });

    remove.addEventListener("click", async () => {
        const accepted = window.confirm("Delete this message?");
        if (!accepted) return;

        remove.disabled = true;

        try {
            await emitAck("message:delete", {
                message_id: message.id
            });

            const deletedMessage = {
                ...message,
                body: "",
                deleted: true,
                attachment: null
            };

            addMessages(message.room_id, [deletedMessage]);
        } catch (error) {
            window.alert(error.message || "Could not delete this message.");
            remove.disabled = false;
        }
    });

    actions.append(edit, remove);
    bubble.appendChild(actions);
}

function renderMessage(message, room, receipts, latestOwnId) {
    const own = isOwnMessage(message);

    const row = el("article", {
        class: own ? "message-row message-own" : "message-row message-other",
        "data-message-id": text(message.id),
        "data-report-message-id": own ? null : text(message.id)
    });

    const bubble = el("div", {
        class: "message-bubble"
    });

    const meta = el("div", { class: "message-meta" });

    meta.appendChild(
        el("strong", { class: "message-sender" }, getSenderName(message))
    );

    meta.appendChild(
        el("time", {
            class: "message-time",
            datetime: text(message.created_at),
            title: text(message.created_at)
        }, formatTime(message.created_at))
    );

    if (message.edited_at) {
        meta.appendChild(
            el("span", { class: "message-edited" }, "(edited)")
        );
    }

    bubble.appendChild(meta);

    if (editingMessageId != null &&
        String(editingMessageId) === String(message.id)) {
        renderEditForm(message, bubble);
    } else if (message.deleted) {
        bubble.appendChild(
            el("p", { class: "message-body message-deleted" },
                "message deleted")
        );
    } else {
        if (message.body) {
            bubble.appendChild(
                el("p", { class: "message-body" }, message.body)
            );
        }

        if (message.attachment) {
            const attachment = renderAttachment(message.attachment);
            if (attachment) bubble.appendChild(attachment);
        }
    }

    const latestOwn = own &&
        latestOwnId != null &&
        String(message.id) === String(latestOwnId);

    const receipt = receiptForMessage(
        message,
        room,
        receipts,
        latestOwn
    );

    if (receipt) {
        bubble.appendChild(receipt);
    }

    if (own && !message.deleted &&
        String(editingMessageId) !== String(message.id)) {
        renderMessageActions(message, bubble);
    } else if (!own) {
        // Stable hook for F10's report control.
        bubble.setAttribute("data-report-message-id", text(message.id));
    }

    row.appendChild(bubble);
    return row;
}

function renderPendingMessages(roomId, container) {
    for (const [clientId, pending] of state.pending) {
        if (String(pending.roomId) !== String(roomId)) continue;

        const row = el("article", {
            class: "message-row message-own message-pending",
            "data-client-id": clientId
        });

        const bubble = el("div", { class: "message-bubble" });

        bubble.appendChild(
            el("p", { class: "message-body" }, pending.body || "")
        );

        bubble.appendChild(
            el("span", { class: "muted-small" },
                pending.failed ? "Failed to send" : "Sending…")
        );

        if (pending.failed && typeof callbacks.onRetryPending === "function") {
            const retry = el("button", {
                type: "button",
                class: "button button-quiet"
            }, "Retry");

            retry.addEventListener("click", () => {
                callbacks.onRetryPending(clientId, pending);
            });

            bubble.appendChild(retry);
        }

        row.appendChild(bubble);
        container.appendChild(row);
    }
}

function renderNotices(roomId, container) {
    const notices = getMapValue(state.notices, roomId) ?? [];

    for (const notice of notices) {
        container.appendChild(
            el("div", { class: "message-notice", role: "status" },
                notice.text || "")
        );
    }
}

function renderHistoryError(container) {
    if (!historyError) return;

    const wrapper = el("div", {
        class: "conversation-history-error",
        role: "alert"
    });

    wrapper.appendChild(el("p", {}, historyError));

    const retry = el("button", {
        type: "button",
        class: "button button-secondary"
    }, "Retry");

    retry.addEventListener("click", () => {
        if (activeRoomId == null) return;

        if (state.messages.get(roomKey(activeRoomId))?.length) {
            loadOlderMessages(activeRoomId);
        } else {
            loadLatestMessages(activeRoomId);
        }
    });

    wrapper.appendChild(retry);
    container.appendChild(wrapper);
}

function isNearBottom(node) {
    return node.scrollHeight - node.scrollTop - node.clientHeight
        <= BOTTOM_THRESHOLD;
}

function renderMessages(appState) {
    const { messageList } = getElements();
    if (!messageList) return;

    const roomId = appState.activeRoomId;

    const oldHeight = messageList.scrollHeight;
    const oldTop = messageList.scrollTop;
    const nearBottom = isNearBottom(messageList);
    const snapshot = olderSnapshot;

    clear(messageList);

    if (roomId == null) {
        messageList.appendChild(
            el("div", { class: "conversation-welcome" },
                el("div", { class: "welcome-symbol", "aria-hidden": "true" }, "✳"),
                el("h2", {}, "Your next good conversation starts here."),
                el("p", {}, "Select a room or start a direct message with someone from your workspace.")
            )
        );

        return;
    }

    const room = getRoom(roomId);
    const messages = getRoomMessages(roomId);
    const receipts = getRoomReceipts(roomId);

    if (!room) {
        messageList.appendChild(
            el("div", { class: "sidebar-empty" },
                "This conversation is no longer available.")
        );
        return;
    }

    if (historyLoading && messages.length === 0) {
        messageList.appendChild(
            el("div", { class: "sidebar-empty" }, "Loading messages…")
        );
    }

    if (messages.length === 0 && !historyLoading && !historyError) {
        messageList.appendChild(
            el("div", { class: "sidebar-empty" },
                "No messages yet. Start the conversation.")
        );
    }

    const ownMessages = messages.filter(isOwnMessage);
    const latestOwnId = ownMessages.length
        ? ownMessages[ownMessages.length - 1].id
        : null;

    let previousDay = null;

    for (const message of messages) {
        const day = formatDay(message.created_at);

        if (day && day !== previousDay) {
            appendDaySeparator(messageList, day);
            previousDay = day;
        }

        messageList.appendChild(
            renderMessage(message, room, receipts, latestOwnId)
        );
    }

    renderPendingMessages(roomId, messageList);
    renderNotices(roomId, messageList);
    renderHistoryError(messageList);

    requestAnimationFrame(() => {
        if (snapshot && String(snapshot.roomId) === String(roomId)) {
            const heightDifference = messageList.scrollHeight -
                snapshot.scrollHeight;

            messageList.scrollTop =
                snapshot.scrollTop + heightDifference;

            olderSnapshot = null;
        } else if (nearBottom) {
            messageList.scrollTop = messageList.scrollHeight;
        } else {
            messageList.scrollTop = oldTop;
        }
    });
}

function renderTyping(appState) {
    const { typingLine } = getElements();
    if (!typingLine) return;

    const roomId = appState.activeRoomId;

    if (roomId == null) {
        typingLine.textContent = "";
        typingLine.hidden = true;
        return;
    }

    const roomTyping = getMapValue(appState.typing, roomId) ?? new Map();

    const names = [];

    for (const [userId, entry] of roomTyping) {
        if (entry.until <= Date.now()) continue;

        if (appState.me?.id != null &&
            String(userId) === String(appState.me.id)) {
            continue;
        }

        if (entry.username) names.push(entry.username);
    }

    let message = "";

    if (names.length === 1) {
        message = `${names[0]} is typing…`;
    } else if (names.length === 2) {
        message = `${names[0]} and ${names[1]} are typing…`;
    } else if (names.length > 2) {
        message = `${names[0]}, ${names[1]} and ${names.length - 2} others are typing…`;
    }

    typingLine.textContent = message;
    typingLine.hidden = !message;
}

function render(appState) {
    const room = appState.activeRoomId == null
        ? null
        : getRoom(appState.activeRoomId);

    updateHeader(room);
    renderMessages(appState);
    renderTyping(appState);
}

function currentLastMessageId(roomId) {
    const messages = getRoomMessages(roomId);
    return messages.length ? messages[messages.length - 1].id : null;
}

async function sendReceipt(roomId, field, messageId) {
    if (messageId == null || !roomId) return;

    const cache = field === "read_up_to" ? lastRead : lastDelivered;
    const previous = getMapValue(cache, roomId);

    if (previous != null && compareIds(messageId, previous) <= 0) {
        return;
    }

    const payload = {
        room_id: roomId,
        [field]: messageId
    };

    try {
        const result = await emitAck("receipt:update", payload);

        if (result) {
            updateReceipt({
                room_id: roomId,
                user_id: state.me?.id,
                delivered_up_to: result.delivered_up_to,
                read_up_to: result.read_up_to
            });
        }

        cache.set(roomKey(roomId), messageId);
    } catch (_error) {
        // The next store update, focus event or reconnect can retry.
    }
}

function maybeMarkRead() {
    if (!isVisibleAndFocused() || activeRoomId == null) return;

    const lastId = currentLastMessageId(activeRoomId);
    if (lastId == null) return;

    sendReceipt(activeRoomId, "read_up_to", lastId);
}

function observeNewMessages(appState) {
    if (!(appState.messages instanceof Map)) return;

    for (const [roomId, messages] of appState.messages) {
        if (!messages.length) continue;

        const latest = messages[messages.length - 1];
        if (latest?.id == null) continue;

        const previous = getMapValue(latestSeen, roomId);

        if (previous == null || compareIds(latest.id, previous) > 0) {
            latestSeen.set(roomId, latest.id);

            // Initial history is seeded before merging, so a first message
            // observed after mount is treated as a newly delivered message.
            sendReceipt(roomId, "delivered_up_to", latest.id);
        }
    }

    maybeMarkRead();
}

async function loadLatestMessages(roomId) {
    if (roomId == null) return;

    const token = ++requestToken;

    historyLoading = true;
    historyError = "";
    render(state);

    try {
        const data = await api(
            "GET",
            `/api/rooms/${encodeURIComponent(roomId)}/messages?limit=${PAGE_SIZE}`
        );

        if (token !== requestToken ||
            String(state.activeRoomId) !== String(roomId)) {
            return;
        }

        if (!Array.isArray(data?.messages)) {
            throw new Error("The server returned invalid message history.");
        }

        const currentLast = currentLastMessageId(roomId);
        const loadedLast = data.messages.length
            ? data.messages[data.messages.length - 1].id
            : null;

        // History is not a new live message event. Set the baseline before
        // merging it into the store so we do not mislabel old messages.
        const baseline = currentLast == null
            ? loadedLast
            : loadedLast == null
                ? currentLast
                : compareIds(currentLast, loadedLast) >= 0
                    ? currentLast
                    : loadedLast;

        if (baseline != null) {
            latestSeen.set(roomKey(roomId), baseline);
        }

        setReceipts(roomId, data.receipts ?? []);
        addMessages(roomId, data.messages);
        setHasMore(roomId, data.messages.length === PAGE_SIZE);

        historyError = "";
    } catch (error) {
        if (token === requestToken) {
            historyError = error.message || "Could not load conversation history.";
        }
    } finally {
        if (token === requestToken) {
            historyLoading = false;
            render(state);
            maybeMarkRead();
        }
    }
}

async function loadOlderMessages(roomId) {
    if (loadingOlder || roomId == null) return;

    const key = roomKey(roomId);
    if (state.hasMore.get(key) !== true) return;

    const messages = getRoomMessages(roomId);
    if (!messages.length) return;

    const oldestId = messages[0].id;
    const { messageList } = getElements();

    if (!messageList) return;

    loadingOlder = true;
    historyError = "";

    // Set the snapshot only when the older page is ready to merge.
    // Receipt and pagination updates notify subscribers synchronously.
    olderSnapshot = null;

    const token = requestToken;

    try {
        const data = await api(
            "GET",
            `/api/rooms/${encodeURIComponent(roomId)}/messages?before=${encodeURIComponent(oldestId)}&limit=${PAGE_SIZE}`
        );

        if (token !== requestToken ||
            String(state.activeRoomId) !== String(roomId)) {
            olderSnapshot = null;
            return;
        }

        if (!Array.isArray(data?.messages)) {
            throw new Error("The server returned invalid older messages.");
        }

        setReceipts(roomId, data.receipts ?? []);
        setHasMore(roomId, data.messages.length === PAGE_SIZE);

        // Capture scroll position after the other state notifications,
        // immediately before the message merge triggers the final render.
        olderSnapshot = {
            roomId,
            scrollHeight: messageList.scrollHeight,
            scrollTop: messageList.scrollTop
        };

        addMessages(roomId, data.messages, { older: true });
    } catch (error) {
        olderSnapshot = null;
        historyError = error.message || "Could not load older messages.";
        render(state);
    } finally {
        loadingOlder = false;
    }
}

function handleMessageScroll() {
    const { messageList } = getElements();
    if (!messageList || activeRoomId == null) return;

    if (messageList.scrollTop <= SCROLL_THRESHOLD) {
        loadOlderMessages(activeRoomId);
    }
}

async function handleLeaveRoom() {
    const room = getRoom(activeRoomId);

    if (!room || room.kind !== "group") return;

    const accepted = window.confirm(
        `Leave #${room.name}? You will need to rejoin to see its messages.`
    );

    if (!accepted) return;

    const { leaveButton } = getElements();
    if (leaveButton) leaveButton.disabled = true;

    try {
        await api(
            "POST",
            `/api/rooms/${encodeURIComponent(room.id)}/leave`
        );

        removeRoom(room.id);

        const general = [...state.rooms.values()].find(item =>
            item.kind === "public" ||
            text(item.name).toLowerCase() === "general"
        );

        if (general) {
            setActiveRoom(general.id);
        } else {
            setActiveRoom(null);
        }

        if (typeof callbacks.onRoomLeft === "function") {
            callbacks.onRoomLeft(room);
        }
    } catch (error) {
        window.alert(error.message || "Could not leave this room.");
    } finally {
        if (leaveButton) leaveButton.disabled = false;
    }
}

function handleFocus() {
    maybeMarkRead();
}

function handleVisibilityChange() {
    if (document.visibilityState === "visible") {
        maybeMarkRead();
    }
}

function handleStateChange(appState) {
    const nextRoomId = appState.activeRoomId;

    if (String(nextRoomId) !== String(activeRoomId)) {
        activeRoomId = nextRoomId;
        historyError = "";
        editingMessageId = null;
        historyLoading = false;
        loadingOlder = false;
        olderSnapshot = null;

        if (nextRoomId != null) {
            loadLatestMessages(nextRoomId);
        }
    }

    render(appState);
    observeNewMessages(appState);
}

function bindEvents() {
    const {
        messageList,
        leaveButton,
        searchButton
    } = getElements();

    messageList?.addEventListener("scroll", handleMessageScroll);
    leaveButton?.addEventListener("click", handleLeaveRoom);

    searchButton?.addEventListener("click", () => {
        callbacks.onSearch?.(activeRoomId);
    });

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("focus", handleFocus);
}

/**
 * Mount the conversation view.
 *
 * Options:
 * {
 *   onSearch(roomId),
 *   onRoomLeft(room),
 *   onRetryPending(clientId, pending)
 * }
 */
export function mount(options = {}) {
    if (!options || typeof options !== "object") {
        throw new TypeError("Conversation mount options must be an object.");
    }

    callbacks = {
        onSearch: options.onSearch,
        onRoomLeft: options.onRoomLeft,
        onRetryPending: options.onRetryPending
    };

    if (!mounted) {
        // Existing messages at mount time are already known; they are not
        // treated as newly delivered live messages.
        for (const [roomId, messages] of state.messages) {
            if (messages.length) {
                latestSeen.set(roomId, messages[messages.length - 1].id);
            }
        }

        bindEvents();
        subscribe(handleStateChange);
        mounted = true;
    }

    activeRoomId = state.activeRoomId;
    render(state);

    if (activeRoomId != null) {
        loadLatestMessages(activeRoomId);
    }
}

/**
 * Render the conversation UI from the shared store.
 */
export function renderView(appState) {
    if (!appState) return;

    render(appState);
}

// Standard view interface used by the app controller.
export { renderView as render };
