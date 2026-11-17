/**
 * F3: Central client-side application store.
 * All application state mutations happen through the exported actions.
 */

export const state = {
    me: null,
    view: "login",
    connection: "offline",
    rooms: new Map(),
    activeRoomId: null,
    messages: new Map(),
    hasMore: new Map(),
    pending: new Map(),
    unread: new Map(),
    receipts: new Map(),
    online: new Map(),
    typing: new Map(),
    notices: new Map()
};

const listeners = new Set();
const typingTimers = new Map();

function notify() {
    for (const listener of [...listeners]) {
        try {
            listener(state);
        } catch (error) {
            console.error("Store subscriber failed:", error);
        }
    }
}

function getId(value) {
    if (value && typeof value === "object") {
        return value.id ?? value.user_id ?? value.room_id ?? null;
    }
    return value ?? null;
}

function findMapKey(map, id) {
    if (map.has(id)) return id;

    const wanted = String(id);
    for (const key of map.keys()) {
        if (String(key) === wanted) return key;
    }

    return id;
}

function canonicalRoomId(roomId) {
    return findMapKey(state.rooms, roomId);
}

function numericId(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function sortMessages(messages) {
    return messages.sort((a, b) => {
        const left = a.id;
        const right = b.id;

        if (typeof left === "number" && typeof right === "number") {
            return left - right;
        }

        return String(left).localeCompare(String(right), undefined, {
            numeric: true
        });
    });
}

function isOwnMessage(message) {
    if (!message || !state.me) return false;

    const senderId =
        message.sender?.id ??
        message.sender_id ??
        message.user_id;

    if (senderId != null && state.me.id != null) {
        return String(senderId) === String(state.me.id);
    }

    const senderName =
        typeof message.sender === "string"
            ? message.sender
            : message.sender?.username;

    return Boolean(
        senderName &&
        state.me.username &&
        senderName === state.me.username
    );
}

function clearTypingTimer(roomId, userId) {
    const timerKey = JSON.stringify([roomId, userId]);
    const timer = typingTimers.get(timerKey);

    if (timer !== undefined) {
        clearTimeout(timer);
        typingTimers.delete(timerKey);
    }
}

/**
 * Subscribe to state changes.
 * Returns an unsubscribe function.
 */
export function subscribe(listener) {
    if (typeof listener !== "function") {
        throw new TypeError("Store subscriber must be a function.");
    }

    listeners.add(listener);

    return () => {
        listeners.delete(listener);
    };
}

export function setMe(user) {
    state.me = user ?? null;
    notify();
}

export function setView(view) {
    if (!["login", "chat", "admin"].includes(view)) {
        throw new TypeError("Invalid application view.");
    }

    state.view = view;
    notify();
}

export function setConnection(connection) {
    if (!["connected", "reconnecting", "offline"].includes(connection)) {
        throw new TypeError("Invalid connection status.");
    }

    state.connection = connection;
    notify();
}

export function setRooms(rooms) {
    const list = rooms instanceof Map
        ? [...rooms.values()]
        : rooms;

    if (!Array.isArray(list)) {
        throw new TypeError("Rooms must be an array or Map.");
    }

    const next = new Map();

    for (const room of list) {
        const id = getId(room);
        if (id == null) continue;
        next.set(id, room);
    }

    state.rooms = next;
    notify();
}

export function upsertRoom(room) {
    const id = getId(room);

    if (id == null) {
        throw new TypeError("Room must have an id.");
    }

    const key = findMapKey(state.rooms, id);
    state.rooms.set(key, room);
    notify();
}

export function removeRoom(roomId) {
    const id = canonicalRoomId(roomId);

    state.rooms.delete(id);
    state.messages.delete(id);
    state.hasMore.delete(id);
    state.unread.delete(id);
    state.receipts.delete(id);
    state.typing.delete(id);
    state.notices.delete(id);

    if (String(state.activeRoomId) === String(id)) {
        state.activeRoomId = null;
    }

    for (const [clientId, entry] of state.pending) {
        if (String(entry.roomId) === String(id)) {
            state.pending.delete(clientId);
        }
    }

    for (const timerKey of [...typingTimers.keys()]) {
        try {
            const [timerRoomId, timerUserId] = JSON.parse(timerKey);
            if (String(timerRoomId) === String(id)) {
                clearTypingTimer(timerRoomId, timerUserId);
            }
        } catch (_error) {
            // Ignore malformed internal timer keys.
        }
    }

    notify();
}

export function setActiveRoom(roomId) {
    state.activeRoomId = roomId ?? null;
    notify();
}

/**
 * Merge messages by ID and maintain ascending ID order.
 * A confirmed message removes its matching pending client_id.
 */
export function addMessages(roomId, messages, { older = false } = {}) {
    if (!Array.isArray(messages)) {
        throw new TypeError("Messages must be an array.");
    }

    const id = canonicalRoomId(roomId);
    const existing = state.messages.get(id) ?? [];
    const merged = new Map(existing.map(message => [message.id, message]));

    for (const message of messages) {
        if (message?.id == null) continue;

        merged.set(message.id, message);

        if (message.client_id != null) {
            state.pending.delete(message.client_id);
        }
    }

    // Both older and newer pages are merged by ID, never by timestamp.
    // The resulting list remains oldest-first.
    state.messages.set(id, sortMessages([...merged.values()]));
    notify();
}

export function addPending(clientId, roomId, body) {
    if (typeof clientId !== "string" || !clientId.trim()) {
        throw new TypeError("Pending message requires a client ID.");
    }

    const id = canonicalRoomId(roomId);

    state.pending.set(clientId, {
        roomId: id,
        body,
        failed: false
    });

    notify();
}

export function failPending(clientId) {
    const entry = state.pending.get(clientId);

    if (entry) {
        state.pending.set(clientId, {
            ...entry,
            failed: true
        });
    }

    notify();
}

export function setHasMore(roomId, hasMore) {
    const id = canonicalRoomId(roomId);
    state.hasMore.set(id, Boolean(hasMore));
    notify();
}

export function setUnread(unreadMap) {
    const entries = unreadMap instanceof Map
        ? [...unreadMap.entries()]
        : Object.entries(unreadMap ?? {});

    const next = new Map();

    for (const [roomId, count] of entries) {
        next.set(canonicalRoomId(roomId), Math.max(0, numericId(count)));
    }

    state.unread = next;
    notify();
}

export function bumpUnread(roomId, message = null) {
    const id = canonicalRoomId(roomId);

    // No unread increments for the active room or our own messages.
    if (String(state.activeRoomId) === String(id)) return;
    if (message && isOwnMessage(message)) return;

    const current = state.unread.get(id) ?? 0;
    state.unread.set(id, current + 1);
    notify();
}

export function clearUnread(roomId) {
    const id = canonicalRoomId(roomId);
    state.unread.set(id, 0);
    notify();
}

export function setReceipts(roomId, receipts) {
    if (!Array.isArray(receipts)) {
        throw new TypeError("Receipts must be an array.");
    }

    const id = canonicalRoomId(roomId);
    const next = new Map();

    for (const receipt of receipts) {
        const userId = getId(receipt);
        if (userId == null) continue;

        const delivered = numericId(receipt.delivered_up_to);
        const read = numericId(receipt.read_up_to);

        next.set(userId, {
            delivered_up_to: Math.max(delivered, read),
            read_up_to: read
        });
    }

    state.receipts.set(id, next);
    notify();
}

export function updateReceipt(receipt) {
    const roomId = canonicalRoomId(receipt?.room_id);
    const userId = receipt?.user_id;

    if (roomId == null || userId == null) {
        throw new TypeError("Receipt requires room_id and user_id.");
    }

    const roomReceipts = state.receipts.get(roomId) ?? new Map();
    const previous = roomReceipts.get(userId) ?? {
        delivered_up_to: 0,
        read_up_to: 0
    };

    const read = Math.max(
        previous.read_up_to,
        numericId(receipt.read_up_to)
    );

    const delivered = Math.max(
        previous.delivered_up_to,
        read,
        numericId(receipt.delivered_up_to)
    );

    roomReceipts.set(userId, {
        delivered_up_to: delivered,
        read_up_to: read
    });

    state.receipts.set(roomId, roomReceipts);
    notify();
}

export function setOnline(users) {
    if (!Array.isArray(users)) {
        throw new TypeError("Online users must be an array.");
    }

    const next = new Map();

    for (const user of users) {
        const id = getId(user);
        if (id != null) next.set(id, user);
    }

    state.online = next;
    notify();
}

export function setPresence(user, online) {
    const id = getId(user);

    if (id == null) {
        throw new TypeError("Presence user must have an ID.");
    }

    const key = findMapKey(state.online, id);

    if (online) {
        state.online.set(key, user);
    } else {
        state.online.delete(key);
    }

    notify();
}

/**
 * Typing entries expire after four seconds without a refresh.
 */
export function setTyping(roomId, user, isTyping) {
    const id = canonicalRoomId(roomId);
    const userId = getId(user);

    if (id == null || userId == null) {
        throw new TypeError("Typing update requires room and user IDs.");
    }

    const roomTyping = state.typing.get(id) ?? new Map();

    clearTypingTimer(id, userId);

    if (!isTyping) {
        roomTyping.delete(userId);

        if (roomTyping.size === 0) {
            state.typing.delete(id);
        } else {
            state.typing.set(id, roomTyping);
        }

        notify();
        return;
    }

    const entry = {
        username: user.username ?? "",
        until: Date.now() + 4000
    };

    roomTyping.set(userId, entry);
    state.typing.set(id, roomTyping);

    const timerKey = JSON.stringify([id, userId]);

    const timer = setTimeout(() => {
        const current = state.typing.get(id);
        const currentEntry = current?.get(userId);

        if (currentEntry && currentEntry.until <= Date.now()) {
            current.delete(userId);

            if (current.size === 0) {
                state.typing.delete(id);
            }

            notify();
        }

        typingTimers.delete(timerKey);
    }, 4000);

    typingTimers.set(timerKey, timer);
    notify();
}

export function addNotice(roomId, text) {
    const id = canonicalRoomId(roomId);
    const notices = state.notices.get(id) ?? [];

    notices.push({
        text: String(text),
        created_at: new Date().toISOString()
    });

    // Keep recent notices bounded.
    if (notices.length > 100) {
        notices.splice(0, notices.length - 100);
    }

    state.notices.set(id, notices);
    notify();
}

/**
 * Build the sync cursor object from the latest loaded message ID
 * in each room. Rooms without loaded messages are omitted.
 */
export function cursors() {
    const result = {};

    for (const [roomId, messages] of state.messages) {
        if (!messages.length) continue;

        const lastMessage = messages[messages.length - 1];

        if (lastMessage?.id == null || numericId(lastMessage.id) <= 0) {
            continue;
        }

        result[String(roomId)] = lastMessage.id;
    }

    return result;
}
