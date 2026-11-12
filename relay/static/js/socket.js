/**
 * F2: Socket.IO client connection.
 * Uses the locally vendored Socket.IO browser client.
 */

import { ApiError } from "./api.js";

let socketInstance = null;
let statusHandler = null;
let reconnectStopped = false;
let manualDisconnect = false;

function reportStatus(status) {
    if (typeof statusHandler !== "function") {
        return;
    }

    try {
        statusHandler(status);
    } catch (error) {
        console.error("Socket status handler failed:", error);
    }
}

function makeAckError(error) {
    return new ApiError(
        typeof error?.message === "string"
            ? error.message
            : "The server rejected the socket request.",
        {
            code: typeof error?.code === "string"
                ? error.code
                : "INTERNAL",
            status: 0,
            details: error?.details ?? null
        }
    );
}

/**
 * Connect after successful login.
 *
 * Options:
 * {
 *   on: { "message:new": handler, ... },
 *   onStatus: (status) => {},
 *   onConnected: () => {}
 * }
 */
export function connect({
    on = {},
    onStatus = () => {},
    onConnected
} = {}) {
    if (typeof globalThis.io !== "function") {
        throw new ApiError(
            "Socket.IO client library is not loaded.",
            { code: "SOCKET_UNAVAILABLE", status: 0 }
        );
    }

    if (!on || typeof on !== "object" || Array.isArray(on)) {
        throw new TypeError("Socket event handlers must be an object.");
    }

    // Dispose of an earlier connection before creating a new one.
    if (socketInstance) {
        socketInstance.io.reconnection(false);
        socketInstance.disconnect();
        socketInstance.removeAllListeners();
        socketInstance = null;
    }

    reconnectStopped = false;
    manualDisconnect = false;

    statusHandler = typeof onStatus === "function"
        ? onStatus
        : () => {};

    reportStatus("reconnecting");

    // Connect to the current origin. The browser sends its same-origin
    // session cookie as part of the Socket.IO handshake.
    const activeSocket = globalThis.io(window.location.origin, {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 10000
    });

    socketInstance = activeSocket;

    activeSocket.on("connect", () => {
        if (activeSocket !== socketInstance) {
            return;
        }

        reportStatus("connected");

        if (typeof onConnected === "function") {
            Promise.resolve()
                .then(() => onConnected())
                .catch((error) => {
                    console.error("Socket onConnected callback failed:", error);
                });
        }
    });

    activeSocket.on("disconnect", () => {
        if (activeSocket !== socketInstance) {
            return;
        }

        if (reconnectStopped || manualDisconnect) {
            reportStatus("offline");
        } else {
            reportStatus("reconnecting");
        }
    });

    activeSocket.on("connect_error", () => {
        if (activeSocket !== socketInstance) {
            return;
        }

        if (reconnectStopped) {
            reportStatus("offline");
        } else {
            reportStatus("reconnecting");
        }
    });

    // Register all event handlers supplied by the application.
    for (const [event, handler] of Object.entries(on)) {
        if (typeof handler !== "function") {
            throw new TypeError(`Handler for "${event}" must be a function.`);
        }

        activeSocket.on(event, handler);
    }

    return activeSocket;
}

/**
 * Emit an event and resolve with the server acknowledgement's data.
 */
export function emitAck(event, payload, timeoutMs = 10000) {
    return new Promise((resolve, reject) => {
        if (!socketInstance || !socketInstance.connected) {
            reject(new ApiError(
                "Socket is not connected.",
                { code: "OFFLINE", status: 0 }
            ));
            return;
        }

        if (typeof event !== "string" || !event.trim()) {
            reject(new TypeError("Socket event must be a non-empty string."));
            return;
        }

        if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
            reject(new TypeError("Timeout must be a positive number."));
            return;
        }

        const activeSocket = socketInstance;

        activeSocket.timeout(timeoutMs).emit(
            event,
            payload,
            (timeoutError, response) => {
                if (timeoutError) {
                    reject(new ApiError(
                        "The server did not acknowledge the request in time.",
                        { code: "TIMEOUT", status: 0 }
                    ));
                    return;
                }

                if (
                    !response ||
                    typeof response !== "object" ||
                    Array.isArray(response)
                ) {
                    reject(new ApiError(
                        "The server returned an invalid socket acknowledgement.",
                        { code: "INVALID_RESPONSE", status: 0 }
                    ));
                    return;
                }

                if (response.ok === false) {
                    reject(makeAckError(response.error));
                    return;
                }

                if (
                    response.ok !== true ||
                    !Object.prototype.hasOwnProperty.call(response, "data")
                ) {
                    reject(new ApiError(
                        "The server returned an invalid socket acknowledgement.",
                        { code: "INVALID_RESPONSE", status: 0 }
                    ));
                    return;
                }

                resolve(response.data);
            }
        );
    });
}

/**
 * Manually disconnect the current socket.
 * A later connect() call can establish a new connection.
 */
export function disconnect() {
    if (socketInstance) {
        manualDisconnect = true;
        socketInstance.disconnect();
        manualDisconnect = false;
    }

    reportStatus("offline");
}

/**
 * Permanently stop automatic reconnection for this connection.
 * Used when the server terminates the user's session.
 */
export function stopReconnecting() {
    reconnectStopped = true;

    if (socketInstance) {
        socketInstance.io.reconnection(false);

        manualDisconnect = true;
        socketInstance.disconnect();
        manualDisconnect = false;
    }

    reportStatus("offline");
}
