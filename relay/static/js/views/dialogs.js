/**
 * F8: Room and message dialogs.
 * Handles room creation, public browsing, invite-code joining and search.
 */

import { api } from "../api.js";
import { state, upsertRoom, setActiveRoom } from "../store.js";
import { $, el, clear, formatTime } from "../dom.js";

const MIN_ROOM_NAME = 1;
const MAX_ROOM_NAME = 40;
const MIN_SEARCH_LENGTH = 2;
const MAX_SEARCH_LENGTH = 100;

let mounted = false;
let elements = null;
let handlers = null;
let onOpenRoom = null;

let browseRequestToken = 0;
let searchRequestToken = 0;

function sameId(left, right) {
    return left != null &&
        right != null &&
        String(left) === String(right);
}

function getElements() {
    const found = {
        createButton: $("create-room-button"),
        browseButton: $("browse-rooms-button"),
        searchButton: $("conversation-search-button"),

        createDialog: $("create-room-dialog"),
        createForm: $("create-room-form"),
        roomName: $("new-room-name"),
        roomVisibility: $("new-room-visibility"),

        browseDialog: $("browse-rooms-dialog"),
        publicResults: $("public-room-results"),
        joinForm: $("join-room-form"),
        inviteCode: $("invite-code-input"),

        searchDialog: $("search-dialog"),
        searchForm: $("message-search-form"),
        searchInput: $("message-search-input"),
        searchCurrentRoom: $("search-current-room"),
        searchResults: $("message-search-results")
    };

    for (const [name, element] of Object.entries(found)) {
        if (!element) {
            throw new Error(
                `Dialogs cannot start: missing element "${name}".`
            );
        }
    }

    for (const [name, dialog] of [
        ["create-room-dialog", found.createDialog],
        ["browse-rooms-dialog", found.browseDialog],
        ["search-dialog", found.searchDialog]
    ]) {
        if (typeof dialog.showModal !== "function") {
            throw new Error(
                `Your browser does not support the native ${name} dialog.`
            );
        }
    }

    return found;
}

function openDialog(dialog) {
    if (!dialog.open) {
        dialog.showModal();
    }
}

function closeDialog(dialog) {
    if (dialog.open) {
        dialog.close();
    }
}

function statusNode(container, key = "dialog-status") {
    let node = container.querySelector(`[data-${key}]`);

    if (!node) {
        node = el("p", {
            class: "inline-error",
            role: "alert",
            [`data-${key}`]: "true"
        });

        container.appendChild(node);
    }

    return node;
}

function showStatus(container, message, key = "dialog-status") {
    const node = statusNode(container, key);
    node.textContent = message || "";
    node.hidden = !message;
}

function clearStatus(container, key = "dialog-status") {
    const node = container.querySelector(`[data-${key}]`);

    if (node) {
        node.textContent = "";
        node.hidden = true;
    }
}

function errorMessage(error, fallback) {
    return (
        typeof error?.message === "string" &&
        error.message.trim()
    )
        ? error.message
        : fallback;
}

function findRoom(roomId) {
    if (roomId == null) return null;

    const direct = state.rooms.get(roomId);

    if (direct) return direct;

    for (const [id, room] of state.rooms) {
        if (sameId(id, roomId)) {
            return room;
        }
    }

    return null;
}

/**
 * Activate a room after a successful create, join or search selection.
 * F9 can optionally receive the opening callback to coordinate navigation.
 */
function openRoom(room, message = null) {
    if (!room || room.id == null) {
        throw new Error("The server returned an invalid room.");
    }

    upsertRoom(room);
    setActiveRoom(room.id);

    if (typeof onOpenRoom === "function") {
        onOpenRoom(room.id, message);
    }
}

function roomDisplayName(room) {
    if (!room) return "Unknown room";

    if (room.kind === "group" || room.kind === "public") {
        return `#${room.name || "unnamed"}`;
    }

    return room.name || "Direct message";
}

function setFormBusy(form, busy) {
    const submit = form.querySelector('button[type="submit"]');

    if (submit) {
        submit.disabled = busy;
    }
}

function createRoomStatus(message) {
    showStatus(elements.createForm, message);
}

function joinRoomStatus(message) {
    showStatus(elements.joinForm, message);
}

function searchStatus(message) {
    const node = statusNode(elements.searchResults);

    clear(elements.searchResults);

    node.textContent = message || "";
    node.hidden = !message;

    if (message) {
        elements.searchResults.appendChild(node);
    }
}

function renderPublicRooms(rooms) {
    clear(elements.publicResults);
    clearStatus(elements.publicResults);

    if (!rooms.length) {
        elements.publicResults.appendChild(
            el("p", { class: "empty-state" }, "No public rooms are available.")
        );
        return;
    }

    for (const room of rooms) {
        if (!room || room.id == null) continue;

        const name = el(
            "strong",
            { class: "dialog-room-name" },
            roomDisplayName(room)
        );

        const count = Number.isFinite(Number(room.member_count))
            ? Number(room.member_count)
            : 0;

        const memberText = `${count} ${count === 1 ? "member" : "members"}`;

        const description = el(
            "span",
            { class: "muted-small dialog-room-meta" },
            memberText
        );

        const copy = el(
            "div",
            { class: "dialog-room-copy" },
            name,
            description
        );

        const action = el(
            "button",
            {
                type: "button",
                class: "button button-quiet"
            },
            room.joined === true ? "Open" : "Join"
        );

        const row = el(
            "div",
            { class: "dialog-room-row" },
            copy,
            action
        );

        action.addEventListener("click", async () => {
            if (action.disabled) return;

            action.disabled = true;

            try {
                if (room.joined === true) {
                    openRoom(room);
                    closeDialog(elements.browseDialog);
                    return;
                }

                action.textContent = "Joining…";

                const data = await api(
                    "POST",
                    `/api/rooms/${encodeURIComponent(room.id)}/join`
                );

                if (!data?.room) {
                    throw new Error("The server did not return the joined room.");
                }

                openRoom(data.room);
                closeDialog(elements.browseDialog);
            } catch (error) {
                action.disabled = false;
                action.textContent = "Join";

                joinRoomStatus(
                    errorMessage(error, "Could not join this room.")
                );
            }
        });

        elements.publicResults.appendChild(row);
    }
}

async function loadPublicRooms() {
    const token = ++browseRequestToken;

    clear(elements.publicResults);

    elements.publicResults.appendChild(
        el("p", { class: "empty-state" }, "Loading public rooms…")
    );

    clearStatus(elements.joinForm);

    try {
        const data = await api("GET", "/api/rooms/public");

        if (!mounted || token !== browseRequestToken) return;

        if (!Array.isArray(data?.rooms)) {
            throw new Error("The server returned an invalid room list.");
        }

        renderPublicRooms(data.rooms);
    } catch (error) {
        if (!mounted || token !== browseRequestToken) return;

        clear(elements.publicResults);

        elements.publicResults.appendChild(
            el(
                "p",
                { class: "empty-state" },
                errorMessage(error, "Could not load public rooms.")
            )
        );
    }
}

function handleCreateRoomOpen() {
    clearStatus(elements.createForm);
    openDialog(elements.createDialog);
    elements.roomName.focus();
}

async function handleCreateRoomSubmit(event) {
    event.preventDefault();

    const name = elements.roomName.value.trim();
    const visibility = elements.roomVisibility.value;

    if (
        name.length < MIN_ROOM_NAME ||
        name.length > MAX_ROOM_NAME
    ) {
        createRoomStatus("Room name must be between 1 and 40 characters.");
        elements.roomName.focus();
        return;
    }

    if (!["public", "private"].includes(visibility)) {
        createRoomStatus("Choose public or private visibility.");
        return;
    }

    clearStatus(elements.createForm);
    setFormBusy(elements.createForm, true);

    try {
        const data = await api("POST", "/api/rooms", {
            name,
            visibility
        });

        if (!data?.room) {
            throw new Error("The server did not return the created room.");
        }

        // The returned owner room may contain an invite_code for private rooms.
        openRoom(data.room);

        elements.createForm.reset();
        closeDialog(elements.createDialog);
    } catch (error) {
        createRoomStatus(
            errorMessage(error, "Could not create this room.")
        );
    } finally {
        setFormBusy(elements.createForm, false);
    }
}

function handleBrowseOpen() {
    openDialog(elements.browseDialog);
    void loadPublicRooms();
}

async function handleJoinByCode(event) {
    event.preventDefault();

    const inviteCode = elements.inviteCode.value.trim();

    if (!inviteCode) {
        joinRoomStatus("Enter an invite code.");
        elements.inviteCode.focus();
        return;
    }

    clearStatus(elements.joinForm);
    setFormBusy(elements.joinForm, true);

    try {
        const data = await api("POST", "/api/rooms/join", {
            invite_code: inviteCode
        });

        if (!data?.room) {
            throw new Error("The server did not return the joined room.");
        }

        openRoom(data.room);

        elements.joinForm.reset();
        closeDialog(elements.browseDialog);
    } catch (error) {
        joinRoomStatus(
            errorMessage(error, "Could not join with this invite code.")
        );
    } finally {
        setFormBusy(elements.joinForm, false);
    }
}

function handleSearchOpen() {
    clear(elements.searchResults);
    clearStatus(elements.searchResults);

    elements.searchInput.value = "";
    elements.searchCurrentRoom.checked = false;

    openDialog(elements.searchDialog);
    elements.searchInput.focus();
}

function getSearchRoomLabel(message) {
    const room = findRoom(message.room_id);

    return room
        ? roomDisplayName(room)
        : `Room ${message.room_id ?? "unknown"}`;
}

function messageSnippet(message) {
    const body = typeof message.body === "string"
        ? message.body.trim()
        : "";

    const attachmentName = message.attachment?.name;

    const source = body ||
        (attachmentName ? `Attachment: ${attachmentName}` : "Message");

    const maximum = 180;

    return source.length > maximum
        ? `${source.slice(0, maximum)}…`
        : source;
}

function renderSearchResults(messages) {
    clear(elements.searchResults);

    if (!messages.length) {
        elements.searchResults.appendChild(
            el("p", { class: "empty-state" }, "No matching messages found.")
        );
        return;
    }

    for (const message of messages) {
        if (!message || message.room_id == null) continue;

        const roomName = getSearchRoomLabel(message);

        const senderName = message.sender?.username ||
            "Unknown sender";

        const time = formatTime(message.created_at);

        const heading = el(
            "div",
            { class: "dialog-search-heading" },
            el("strong", {}, roomName),
            el("span", { class: "muted-small" }, senderName),
            el("span", { class: "muted-small" }, time)
        );

        const snippet = el(
            "span",
            { class: "dialog-search-snippet" },
            messageSnippet(message)
        );

        const result = el(
            "button",
            {
                type: "button",
                class: "button button-quiet dialog-search-result"
            },
            heading,
            snippet
        );

        result.addEventListener("click", () => {
            closeDialog(elements.searchDialog);

            setActiveRoom(message.room_id);

            if (typeof onOpenRoom === "function") {
                onOpenRoom(message.room_id, message);
            }
        });

        elements.searchResults.appendChild(result);
    }
}

async function handleSearchSubmit(event) {
    event.preventDefault();

    const query = elements.searchInput.value.trim();

    if (
        query.length < MIN_SEARCH_LENGTH ||
        query.length > MAX_SEARCH_LENGTH
    ) {
        searchStatus("Search must contain between 2 and 100 characters.");
        elements.searchInput.focus();
        return;
    }

    const params = new URLSearchParams();
    params.set("q", query);

    if (elements.searchCurrentRoom.checked) {
        const roomId = state.activeRoomId;

        if (roomId == null) {
            searchStatus("Open a conversation before searching within it.");
            return;
        }

        params.set("room_id", String(roomId));
    }

    const token = ++searchRequestToken;

    clear(elements.searchResults);

    elements.searchResults.appendChild(
        el("p", { class: "empty-state" }, "Searching messages…")
    );

    setFormBusy(elements.searchForm, true);

    try {
        const data = await api(
            "GET",
            `/api/search?${params.toString()}`
        );

        if (!mounted || token !== searchRequestToken) return;

        if (!Array.isArray(data?.messages)) {
            throw new Error("The server returned invalid search results.");
        }

        renderSearchResults(data.messages);
    } catch (error) {
        if (!mounted || token !== searchRequestToken) return;

        clear(elements.searchResults);

        elements.searchResults.appendChild(
            el(
                "p",
                { class: "empty-state" },
                errorMessage(error, "Could not search messages.")
            )
        );
    } finally {
        if (token === searchRequestToken) {
            setFormBusy(elements.searchForm, false);
        }
    }
}

/**
 * Open the create-room native dialog.
 */
export function openCreateRoom() {
    if (!mounted) {
        throw new Error("Mount the dialogs view before opening dialogs.");
    }

    handleCreateRoomOpen();
}

/**
 * Open the public-room browser and load its rooms.
 */
export function openBrowseRooms() {
    if (!mounted) {
        throw new Error("Mount the dialogs view before opening dialogs.");
    }

    handleBrowseOpen();
}

/**
 * Open the message-search dialog.
 */
export function openSearch() {
    if (!mounted) {
        throw new Error("Mount the dialogs view before opening dialogs.");
    }

    handleSearchOpen();
}

/**
 * Mount all dialog event handlers.
 * Optional onOpenRoom callback receives (roomId, message).
 */
export function mount(options = {}) {
    if (mounted) {
        return unmount;
    }

    if (
        options === null ||
        typeof options !== "object" ||
        Array.isArray(options)
    ) {
        throw new TypeError("Dialog mount options must be an object.");
    }

    if (
        options.onOpenRoom !== undefined &&
        typeof options.onOpenRoom !== "function"
    ) {
        throw new TypeError("onOpenRoom must be a function.");
    }

    elements = getElements();
    onOpenRoom = options.onOpenRoom || null;
    mounted = true;

    handlers = {
        createOpen: handleCreateRoomOpen,
        browseOpen: handleBrowseOpen,
        searchOpen: handleSearchOpen,
        createSubmit: handleCreateRoomSubmit,
        joinSubmit: handleJoinByCode,
        searchSubmit: handleSearchSubmit
    };

    elements.createButton.addEventListener(
        "click",
        handlers.createOpen
    );

    elements.browseButton.addEventListener(
        "click",
        handlers.browseOpen
    );

    elements.searchButton.addEventListener(
        "click",
        handlers.searchOpen
    );

    elements.createForm.addEventListener(
        "submit",
        handlers.createSubmit
    );

    elements.joinForm.addEventListener(
        "submit",
        handlers.joinSubmit
    );

    elements.searchForm.addEventListener(
        "submit",
        handlers.searchSubmit
    );

    return unmount;
}

/**
 * Remove event listeners and invalidate outstanding requests.
 */
export function unmount() {
    if (!mounted || !elements || !handlers) return;

    elements.createButton.removeEventListener(
        "click",
        handlers.createOpen
    );

    elements.browseButton.removeEventListener(
        "click",
        handlers.browseOpen
    );

    elements.searchButton.removeEventListener(
        "click",
        handlers.searchOpen
    );

    elements.createForm.removeEventListener(
        "submit",
        handlers.createSubmit
    );

    elements.joinForm.removeEventListener(
        "submit",
        handlers.joinSubmit
    );

    elements.searchForm.removeEventListener(
        "submit",
        handlers.searchSubmit
    );

    browseRequestToken += 1;
    searchRequestToken += 1;

    closeDialog(elements.createDialog);
    closeDialog(elements.browseDialog);
    closeDialog(elements.searchDialog);

    mounted = false;
    elements = null;
    handlers = null;
    onOpenRoom = null;
}