/**
 * F4: Login and registration view.
 * Uses the shared REST API client and application store.
 */

import { api, ApiError } from "../api.js";
import { setMe } from "../store.js";
import { $ } from "../dom.js";

const USERNAME_PATTERN = /^[a-z0-9_]{3,20}$/;
const MIN_PASSWORD_LENGTH = 8;

let mounted = false;
let registerMode = false;
let submitting = false;
let onLoggedIn = null;
let currentNotice = "";

function getElements() {
    return {
        view: $("auth-view"),
        title: $("auth-title"),
        description: $("auth-description"),
        form: $("auth-form"),
        username: $("auth-username"),
        password: $("auth-password"),
        error: $("auth-error"),
        submit: $("auth-submit"),
        toggle: $("auth-mode-toggle"),
        switchCopy: $("auth-switch-copy"),
        notice: $("auth-notice")
    };
}

function showError(message) {
    const { error } = getElements();
    if (!error) return;

    error.textContent = String(message);
    error.hidden = false;
}

function clearError() {
    const { error } = getElements();
    if (!error) return;

    error.textContent = "";
    error.hidden = true;
}

function showNotice(message) {
    const { notice } = getElements();
    if (!notice) return;

    notice.textContent = message ? String(message) : "";
    notice.hidden = !message;
}

function updateMode() {
    const elements = getElements();

    if (!elements.title || !elements.submit || !elements.toggle) {
        return;
    }

    if (registerMode) {
        elements.title.textContent = "Create your account";
        elements.description.textContent =
            "Join Relay and start collaborating with your team.";
        elements.submit.textContent = "Create account";
        elements.toggle.textContent = "Log in";

        if (elements.switchCopy) {
            elements.switchCopy.textContent = "Already on Relay?";
        }

        if (elements.password) {
            elements.password.autocomplete = "new-password";
        }
    } else {
        elements.title.textContent = "Welcome back";
        elements.description.textContent =
            "Log in to pick up where your team left off.";
        elements.submit.textContent = "Log in";
        elements.toggle.textContent = "Create an account";

        if (elements.switchCopy) {
            elements.switchCopy.textContent = "New to Relay?";
        }

        if (elements.password) {
            elements.password.autocomplete = "current-password";
        }
    }

    clearError();
    showNotice(currentNotice);
}

function validateCredentials(username, password) {
    if (!USERNAME_PATTERN.test(username)) {
        return "Username must contain 3–20 characters using letters, numbers and underscores.";
    }

    if (typeof password !== "string" || password.length < MIN_PASSWORD_LENGTH) {
        return "Password must contain at least 8 characters.";
    }

    return null;
}

function setSubmitting(value) {
    submitting = value;

    const elements = getElements();

    if (elements.submit) {
        elements.submit.disabled = value;
        elements.submit.textContent = value
            ? "Please wait…"
            : registerMode
                ? "Create account"
                : "Log in";
    }

    if (elements.form) {
        elements.form.setAttribute("aria-busy", String(value));
    }
}

function serverErrorMessage(error) {
    if (error instanceof ApiError && error.message) {
        // Always display the message returned by the server.
        return error.message;
    }

    if (error instanceof Error && error.message) {
        return error.message;
    }

    return "Something went wrong. Please try again.";
}

async function handleSubmit(event) {
    event.preventDefault();

    if (submitting) return;

    const elements = getElements();

    if (!elements.username || !elements.password) {
        showError("The login form is not available.");
        return;
    }

    const username = elements.username.value.trim().toLowerCase();
    const password = elements.password.value;

    const validationError = validateCredentials(username, password);

    if (validationError) {
        showError(validationError);
        return;
    }

    // Keep the username normalized before sending it.
    elements.username.value = username;

    clearError();
    setSubmitting(true);

    const endpoint = registerMode
        ? "/api/auth/register"
        : "/api/auth/login";

    try {
        const data = await api("POST", endpoint, {
            username,
            password
        });

        if (!data || !data.user || typeof data.user !== "object") {
            throw new ApiError(
                "The server did not return a valid user account.",
                { code: "INVALID_RESPONSE", status: 0 }
            );
        }

        const user = data.user;

        // Store the authenticated user. Routing is handled by the caller.
        setMe(user);

        elements.password.value = "";
        currentNotice = "";
        showNotice("");

        if (typeof onLoggedIn === "function") {
            try {
                await onLoggedIn(user);
            } catch (callbackError) {
                console.error(
                    "The login success callback failed:",
                    callbackError
                );

                showError(
                    "Authentication succeeded, but the application could not open your workspace. Please refresh."
                );
            }
        }
    } catch (error) {
        showError(serverErrorMessage(error));
    } finally {
        setSubmitting(false);
    }
}

function handleModeToggle() {
    if (submitting) return;

    registerMode = !registerMode;

    const elements = getElements();

    if (elements.password) {
        elements.password.value = "";
    }

    updateMode();
}

/**
 * Mount the login view.
 *
 * Options:
 * {
 *   onLoggedIn: (user) => {},
 *   notice: "Optional session termination notice"
 * }
 */
export function mount(options = {}) {
    if (!options || typeof options !== "object") {
        throw new TypeError("Login mount options must be an object.");
    }

    onLoggedIn = typeof options.onLoggedIn === "function"
        ? options.onLoggedIn
        : null;

    currentNotice = options.notice ?? "";

    const elements = getElements();

    if (
        !elements.form ||
        !elements.username ||
        !elements.password ||
        !elements.submit ||
        !elements.toggle
    ) {
        throw new Error("Required login form elements were not found.");
    }

    if (!mounted) {
        elements.form.addEventListener("submit", handleSubmit);
        elements.toggle.addEventListener("click", handleModeToggle);

        elements.username.addEventListener("input", clearError);
        elements.password.addEventListener("input", clearError);

        mounted = true;
    }

    updateMode();
}

/**
 * Render visibility and notice state from the application store.
 */
export function render(appState) {
    if (!appState) return;

    const { view } = getElements();

    if (view && appState.view !== undefined) {
        view.hidden = appState.view !== "login";
    }

    const loading = $("loading-state");

    if (loading && appState.view !== undefined) {
        loading.hidden = true;
    }

    showNotice(currentNotice);
}
