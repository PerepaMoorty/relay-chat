/**
 * F10: Admin console.
 * Renders reports, users, audit logs, connected clients and activity.
 */

import { api } from "../api.js";
import { $, el, clear } from "../dom.js";

const TAB_INFO = {
    reports: {
        heading: "Reports",
        description: "Review and resolve reported messages."
    },
    users: {
        heading: "Users",
        description: "Manage user access, bans and temporary mutes."
    },
    audit: {
        heading: "Audit log",
        description: "Review recorded administrative actions."
    },
    clients: {
        heading: "Connected clients",
        description: "See users currently connected to the server."
    },
    activity: {
        heading: "Server activity",
        description: "Review connection events and server errors."
    }
};

let mounted = false;
let activeTab = "reports";
let requestToken = 0;
let elements = null;

function button(label, className, onClick) {
    const result = el("button", {
        type: "button",
        class: className,
        textContent: undefined
    }, label);

    result.addEventListener("click", onClick);
    return result;
}

function formatDate(value) {
    if (!value) return "—";

    const date = new Date(value);
    return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleString();
}

function paragraph(label, value) {
    return el("p", { class: "admin-record-detail" },
        el("strong", {}, `${label}: `),
        value == null || value === "" ? "—" : String(value)
    );
}

function recordCard(title, details = []) {
    const card = el("article", { class: "admin-record" });
    card.appendChild(el("h3", { class: "admin-record-title" }, title));

    for (const detail of details) {
        card.appendChild(detail);
    }

    return card;
}

function showEmpty(message) {
    clear(elements.body);
    elements.body.appendChild(
        el("p", { class: "empty-state" }, message)
    );
}

function showError(error) {
    clear(elements.body);
    elements.body.appendChild(
        el("p", { class: "inline-error", role: "alert" },
            error?.message || "Could not load admin data."
        )
    );
}

function setActiveTab(tab) {
    if (!Object.hasOwn(TAB_INFO, tab)) return;

    activeTab = tab;

    for (const tabButton of elements.tabs.querySelectorAll("[data-tab]")) {
        const selected = tabButton.dataset.tab === tab;
        tabButton.classList.toggle("is-active", selected);
        tabButton.setAttribute("aria-selected", String(selected));
    }

    elements.panel.setAttribute(
        "aria-labelledby",
        `admin-tab-${tab}`
    );

    elements.heading.textContent = TAB_INFO[tab].heading;
    elements.description.textContent = TAB_INFO[tab].description;

    void loadActiveTab();
}

function appendCards(items, renderer, emptyMessage) {
    clear(elements.body);

    if (!Array.isArray(items) || items.length === 0) {
        elements.body.appendChild(
            el("p", { class: "empty-state" }, emptyMessage)
        );
        return;
    }

    for (const item of items) {
        elements.body.appendChild(renderer(item));
    }
}

function renderReports(reports) {
    appendCards(reports, report => {
        const message = report.message || {};
        const sender = message.sender?.username || "Unknown user";
        const messageText = message.deleted
            ? "[Message deleted]"
            : (message.body || "[No message text]");

        const card = recordCard(`Report #${report.id}`, [
            paragraph("Reported user", sender),
            paragraph("Message", messageText),
            paragraph("Reason", report.reason),
            paragraph("Reported by", report.reporter),
            paragraph("Status", report.status),
            paragraph("Reported at", formatDate(report.created_at))
        ]);

        const actions = el("div", { class: "admin-record-actions" });

        const removeButton = button(
            "Remove message",
            "button button-danger-text",
            async () => {
                if (!window.confirm(
                    "Remove this message and resolve the report?"
                )) return;

                removeButton.disabled = true;

                try {
                    await api(
                        "POST",
                        `/api/admin/reports/${report.id}/resolve`,
                        {
                            action: "delete",
                            reason: "Removed after moderator review"
                        }
                    );
                    await loadActiveTab();
                } catch (error) {
                    window.alert(error.message || "Could not resolve report.");
                    removeButton.disabled = false;
                }
            }
        );

        const dismissButton = button(
            "Dismiss",
            "button button-secondary",
            async () => {
                if (!window.confirm("Dismiss this report?")) return;

                dismissButton.disabled = true;

                try {
                    await api(
                        "POST",
                        `/api/admin/reports/${report.id}/resolve`,
                        { action: "dismiss" }
                    );
                    await loadActiveTab();
                } catch (error) {
                    window.alert(error.message || "Could not dismiss report.");
                    dismissButton.disabled = false;
                }
            }
        );

        actions.append(removeButton, dismissButton);
        card.appendChild(actions);
        return card;
    }, "There are no open reports.");
}

async function performUserAction(user, action) {
    const body = {};

    if (action === "ban" || action === "mute") {
        const reason = window.prompt(
            action === "ban" ? "Reason for banning this user:" : "Reason for muting this user:"
        );

        if (reason === null) return;

        if (!reason.trim()) {
            window.alert("A reason is required.");
            return;
        }

        body.reason = reason.trim();
    }

    if (action === "mute") {
        const minutesValue = window.prompt(
            "Mute duration in minutes (15 to 10080):",
            "60"
        );

        if (minutesValue === null) return;

        const minutes = Number(minutesValue);

        if (!Number.isInteger(minutes) || minutes < 15 || minutes > 10080) {
            window.alert("Enter a whole number between 15 and 10080.");
            return;
        }

        body.minutes = minutes;
    }

    const descriptions = {
        ban: "Ban this user?",
        unban: "Unban this user?",
        mute: "Mute this user?",
        unmute: "Remove this user's mute?"
    };

    if (!window.confirm(descriptions[action])) return;

    try {
        await api(
            "POST",
            `/api/admin/users/${user.id}/${action}`,
            body
        );
        await loadActiveTab();
    } catch (error) {
        window.alert(error.message || `Could not ${action} user.`);
    }
}

function renderUsers(users) {
    appendCards(users, user => {
        const card = recordCard(user.username || `User #${user.id}`, [
            paragraph("User ID", user.id),
            paragraph("Role", user.role),
            paragraph("Account created", formatDate(user.created_at)),
            paragraph("Banned", user.banned ? "Yes" : "No"),
            paragraph("Muted until", formatDate(user.muted_until))
        ]);

        const actions = el("div", { class: "admin-record-actions" });

        if (user.banned) {
            actions.appendChild(button(
                "Unban",
                "button button-secondary",
                () => void performUserAction(user, "unban")
            ));
        } else {
            actions.appendChild(button(
                "Ban",
                "button button-danger-text",
                () => void performUserAction(user, "ban")
            ));
        }

        if (user.muted_until) {
            actions.appendChild(button(
                "Unmute",
                "button button-secondary",
                () => void performUserAction(user, "unmute")
            ));
        } else {
            actions.appendChild(button(
                "Mute",
                "button button-secondary",
                () => void performUserAction(user, "mute")
            ));
        }

        card.appendChild(actions);
        return card;
    }, "No users found.");
}

function renderAudit(entries) {
    appendCards(entries, entry => recordCard(
        `${entry.action || "Action"} — ${entry.actor || "Unknown admin"}`,
        [
            paragraph(
                "Target",
                `${entry.target_type || "—"} #${entry.target_id ?? "—"}`
            ),
            paragraph("Reason", entry.reason),
            paragraph("Time", formatDate(entry.created_at))
        ]
    ), "No audit entries recorded.");
}

function renderClients(clients) {
    appendCards(clients, client => recordCard(
        client.username || "Unknown user",
        [
            paragraph("Session", client.sid),
            paragraph("Connected at", formatDate(client.connected_at))
        ]
    ), "No clients are currently connected.");
}

function renderActivity(entries) {
    appendCards(entries, entry => recordCard(
        `${entry.kind || "Event"} — ${entry.user || "System"}`,
        [
            paragraph("Details", entry.detail),
            paragraph("Time", formatDate(entry.created_at))
        ]
    ), "No activity entries recorded.");
}

async function loadActiveTab() {
    const token = ++requestToken;
    showEmpty("Loading...");

    try {
        let data;

        switch (activeTab) {
            case "reports":
                data = await api("GET", "/api/admin/reports?status=open");
                if (token === requestToken) renderReports(data.reports);
                break;

            case "users":
                data = await api("GET", "/api/admin/users");
                if (token === requestToken) renderUsers(data.users);
                break;

            case "audit":
                data = await api("GET", "/api/admin/audit");
                if (token === requestToken) renderAudit(data.entries);
                break;

            case "clients":
                data = await api("GET", "/api/admin/clients");
                if (token === requestToken) renderClients(data.clients);
                break;

            case "activity":
                data = await api("GET", "/api/admin/activity");
                if (token === requestToken) renderActivity(data.entries);
                break;

            default:
                showEmpty("Choose an admin section.");
        }
    } catch (error) {
        if (token === requestToken) showError(error);
    }
}

/**
 * Called when an admin opens the admin screen.
 */
export function show() {
    if (!mounted) mount();
    void loadActiveTab();
}

/**
 * Mount once during application initialization.
 * The report-button handler is also available to non-admin users.
 */
export function mount() {
    if (mounted) return;

    elements = {
        tabs: $("admin-tabs"),
        panel: $("admin-panel"),
        body: $("admin-body"),
        heading: $("admin-panel")?.querySelector("h2"),
        description: $("admin-panel")?.querySelector(".admin-panel-heading p"),
        refresh: $("admin-refresh-button")
    };

    for (const [name, element] of Object.entries(elements)) {
        if (!element) {
            throw new Error(`Admin view cannot start: missing ${name}.`);
        }
    }

    elements.tabs.addEventListener("click", event => {
        const tabButton = event.target.closest("[data-tab]");
        if (!tabButton || !elements.tabs.contains(tabButton)) return;

        setActiveTab(tabButton.dataset.tab);
    });

    elements.refresh.addEventListener("click", () => {
        void loadActiveTab();
    });

    document.addEventListener("click", async event => {
        const reportButton = event.target instanceof Element
            ? event.target.closest("[data-report-button]")
            : null;

        if (!reportButton || reportButton.disabled) return;

        const messageContainer = reportButton.closest("[data-report-message-id]");
        const messageId = messageContainer?.getAttribute("data-report-message-id");

        if (!messageId) return;

        const reason = window.prompt("Why are you reporting this message?");
        if (reason === null) return;

        if (!reason.trim()) {
            window.alert("Please provide a reason for the report.");
            return;
        }

        reportButton.disabled = true;

        try {
            await api(
                "POST",
                `/api/messages/${encodeURIComponent(messageId)}/report`,
                { reason: reason.trim().slice(0, 200) }
            );

            reportButton.textContent = "Reported";
        } catch (error) {
            window.alert(error.message || "Could not submit the report.");
            reportButton.disabled = false;
        }
    });

    mounted = true;
}
