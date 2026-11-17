/**
 * F5: Sidebar, conversations, online users and people search.
 * All user-controlled values are rendered as DOM text nodes.
 */

import { api } from "../api.js";
import {
    state,
    upsertRoom,
    setActiveRoom,
    clearUnread,
    setMe,
    setView,
    setConnection
} from "../store.js";
import { stopReconnecting } from "../socket.js";
import { $, el, clear } from "../dom.js";

let mounted = false;
let callbacks = {};

let searchTimer = null;
let searchToken = 0;
let searchUsers = [];
let searchStatus = "";
let searchQuery = "";
const openingDms = new Set();

let loggingOut = false;

function elements() {
    return {
        sidebar: $("sidebar"),
        chatLayout: document.querySelector(".chat-layout"),
        meAvatar: $("me-avatar"),
        meUsername: $("me-username"),
        meRole: $("me-role"),
        logout: $("logout-button"),
        admin: $("admin-button"),
        peopleForm: $("people-search-form"),
        peopleInput: $("people-search"),
        peopleResults: $("people-search-results"),
        createRoom: $("create-room-button"),
        roomList: $("room-list"),
        browseRooms: $("browse-rooms-button"),
        onlineCount: $("online-count"),
        onlineList: $("online-list"),
        sidebarToggle: $("sidebar-toggle")
    };
}

function text(value) {
    return value == null ? "" : String(value);
}

function initials(username) {
    const value = text(username).trim();
    return value ? value.slice(0, 2).toUpperCase() : "??";
}

function displayRole(user) {
    if (user?.role === "admin") return "Admin";
    return "Member";
}

function displayError(error) {
    return error?.message || "Something went wrong. Please try again.";
}

function showSidebarFeedback(message) {
    const sidebar = elements().sidebar;
    if (!sidebar) return;

    let feedback = $("sidebar-feedback");

    if (!feedback) {
        feedback = el("p", {
            id: "sidebar-feedback",
            class: "sidebar-empty",
            role: "alert"
        });

        const bottom = sidebar.querySelector(".sidebar-bottom");

        if (bottom) {
            sidebar.insertBefore(feedback, bottom);
        } else {
            sidebar.appendChild(feedback);
        }
    }

    feedback.textContent = text(message);
    feedback.hidden = false;
}

function clearSidebarFeedback() {
    const feedback = $("sidebar-feedback");

    if (feedback) {
        feedback.textContent = "";
        feedback.hidden = true;
    }
}

function closeMobileSidebar() {
    const { chatLayout, sidebarToggle } = elements();

    chatLayout?.classList.remove("sidebar-open");

    if (sidebarToggle) {
        sidebarToggle.setAttribute("aria-expanded", "false");
    }
}

function openRoom(room) {
    if (!room || room.id == null) return;

    setActiveRoom(room.id);
    clearUnread(room.id);
    closeMobileSidebar();

    if (typeof callbacks.onRoomSelected === "function") {
        callbacks.onRoomSelected(room);
    }
}

function sortByName(left, right) {
    return text(left).localeCompare(text(right), undefined, {
        sensitivity: "base"
    });
}

function roomLabel(room) {
    if (room.kind === "direct") {
        return room.peer?.username || room.name || "Direct message";
    }

    return room.name || "Unnamed room";
}

function roomSymbol(room) {
    return room.kind === "direct" ? "@" : "#";
}

function roomGroups(rooms) {
    const general = [];
    const groups = [];
    const direct = [];
    const other = [];

    for (const room of rooms) {
        const isGeneral =
            room.kind === "public" ||
            text(room.name).toLowerCase() === "general";

        if (isGeneral) {
            general.push(room);
        } else if (room.kind === "direct") {
            direct.push(room);
        } else if (room.kind === "group") {
            groups.push(room);
        } else {
            other.push(room);
        }
    }

    groups.sort((a, b) => sortByName(a.name, b.name));
    direct.sort((a, b) => sortByName(roomLabel(a), roomLabel(b)));
    other.sort((a, b) => sortByName(roomLabel(a), roomLabel(b)));

    return [
        ...general,
        ...groups,
        ...other,
        ...direct
    ];
}

function createRoomButton(room, appState) {
    const active =
        String(appState.activeRoomId) === String(room.id);

    const unread = Math.max(
        0,
        Number(
            appState.unread?.get(room.id) ??
            room.unread ??
            0
        ) || 0
    );

    const button = el("button", {
        type: "button",
        class: active
            ? "nav-utility room-entry"
            : "nav-utility nav-utility-muted room-entry",
        "aria-current": active ? "page" : null,
        title: roomLabel(room)
    });

    button.appendChild(
        el("span", {
            class: "room-symbol",
            "aria-hidden": "true"
        }, roomSymbol(room))
    );

    button.appendChild(
        el("span", { class: "room-entry-name" }, roomLabel(room))
    );

    const badge = el("span", {
        class: "count-pill unread-badge",
        hidden: unread === 0,
        "aria-label": unread ? `${unread} unread messages` : null
    }, unread > 99 ? "99+" : String(unread));

    button.appendChild(badge);

    button.addEventListener("click", () => openRoom(room));

    return button;
}

function renderRooms(appState) {
    const { roomList } = elements();
    if (!roomList) return;

    clear(roomList);

    const rooms = appState.rooms instanceof Map
        ? [...appState.rooms.values()]
        : [];

    if (!rooms.length) {
        roomList.appendChild(
            el("div", { class: "sidebar-empty" },
                "Your conversations will appear here.")
        );
        return;
    }

    for (const room of roomGroups(rooms)) {
        roomList.appendChild(createRoomButton(room, appState));
    }
}

function renderProfile(user) {
    const { meAvatar, meUsername, meRole, admin } = elements();

    if (meAvatar) {
        meAvatar.textContent = initials(user?.username || "ME");
    }

    if (meUsername) {
        meUsername.textContent = user?.username || "Your name";
    }

    if (meRole) {
        meRole.textContent = displayRole(user);
    }

    if (admin) {
        admin.hidden = user?.role !== "admin";
    }
}

function renderOnlineUsers(appState) {
    const { onlineCount, onlineList } = elements();
    if (!onlineList) return;

    const users = appState.online instanceof Map
        ? [...appState.online.values()]
        : [];

    users.sort((a, b) => sortByName(a.username, b.username));

    if (onlineCount) {
        onlineCount.textContent = String(users.length);
    }

    clear(onlineList);

    if (!users.length) {
        onlineList.appendChild(
            el("div", { class: "sidebar-empty" },
                "No one else is online yet.")
        );
        return;
    }

    for (const user of users) {
        const isMe =
            appState.me?.id != null &&
            String(user.id) === String(appState.me.id);

        const row = el("div", {
            class: "profile-card online-user"
        });

        row.appendChild(
            el("span", {
                class: "avatar",
                "aria-hidden": "true"
            }, initials(user.username))
        );

        const copy = el("div", { class: "profile-copy" });

        copy.appendChild(
            el("strong", {}, `${text(user.username)}${isMe ? " (you)" : ""}`)
        );

        copy.appendChild(
            el("span", { class: "muted-small" }, "Online")
        );

        row.appendChild(copy);
        onlineList.appendChild(row);
    }
}

function renderPeopleSearch() {
    const { peopleResults } = elements();
    if (!peopleResults) return;

    clear(peopleResults);

    if (!searchQuery) return;

    if (searchStatus) {
        peopleResults.appendChild(
            el("div", { class: "sidebar-empty" }, searchStatus)
        );
        return;
    }

    if (!searchUsers.length) {
        peopleResults.appendChild(
            el("div", { class: "sidebar-empty" }, "No people found.")
        );
        return;
    }

    for (const user of searchUsers) {
        const busy = openingDms.has(String(user.id));

        const button = el("button", {
            type: "button",
            class: "nav-utility nav-utility-muted person-result",
            disabled: busy
        });

        const dot = el("span", {
            class: "secure-indicator",
            hidden: !user.online,
            "aria-hidden": "true"
        });

        button.appendChild(dot);

        button.appendChild(
            el("span", {}, user.username || "Unknown user")
        );

        button.appendChild(
            el("span", { class: "muted-small" },
                busy ? "Opening…" : user.online ? "Online" : "Offline")
        );

        button.addEventListener("click", () => openDirectMessage(user));

        peopleResults.appendChild(button);
    }
}

async function searchPeople() {
    const { peopleInput } = elements();
    if (!peopleInput) return;

    const query = peopleInput.value.trim();

    clearTimeout(searchTimer);
    searchQuery = query;
    searchToken += 1;

    const token = searchToken;

    if (!query) {
        searchUsers = [];
        searchStatus = "";
        renderPeopleSearch();
        return;
    }

    searchUsers = [];
    searchStatus = "Searching…";
    renderPeopleSearch();

    try {
        const data = await api(
            "GET",
            `/api/users?q=${encodeURIComponent(query)}`
        );

        if (token !== searchToken) return;

        if (!Array.isArray(data?.users)) {
            throw new Error("The server returned an invalid people list.");
        }

        searchUsers = data.users;
        searchStatus = searchUsers.length ? "" : "No people found.";
    } catch (error) {
        if (token !== searchToken) return;

        searchUsers = [];
        searchStatus = displayError(error);
    }

    renderPeopleSearch();
}

function handlePeopleInput() {
    const { peopleInput } = elements();
    if (!peopleInput) return;

    clearTimeout(searchTimer);

    searchQuery = peopleInput.value.trim();
    searchToken += 1;
    searchUsers = [];

    if (!searchQuery) {
        searchStatus = "";
        renderPeopleSearch();
        return;
    }

    searchStatus = "Searching…";
    renderPeopleSearch();

    searchTimer = setTimeout(searchPeople, 250);
}

async function openDirectMessage(user) {
    if (!user || user.id == null) return;

    const userId = String(user.id);
    if (openingDms.has(userId)) return;

    openingDms.add(userId);
    clearSidebarFeedback();
    renderPeopleSearch();

    try {
        const data = await api("POST", "/api/dms", {
            user_id: user.id
        });

        if (!data?.room || data.room.id == null) {
            throw new Error("The server did not return a direct message room.");
        }

        upsertRoom(data.room);
        openRoom(data.room);

        const { peopleInput } = elements();

        if (peopleInput) {
            peopleInput.value = "";
        }

        searchQuery = "";
        searchUsers = [];
        searchStatus = "";
        searchToken += 1;
        renderPeopleSearch();
    } catch (error) {
        searchStatus = displayError(error);
        renderPeopleSearch();
    } finally {
        openingDms.delete(userId);
        renderPeopleSearch();
    }
}

async function handleLogout() {
    if (loggingOut) return;

    loggingOut = true;

    const { logout } = elements();

    if (logout) {
        logout.disabled = true;
    }

    clearSidebarFeedback();

    try {
        await api("POST", "/api/auth/logout");

        // The session has been revoked. Do not reconnect with its cookie.
        stopReconnecting();

        setMe(null);
        setConnection("offline");
        setView("login");

        closeMobileSidebar();

        if (typeof callbacks.onLogout === "function") {
            callbacks.onLogout();
        }
    } catch (error) {
        showSidebarFeedback(`Could not log out: ${displayError(error)}`);
    } finally {
        loggingOut = false;

        if (logout) {
            logout.disabled = false;
        }
    }
}

function handleMobileToggle() {
    const { chatLayout, sidebarToggle } = elements();
    if (!chatLayout || !sidebarToggle) return;

    const isOpen = chatLayout.classList.toggle("sidebar-open");

    sidebarToggle.setAttribute("aria-expanded", String(isOpen));
}

function bindEvents() {
    const elms = elements();

    elms.peopleInput?.addEventListener("input", handlePeopleInput);

    elms.peopleForm?.addEventListener("submit", event => {
        event.preventDefault();
        searchPeople();
    });

    elms.logout?.addEventListener("click", handleLogout);

    elms.admin?.addEventListener("click", () => {
        if (state.me?.role === "admin" &&
            typeof callbacks.onAdmin === "function") {
            callbacks.onAdmin();
        }
    });

    elms.createRoom?.addEventListener("click", () => {
        callbacks.onCreateRoom?.();
    });

    elms.browseRooms?.addEventListener("click", () => {
        callbacks.onBrowseRooms?.();
    });

    elms.sidebarToggle?.addEventListener("click", handleMobileToggle);
}

/**
 * Mount the sidebar and register callbacks.
 *
 * Options:
 * {
 *   onRoomSelected(room),
 *   onCreateRoom(),
 *   onBrowseRooms(),
 *   onAdmin(),
 *   onLogout()
 * }
 */
export function mount(options = {}) {
    if (!options || typeof options !== "object") {
        throw new TypeError("Sidebar mount options must be an object.");
    }

    callbacks = {
        onRoomSelected: options.onRoomSelected,
        onCreateRoom: options.onCreateRoom,
        onBrowseRooms: options.onBrowseRooms,
        onAdmin: options.onAdmin,
        onLogout: options.onLogout
    };

    if (!mounted) {
        bindEvents();
        mounted = true;
    }

    render(state);
}

/**
 * Render the sidebar from the shared application state.
 */
export function render(appState) {
    if (!appState) return;

    renderProfile(appState.me);
    renderRooms(appState);
    renderOnlineUsers(appState);
    renderPeopleSearch();
}
