/**
 * F2: REST API client.
 * Handles the common response envelope, API errors and file uploads.
 */

export class ApiError extends Error {
    constructor(message, { code = "INTERNAL", status = 0, details = null } = {}) {
        super(message);
        this.name = "ApiError";
        this.code = code;
        this.status = status;
        this.details = details;
    }
}

function invalidResponse(status) {
    return new ApiError(
        "The server returned an invalid response.",
        { code: "INVALID_RESPONSE", status }
    );
}

/**
 * Send a same-origin REST request.
 * Resolves to the response's data field.
 */
export async function api(method, path, body) {
    if (typeof method !== "string" || !method.trim()) {
        throw new TypeError("HTTP method must be a non-empty string.");
    }

    if (typeof path !== "string" || !path.startsWith("/")) {
        throw new TypeError("API path must be a same-origin absolute path.");
    }

    const headers = {
        Accept: "application/json"
    };

    const options = {
        method: method.toUpperCase(),
        credentials: "same-origin",
        headers
    };

    if (body !== undefined) {
        if (typeof FormData !== "undefined" && body instanceof FormData) {
            // Let the browser set the multipart boundary.
            options.body = body;
        } else {
            headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }
    }

    let response;

    try {
        response = await fetch(path, options);
    } catch (_error) {
        throw new ApiError(
            "Unable to connect to the server. Check your network connection.",
            { code: "NETWORK", status: 0 }
        );
    }

    let payload;

    try {
        payload = await response.json();
    } catch (_error) {
        throw invalidResponse(response.status);
    }

    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        throw invalidResponse(response.status);
    }

    if (payload.ok === false) {
        const error = payload.error;

        throw new ApiError(
            typeof error?.message === "string"
                ? error.message
                : "The request failed.",
            {
                code: typeof error?.code === "string"
                    ? error.code
                    : "INTERNAL",
                status: response.status,
                details: error?.details ?? null
            }
        );
    }

    if (!response.ok) {
        throw new ApiError(
            `Request failed with HTTP status ${response.status}.`,
            { code: "HTTP_ERROR", status: response.status }
        );
    }

    if (
        payload.ok !== true ||
        !Object.prototype.hasOwnProperty.call(payload, "data")
    ) {
        throw invalidResponse(response.status);
    }

    return payload.data;
}

/**
 * Upload one file to POST /api/files.
 * Resolves to the attachment object.
 */
export async function upload(file) {
    if (!file || typeof file.name !== "string") {
        throw new ApiError(
            "A valid file must be selected.",
            { code: "VALIDATION_ERROR", status: 0 }
        );
    }

    const form = new FormData();
    form.append("file", file, file.name);

    const data = await api("POST", "/api/files", form);

    if (!data || !data.attachment) {
        throw invalidResponse(201);
    }

    return data.attachment;
}
