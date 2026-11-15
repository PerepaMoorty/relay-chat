// PR F1 — frontend scaffold placeholder. The application controller is implemented in F9.

/**
 * PR F9: Main application controller.
 * Handles boot, login/chat routing, view wiring, socket events and reconnect sync.
 */

import { api } from "./api.js";
import {
    connect,
    emitAck,
    stopReconnecting
} from "./socket.js";

import {
    state,
    subscribe,
    setMe,
    setView,
    setConnection,
    setRooms,
    upsertRoom,
    removeRoom,
    setActiveRoom,
    addMessages,
    bumpUnread,
    clearUnread,
    setUnread,
    setOnline,
    setPresence,
    setTyping,
    addNotice,
    updateReceipt,
    cursors
} from "./store.js";

import * as LoginView from "./views/login.js";
import * as SidebarView from "./views/sidebar.js";
import * as ConversationView from "./views/conversation.js";
import * as ComposerView from "./views/composer.js";
import * as DialogsView from "./views/dialogs.js";

let booting = true;
let loginMounted = false;
let sidebarMounted = false;
let composerCleanup = null;
let dialogsMounted = false;
let startingChat = false;

/**
 * Find an element by its stable HTML ID.
 */
function $(id) {
    return document.getElementById(id);
}

/**
 * Find a room by ID, tolerating numeric/string ID differences.
 */
function getRoom(roomId) {
    if (roomId == null) return null;

    for (const [id, room] of state.rooms) {
        if (String(id) === String(roomId)) {
            return room;
        }
    }

    return null;
}

/**
 * Find the public general room.
 */
function getGeneralRoom() {
    return [...state.rooms.values()].find(room =>
        room.kind === "public" ||
        String(room.name ?? "").toLowerCase() === "general"
    ) ?? null;
}

/**
 * Open #general, falling back to the first available room.
 */
function openGeneralRoom() {
    const room =
        getGeneralRoom() ??
        state.rooms.values().next().value ??
        null;

    if (room) {
        setActiveRoom(room.id);
        clearUnread(room.id);
    } else {
        setActiveRoom(null);
    }
}

/**
 * Render application-level visibility and connection status.
 *
 * Conversation and composer render themselves through their own
 * store subscriptions. The sidebar and login view are rendered here.
 */
function renderApp(appState) {
    const loading = $("loading-state");
    const authView = $("auth-view");
    const chatView = $("chat-view");
    const adminView = $("admin-view");
    const banner = $("connection-banner");
    const bannerText = $("connection-banner-text");

    if (booting) {
        if (loading) loading.hidden = false;
        if (authView) authView.hidden = true;
        if (chatView) chatView.hidden = true;
        if (adminView) adminView.hidden = true;
        if (banner) banner.hidden = true;
        return;
    }

    if (loading) loading.hidden = true;

    if (authView) {
        authView.hidden = appState.view !== "login";
    }

    if (chatView) {
        chatView.hidden = appState.view !== "chat";
    }

    if (adminView) {
        adminView.hidden = appState.view !== "admin";
    }

    if (loginMounted) {
        LoginView.render(appState);
    }

    if (sidebarMounted) {
        SidebarView.render(appState);
    }

    if (banner && bannerText) {
        banner.hidden =
            appState.view !== "chat" ||
            appState.connection === "connected";

        bannerText.textContent =
            appState.connection === "offline"
                ? "Offline"
                : "Reconnecting…";
    }
}

/**
 * Unmount controls whose modules support cleanup.
 */
function unmountChatControls() {
    if (typeof composerCleanup === "function") {
        composerCleanup();
        composerCleanup = null;
    }

    if (dialogsMounted) {
        DialogsView.unmount();
        dialogsMounted = false;
    }
}

/**
 * Clear session-specific client state.
 * Store mutations always go through exported store actions.
 */
function resetSessionState() {
    for (const roomId of [...state.rooms.keys()]) {
        removeRoom(roomId);
    }

    setRooms([]);
    setActiveRoom(null);
    setUnread({});
    setOnline([]);
    setMe(null);
    setConnection("offline");
    setView("login");
}

/**
 * Handle a completed logout from the sidebar.
 */
function handleLogoutComplete() {
    unmountChatControls();
    resetSessionState();

    LoginView.mount({
        onLoggedIn: startChat
    });
}

/**
 * Handle server-side session revocation.
 */
function handleSessionTerminated(payload) {
    stopReconnecting();
    unmountChatControls();

    const notice = payload?.reason === "banned"
        ? "Your account was banned by an administrator"
        : "You were logged out";

    resetSessionState();

    LoginView.mount({
        onLoggedIn: startChat,
        notice
    });
}

/**
 * Navigate to the admin shell.
 * The full admin implementation belongs to F10.
 */
function openAdmin() {
    if (state.me?.role === "admin") {
        setView("admin");
    }
}

/**
 * Handle a live incoming message.
 */
function handleMessageNew(payload) {
    const message = payload?.message;

    if (
        !message ||
        message.room_id == null ||
        message.id == null
    ) {
        return;
    }

    addMessages(message.room_id, [message]);
    bumpUnread(message.room_id, message);

    // Mark the incoming message as delivered to this connected client.
    void emitAck("receipt:update", {
        room_id: message.room_id,
        delivered_up_to: message.id
    }).catch(() => {
        // A disconnect during receipt delivery is normal.
        // Reconnect sync will recover missed messages.
    });
}

/**
 * Handle an edited or deleted message.
 */
function handleMessageUpdated(payload) {
    const message = payload?.message;

    if (
        !message ||
        message.room_id == null ||
        message.id == null
    ) {
        return;
    }

    addMessages(message.room_id, [message]);
}

/**
 * Handle a live receipt watermark update.
 */
function handleReceiptUpdated(payload) {
    if (
        payload?.room_id == null ||
        payload?.user_id == null
    ) {
        return;
    }

    updateReceipt(payload);
}

/**
 * Handle another member's typing state.
 */
function handleTyping(payload) {
    if (
        payload?.room_id == null ||
        !payload.user ||
        payload.user.id == null
    ) {
        return;
    }

    setTyping(
        payload.room_id,
        payload.user,
        payload.is_typing === true
    );
}

/**
 * Handle the initial online-user snapshot for this socket.
 */
function handlePresenceSnapshot(payload) {
    if (Array.isArray(payload?.users)) {
        setOnline(payload.users);
    }
}

/**
 * Handle a member joining or leaving the presence channel.
 */
function handlePresence(payload) {
    const user = payload?.user;

    if (!user || user.id == null) {
        return;
    }

    const online = payload.online === true;

    setPresence(user, online);

    const general = getGeneralRoom();

    if (general) {
        const username = user.username || "A user";
        const action = online ? "joined" : "left";

        addNotice(
            general.id,
            `${username} ${action}`
        );
    }
}

/**
 * Handle a room becoming available to the current user.
 */
function handleRoomAdded(payload) {
    if (payload?.room?.id != null) {
        upsertRoom(payload.room);
    }
}

/**
 * Handle membership removal.
 */
function handleRoomRemoved(payload) {
    const roomId = payload?.room_id;

    if (roomId == null) return;

    const wasActive =
        String(state.activeRoomId) === String(roomId);

    removeRoom(roomId);

    if (wasActive) {
        openGeneralRoom();
    }
}

/**
 * Merge a room update without losing viewer-specific information.
 *
 * room:updated intentionally omits peer and invite_code.
 * Preserve these fields from the current user's existing room object.
 */
function handleRoomUpdated(payload) {
    const room = payload?.room;

    if (!room || room.id == null) {
        return;
    }

    const existing = getRoom(room.id);

    const merged = {
        ...(existing ?? {}),
        ...room
    };

    if (!room.peer && existing?.peer) {
        merged.peer = existing.peer;
    }

    if (!room.invite_code && existing?.invite_code) {
        merged.invite_code = existing.invite_code;
    }

    upsertRoom(merged);
}

/**
 * Merge reconnect synchronization data into the store.
 */
async function synchronizeAfterConnect() {
    try {
        const data = await emitAck("sync", {
            cursors: cursors()
        });

        if (!data || typeof data !== "object") {
            throw new Error("The server returned invalid sync data.");
        }

        if (Array.isArray(data.rooms)) {
            setRooms(data.rooms);
        }

        if (
            data.unread &&
            typeof data.unread === "object"
        ) {
            setUnread(data.unread);
        }

        if (Array.isArray(data.messages)) {
            const messagesByRoom = new Map();

            for (const message of data.messages) {
                if (
                    message?.room_id == null ||
                    message?.id == null
                ) {
                    continue;
                }

                const roomId = message.room_id;

                if (!messagesByRoom.has(roomId)) {
                    messagesByRoom.set(roomId, []);
                }

                messagesByRoom.get(roomId).push(message);
            }

            for (const [roomId, messages] of messagesByRoom) {
                addMessages(roomId, messages);
            }
        }

        // The user may have lost access to the active room while offline.
        if (
            state.activeRoomId != null &&
            !getRoom(state.activeRoomId)
        ) {
            openGeneralRoom();
        }
    } catch (error) {
        console.error("Reconnect synchronization failed:", error);
    }
}

/**
 * Connect the socket and register every server-to-client event
 * defined in control file section 6.6.
 */
function connectSocket() {
    connect({
        on: {
            "message:new": handleMessageNew,
            "message:updated": handleMessageUpdated,
            "receipt:updated": handleReceiptUpdated,
            typing: handleTyping,
            "presence:snapshot": handlePresenceSnapshot,
            presence: handlePresence,
            "room:added": handleRoomAdded,
            "room:removed": handleRoomRemoved,
            "room:updated": handleRoomUpdated,
            "session:terminated": handleSessionTerminated
        },

        onStatus(status) {
            if (
                status === "connected" ||
                status === "reconnecting" ||
                status === "offline"
            ) {
                setConnection(status);
            }
        },

        onConnected: synchronizeAfterConnect
    });
}

/**
 * Mount the existing frontend views.
 *
 * Sidebar and conversation modules protect themselves against
 * duplicate event listeners/subscriptions. Composer and dialogs
 * are explicitly mounted again after a later login.
 */
function mountChatViews() {
    SidebarView.mount({
        onAdmin: openAdmin,
        onLogout: handleLogoutComplete
    });

    sidebarMounted = true;

    ConversationView.mount({
        onRetryPending(clientId) {
            void ComposerView.retryPending(clientId);
        }
    });

    if (!composerCleanup) {
        composerCleanup = ComposerView.mount();
    }

    if (!dialogsMounted) {
        DialogsView.mount();
        dialogsMounted = true;
    }
}

/**
 * Load the user's rooms and start the authenticated chat session.
 */
async function startChat(user) {
    if (startingChat) return;

    startingChat = true;

    try {
        if (!user || user.id == null) {
            throw new Error("A valid authenticated user was not returned.");
        }

        setMe(user);

        const data = await api("GET", "/api/rooms");

        if (!Array.isArray(data?.rooms)) {
            throw new Error("The server returned an invalid room list.");
        }

        setRooms(data.rooms);

        const unread = {};

        for (const room of data.rooms) {
            if (room?.id != null) {
                unread[String(room.id)] = Number(room.unread) || 0;
            }
        }

        setUnread(unread);
        setView("chat");

        // Clear any previous login notice after successful authentication.
        LoginView.mount({
            onLoggedIn: startChat
        });

        mountChatViews();

        // Register handlers before selecting the initial conversation.
        connectSocket();

        // Open #general after the socket is configured.
        openGeneralRoom();
    } catch (error) {
        console.error("Unable to start the chat session:", error);

        stopReconnecting();
        unmountChatControls();
        resetSessionState();

        LoginView.mount({
            onLoggedIn: startChat,
            notice: error?.message || "Unable to load your conversations."
        });
    } finally {
        startingChat = false;
    }
}

/**
 * Restore the session on page load.
 */
async function boot() {
    try {
        const data = await api("GET", "/api/auth/me");
        const user = data?.user ?? null;

        if (user) {
            await startChat(user);
        } else {
            setMe(null);
            setView("login");
        }
    } catch (error) {
        console.error("Session lookup failed:", error);

        setMe(null);
        setView("login");

        LoginView.mount({
            onLoggedIn: startChat,
            notice: error?.message || "Unable to check your session."
        });
    } finally {
        booting = false;
        renderApp(state);
    }
}

/**
 * Initialize the application after the HTML document has loaded.
 */
function initialize() {
    LoginView.mount({
        onLoggedIn: startChat
    });

    loginMounted = true;

    subscribe(renderApp);

    $("admin-back-button")?.addEventListener("click", () => {
        if (state.me?.role === "admin") {
            setView("chat");
        }
    });

    renderApp(state);
    void boot();
}

initialize();
