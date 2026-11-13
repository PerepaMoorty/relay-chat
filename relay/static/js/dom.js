/**
 * F3: Safe DOM creation and formatting helpers.
 * Never uses innerHTML or inline event-handler attributes.
 */

const FORBIDDEN_ATTRIBUTES = new Set([
    "style",
    "innerhtml",
    "outerhtml",
    "srcdoc"
]);

const BOOLEAN_ATTRIBUTES = new Set([
    "disabled",
    "hidden",
    "required",
    "checked",
    "selected",
    "multiple",
    "readonly",
    "autofocus",
    "open",
    "novalidate"
]);

function isNode(value) {
    return (
        value !== null &&
        typeof value === "object" &&
        typeof value.nodeType === "number"
    );
}

function appendChildValue(parent, child) {
    if (child === null || child === undefined || typeof child === "boolean") {
        return;
    }

    if (Array.isArray(child)) {
        for (const item of child) {
            appendChildValue(parent, item);
        }
        return;
    }

    if (isNode(child)) {
        parent.appendChild(child);
        return;
    }

    if (typeof child === "string" || typeof child === "number") {
        parent.appendChild(document.createTextNode(String(child)));
        return;
    }

    throw new TypeError(
        "DOM children must be text, numbers, arrays or DOM nodes."
    );
}

/**
 * Create an element with safe attributes and text/node children.
 *
 * Event handlers must be attached separately with addEventListener().
 */
export function el(tag, attrs, ...children) {
    if (typeof tag !== "string" || !tag.trim()) {
        throw new TypeError("Element tag must be a non-empty string.");
    }

    if (
        attrs === null ||
        attrs === undefined ||
        typeof attrs !== "object" ||
        Array.isArray(attrs) ||
        isNode(attrs)
    ) {
        children.unshift(attrs);
        attrs = {};
    }

    const element = document.createElement(tag);

    for (const [rawName, value] of Object.entries(attrs)) {
        const name = rawName === "className"
            ? "class"
            : rawName === "htmlFor"
                ? "for"
                : rawName;

        const lowerName = name.toLowerCase();

        if (!name || /^on/i.test(name) || FORBIDDEN_ATTRIBUTES.has(lowerName)) {
            throw new TypeError(
                `Unsafe DOM attribute rejected: ${name}`
            );
        }

        if (value === null || value === undefined || value === false) {
            continue;
        }

        if (value === true) {
            if (BOOLEAN_ATTRIBUTES.has(lowerName)) {
                element.setAttribute(name, "");
            } else {
                element.setAttribute(name, "true");
            }
            continue;
        }

        element.setAttribute(name, String(value));
    }

    for (const child of children) {
        appendChildValue(element, child);
    }

    return element;
}

/**
 * Remove all child nodes from an element.
 */
export function clear(node) {
    if (!isNode(node)) {
        throw new TypeError("clear() requires a DOM node.");
    }

    while (node.firstChild) {
        node.removeChild(node.firstChild);
    }

    return node;
}

function parseDate(iso) {
    if (!iso) return null;

    const date = iso instanceof Date ? iso : new Date(iso);

    return Number.isNaN(date.getTime()) ? null : date;
}

function sameLocalDay(left, right) {
    return (
        left.getFullYear() === right.getFullYear() &&
        left.getMonth() === right.getMonth() &&
        left.getDate() === right.getDate()
    );
}

function isYesterday(date) {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    return sameLocalDay(date, yesterday);
}

/**
 * Format an ISO timestamp in local time.
 * Includes the date when the message is not from today.
 */
export function formatTime(iso) {
    const date = parseDate(iso);
    if (!date) return "";

    const time = new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
    }).format(date);

    if (sameLocalDay(date, new Date())) {
        return time;
    }

    const day = new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric"
    }).format(date);

    return `${day}, ${time}`;
}

/**
 * Format a day separator for the conversation view.
 */
export function formatDay(iso) {
    const date = parseDate(iso);
    if (!date) return "";

    if (sameLocalDay(date, new Date())) {
        return "Today";
    }

    if (isYesterday(date)) {
        return "Yesterday";
    }

    return new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        year: "numeric",
        month: "short",
        day: "numeric"
    }).format(date);
}

/**
 * Format a byte count using human-readable units.
 */
export function formatSize(bytes) {
    const value = Number(bytes);

    if (!Number.isFinite(value) || value < 0) {
        return "0 B";
    }

    if (value < 1024) {
        return `${Math.floor(value)} B`;
    }

    const units = ["KB", "MB", "GB", "TB"];
    let size = value / 1024;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex += 1;
    }

    const precision = size >= 10 ? 0 : 1;

    return `${size.toFixed(precision)} ${units[unitIndex]}`;
}

/**
 * Find an element by its ID.
 */
export function $(id) {
    if (typeof id !== "string" || !id.trim()) {
        throw new TypeError("Element ID must be a non-empty string.");
    }

    return document.getElementById(id);
}
