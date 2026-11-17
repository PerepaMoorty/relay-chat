/**
 * F7: Message composer.
 * Handles validation, optimistic sending, typing events and attachments.
 */

import { upload } from "../api.js";
import { emitAck } from "../socket.js";
import {
    state,
    subscribe,
    addPending,
    failPending,
    addMessages
} from "../store.js";
import { $, formatSize, formatTime } from "../dom.js";

const MAX_MESSAGE_LENGTH = 4000;
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const MAX_TEXTAREA_ROWS = 6;
const TYPING_INTERVAL = 2000;
const TYPING_IDLE_DELAY = 3000;

const INVALID_CONTROL_CHARACTERS =
    /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/u;

let mounted = false;
let elements = null;
let unsubscribe = null;
let observedRoomId = null;

let selectedAttachment = null;
let uploadInProgress = false;
let uploadToken = 0;

let typingActive = false;
let typingRoomId = null;
let lastTypingSentAt = 0;
let idleTimer = null;

const pendingPayloads = new Map();
const inFlight = new Set();

let handlers = null;

function sameRoom(left, right) {
    if (left == null || right == null) {
        return left == null && right == null;
    }

    return String(left) === String(right);
}

function showError(message) {
    if (!elements?.error) return;

    elements.error.textContent = message || "";
    elements.error.hidden = !message;
}

function clearError() {
    showError("");
}

function updateSendAvailability() {
    if (!elements) return;

    elements.sendButton.disabled =
        state.activeRoomId == null || uploadInProgress;

    elements.attachmentInput.disabled = uploadInProgress;

    elements.attachmentRemove.disabled =
        uploadInProgress || !selectedAttachment;
}

function resizeTextarea() {
    if (!elements?.textarea) return;

    const textarea = elements.textarea;

    // Reset to one row before measuring so the textarea can shrink too.
    textarea.rows = 1;

    const styles = window.getComputedStyle(textarea);
    const lineHeight = Number.parseFloat(styles.lineHeight) || 20;
    const paddingTop = Number.parseFloat(styles.paddingTop) || 0;
    const paddingBottom = Number.parseFloat(styles.paddingBottom) || 0;

    const contentHeight = Math.max(
        lineHeight,
        textarea.scrollHeight - paddingTop - paddingBottom
    );

    const rows = Math.ceil(contentHeight / lineHeight);

    textarea.rows = Math.min(
        MAX_TEXTAREA_ROWS,
        Math.max(1, rows)
    );
}

function emitTyping(event, roomId) {
    if (roomId == null) return;

    emitAck(event, { room_id: roomId }).catch(() => {
        // Typing is best-effort and must not interrupt message composition.
    });
}

function stopTyping(roomId = typingRoomId) {
    if (idleTimer !== null) {
        clearTimeout(idleTimer);
        idleTimer = null;
    }

    if (typingActive && roomId != null) {
        emitTyping("typing:stop", roomId);
    }

    typingActive = false;
    typingRoomId = null;
    lastTypingSentAt = 0;
}

function handleTypingInput() {
    if (!elements) return;

    const roomId = state.activeRoomId;
    const hasText = elements.textarea.value.trim().length > 0;

    if (roomId == null || !hasText) {
        stopTyping();
        return;
    }

    const now = Date.now();

    if (
        !typingActive ||
        !sameRoom(typingRoomId, roomId) ||
        now - lastTypingSentAt >= TYPING_INTERVAL
    ) {
        if (typingActive && !sameRoom(typingRoomId, roomId)) {
            stopTyping();
        }

        typingActive = true;
        typingRoomId = roomId;
        lastTypingSentAt = now;

        emitTyping("typing:start", roomId);
    }

    if (idleTimer !== null) {
        clearTimeout(idleTimer);
    }

    idleTimer = setTimeout(() => {
        stopTyping(roomId);
    }, TYPING_IDLE_DELAY);
}

function clearSelectedAttachment() {
    selectedAttachment = null;

    if (elements) {
        elements.attachmentInput.value = "";
        elements.attachmentName.textContent = "";
        elements.attachmentSize.textContent = "";
        elements.attachmentChip.hidden = true;
    }

    updateSendAvailability();
}

function displayAttachment(attachment) {
    selectedAttachment = attachment;

    elements.attachmentName.textContent =
        attachment.name || "Attached file";

    elements.attachmentSize.textContent =
        formatSize(attachment.size);

    elements.attachmentChip.hidden = false;

    updateSendAvailability();
}

function getErrorMessage(error) {
    const message =
        typeof error?.message === "string" && error.message.trim()
            ? error.message
            : "Could not send your message. Please try again.";

    if (error?.code === "MUTED" && error.details?.until) {
        const until = formatTime(error.details.until);

        if (until) {
            return `${message} Muted until ${until}.`;
        }
    }

    return message;
}

function validateMessage(body, attachment) {
    if (!body && !attachment) {
        return "Write a message or attach a file before sending.";
    }

    if (Array.from(body).length > MAX_MESSAGE_LENGTH) {
        return "Messages cannot exceed 4000 characters.";
    }

    if (INVALID_CONTROL_CHARACTERS.test(body)) {
        return "Your message contains unsupported control characters.";
    }

    if (attachment && attachment.id == null) {
        return "The selected attachment is invalid. Please attach it again.";
    }

    return "";
}

async function deliverPending(clientId, payload) {
    if (inFlight.has(clientId)) {
        return false;
    }

    inFlight.add(clientId);

    try {
        const result = await emitAck("message:send", payload);

        if (!result?.message || result.message.id == null) {
            throw new Error(
                "The server did not return the sent message."
            );
        }

        // The acknowledgement confirms the optimistic message.
        // addMessages also removes its matching pending client_id.
        addMessages(payload.room_id, [result.message]);

        pendingPayloads.delete(clientId);

        return true;
    } catch (error) {
        failPending(clientId);

        if (sameRoom(state.activeRoomId, payload.room_id)) {
            showError(getErrorMessage(error));
        }

        return false;
    } finally {
        inFlight.delete(clientId);
    }
}

async function sendMessage() {
    if (!elements) return;

    const roomId = state.activeRoomId;

    if (roomId == null) {
        showError("Select a conversation before sending a message.");
        return;
    }

    if (uploadInProgress) {
        showError("Please wait for the file upload to finish.");
        return;
    }

    const body = elements.textarea.value.trim();
    const attachment = selectedAttachment;
    const validationError = validateMessage(body, attachment);

    if (validationError) {
        showError(validationError);
        return;
    }

    let clientId;

    try {
        if (typeof globalThis.crypto?.randomUUID !== "function") {
            throw new Error("Secure message IDs are not available.");
        }

        clientId = globalThis.crypto.randomUUID();
    } catch (error) {
        showError(error.message);
        return;
    }

    const payload = {
        room_id: roomId,
        body,
        client_id: clientId
    };

    if (attachment) {
        payload.attachment_id = attachment.id;
    }

    try {
        // Display the pending message immediately.
        addPending(clientId, roomId, body);
        pendingPayloads.set(clientId, payload);
    } catch (error) {
        showError(error.message || "Could not prepare your message.");
        return;
    }

    stopTyping(roomId);

    // Clear the composer immediately. Failed messages remain available
    // in the conversation view for retry using the same client_id.
    elements.textarea.value = "";
    resizeTextarea();

    if (attachment) {
        clearSelectedAttachment();
    }

    clearError();

    updateSendAvailability();

    await deliverPending(clientId, payload);
}

async function handleAttachmentChange() {
    if (!elements || uploadInProgress) return;

    const file = elements.attachmentInput.files?.[0];

    if (!file) return;

    clearError();

    if (file.size === 0) {
        elements.attachmentInput.value = "";
        showError("Empty files cannot be uploaded.");
        return;
    }

    if (file.size > MAX_UPLOAD_BYTES) {
        elements.attachmentInput.value = "";
        showError("Files cannot exceed 10 MB.");
        return;
    }

    const token = ++uploadToken;

    uploadInProgress = true;
    updateSendAvailability();

    try {
        const attachment = await upload(file);

        if (!mounted || token !== uploadToken) {
            return;
        }

        if (!attachment || attachment.id == null) {
            throw new Error("The server returned an invalid attachment.");
        }

        displayAttachment(attachment);
        clearError();
    } catch (error) {
        if (mounted && token === uploadToken) {
            elements.attachmentInput.value = "";
            showError(getErrorMessage(error));
        }
    } finally {
        if (token === uploadToken) {
            uploadInProgress = false;
            updateSendAvailability();
        }
    }
}

function handleAttachmentRemove() {
    if (uploadInProgress) return;

    clearSelectedAttachment();
    clearError();
}

function handleTextareaKeydown(event) {
    if (
        event.key !== "Enter" ||
        event.shiftKey ||
        event.isComposing ||
        event.keyCode === 229
    ) {
        return;
    }

    event.preventDefault();

    if (typeof elements.form.requestSubmit === "function") {
        elements.form.requestSubmit();
    } else {
        void sendMessage();
    }
}

function handleStoreChange(nextState) {
    const nextRoomId = nextState.activeRoomId ?? null;

    if (!sameRoom(nextRoomId, observedRoomId)) {
        if (typingActive) {
            stopTyping(observedRoomId);
        }

        observedRoomId = nextRoomId;
    }

    updateSendAvailability();
}

function getElements() {
    const found = {
        form: $("composer-form"),
        textarea: $("message-input"),
        sendButton: $("send-button"),
        error: $("composer-error"),
        attachmentInput: $("attachment-input"),
        attachmentChip: $("attachment-chip"),
        attachmentName: $("attachment-name"),
        attachmentSize: $("attachment-size"),
        attachmentRemove: $("attachment-remove")
    };

    for (const [name, element] of Object.entries(found)) {
        if (!element) {
            throw new Error(
                `Composer cannot start: missing element "${name}".`
            );
        }
    }

    return found;
}

/**
 * Mount the composer and attach its event listeners.
 * Returns the unmount function for convenient lifecycle cleanup.
 */
export function mount() {
    if (mounted) {
        return unmount;
    }

    elements = getElements();
    mounted = true;
    observedRoomId = state.activeRoomId ?? null;

    handlers = {
        submit: (event) => {
            event.preventDefault();
            void sendMessage();
        },

        keydown: handleTextareaKeydown,

        input: () => {
            resizeTextarea();
            clearError();
            handleTypingInput();
        },

        attachmentChange: () => {
            void handleAttachmentChange();
        },

        attachmentRemove: handleAttachmentRemove
    };

    elements.form.addEventListener("submit", handlers.submit);
    elements.textarea.addEventListener("keydown", handlers.keydown);
    elements.textarea.addEventListener("input", handlers.input);
    elements.attachmentInput.addEventListener(
        "change",
        handlers.attachmentChange
    );
    elements.attachmentRemove.addEventListener(
        "click",
        handlers.attachmentRemove
    );

    unsubscribe = subscribe(handleStoreChange);

    resizeTextarea();
    updateSendAvailability();

    return unmount;
}

/**
 * Retry a failed optimistic message using its original client_id.
 * Accepts either the client_id string or a pending message object.
 */
export async function retryPending(clientIdOrMessage) {
    const clientId = typeof clientIdOrMessage === "string"
        ? clientIdOrMessage
        : clientIdOrMessage?.client_id;

    if (typeof clientId !== "string" || !clientId) {
        return false;
    }

    const pending = state.pending.get(clientId);

    if (!pending) {
        return false;
    }

    const payload = pendingPayloads.get(clientId) || {
        room_id: pending.roomId,
        body: pending.body,
        client_id: clientId
    };

    if (inFlight.has(clientId)) {
        return false;
    }

    clearError();

    // Reset the failed state before retrying.
    addPending(clientId, payload.room_id, payload.body);
    pendingPayloads.set(clientId, payload);

    return deliverPending(clientId, payload);
}

/**
 * Remove event listeners and stop the typing signal.
 */
export function unmount() {
    if (!mounted || !elements || !handlers) return;

    stopTyping();

    if (unsubscribe) {
        unsubscribe();
        unsubscribe = null;
    }

    elements.form.removeEventListener("submit", handlers.submit);
    elements.textarea.removeEventListener("keydown", handlers.keydown);
    elements.textarea.removeEventListener("input", handlers.input);
    elements.attachmentInput.removeEventListener(
        "change",
        handlers.attachmentChange
    );
    elements.attachmentRemove.removeEventListener(
        "click",
        handlers.attachmentRemove
    );

    uploadToken += 1;
    uploadInProgress = false;

    mounted = false;
    handlers = null;
    elements = null;
    observedRoomId = null;
}