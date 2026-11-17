"""Measure Relay Socket.IO message delivery with concurrent client connections.

Install the optional client dependencies with ``python -m pip install -r requirements-load.txt``.
Run against a disposable or explicitly designated test server; this script sends messages to #general.
"""

from __future__ import annotations

import argparse
import getpass
import json
import math
import os
import platform
import statistics
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import requests
import socketio

MIN_CLIENTS = 20


def percentile(values: list[float], percent: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percent / 100 * len(ordered)) - 1)
    return round(ordered[index], 3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Relay base URL")
    parser.add_argument("--username", default="alice", help="Existing Relay test account")
    parser.add_argument("--password", help="Account password; otherwise prompt or use RELAY_LOAD_PASSWORD")
    parser.add_argument("--clients", type=int, default=20, help="Concurrent Socket.IO connections (default: 20)")
    parser.add_argument("--messages", type=int, default=100, help="Messages sent concurrently (default: 100)")
    parser.add_argument("--transport", choices=("websocket", "polling"), default="websocket")
    parser.add_argument("--timeout", type=float, default=15, help="Per-operation timeout in seconds")
    parser.add_argument("--report", type=Path, help="Write the JSON report to this path")
    args = parser.parse_args()
    if args.clients < 1 or args.messages < 1:
        parser.error("--clients and --messages must both be at least 1")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    args.url = args.url.rstrip("/")
    args.password = args.password or os.environ.get("RELAY_LOAD_PASSWORD")
    if not args.password:
        args.password = getpass.getpass("Relay test account password: ")
    return args


def main() -> int:
    args = parse_args()
    run_id = uuid.uuid4().hex[:12]
    session = requests.Session()
    clients: list[socketio.Client] = []
    errors: list[str] = []
    lock = threading.Condition()
    started_at: dict[str, float] = {}
    acknowledgements: dict[str, tuple[int, float]] = {}
    arrivals: dict[str, list[tuple[int, int, float]]] = {}
    arrival_order: list[list[tuple[str, int]]] = []
    expected_ids = {f"load-{run_id}-{seq:06d}" for seq in range(args.messages)}

    try:
        login = session.post(
            f"{args.url}/api/auth/login",
            json={"username": args.username, "password": args.password},
            timeout=args.timeout,
        )
        if login.status_code != 200 or not login.json().get("ok"):
            raise RuntimeError(f"Login failed with HTTP {login.status_code}")
        rooms_response = session.get(f"{args.url}/api/rooms", timeout=args.timeout)
        if rooms_response.status_code != 200 or not rooms_response.json().get("ok"):
            raise RuntimeError(f"Could not load rooms (HTTP {rooms_response.status_code})")
        general = next(
            (
                room
                for room in rooms_response.json()["data"]["rooms"]
                if room["kind"] == "public" and room["name"] == "general"
            ),
            None,
        )
        if general is None:
            raise RuntimeError("The account is not a member of #general")
        room_id = general["id"]
        cookies = session.cookies.get_dict()
        if not cookies:
            raise RuntimeError("Login succeeded but no session cookie was returned")
        cookie_header = "; ".join(f"{name}={value}" for name, value in cookies.items())

        def on_message(client_index: int, data: dict) -> None:
            message = data.get("message", {}) if isinstance(data, dict) else {}
            client_id = message.get("client_id")
            message_id = message.get("id")
            if client_id not in expected_ids or not isinstance(message_id, int):
                return
            received_at = time.perf_counter()
            with lock:
                arrivals.setdefault(client_id, []).append((client_index, message_id, received_at))
                arrival_order[client_index].append((client_id, message_id))
                lock.notify_all()

        for client_index in range(args.clients):
            client = socketio.Client(reconnection=False, logger=False, engineio_logger=False)
            client.on("message:new", lambda data, index=client_index: on_message(index, data))
            clients.append(client)
        arrival_order = [[] for _ in clients]

        connect_started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.clients) as pool:
            futures = [
                pool.submit(
                    client.connect,
                    args.url,
                    headers={"Cookie": cookie_header},
                    transports=[args.transport],
                    wait_timeout=args.timeout,
                )
                for client in clients
            ]
            for future in as_completed(futures, timeout=args.timeout + 5):
                future.result()
        connect_duration = time.perf_counter() - connect_started
        if not all(client.connected for client in clients):
            raise RuntimeError("One or more Socket.IO clients did not connect")

        def send_batch(client_index: int) -> None:
            client = clients[client_index]
            for seq in range(client_index, args.messages, args.clients):
                client_id = f"load-{run_id}-{seq:06d}"
                started = time.perf_counter()
                with lock:
                    started_at[client_id] = started
                ack = client.call(
                    "message:send",
                    {"room_id": room_id, "body": f"T9 load message {seq}", "client_id": client_id},
                    timeout=args.timeout,
                )
                acked_at = time.perf_counter()
                if not isinstance(ack, dict) or not ack.get("ok"):
                    with lock:
                        errors.append(f"Message {seq} received an unsuccessful acknowledgement")
                    continue
                message = ack.get("data", {}).get("message", {})
                if message.get("client_id") != client_id or not isinstance(message.get("id"), int):
                    with lock:
                        errors.append(f"Message {seq} acknowledgement did not match its client_id")
                    continue
                with lock:
                    acknowledgements[client_id] = (message["id"], acked_at)

        send_started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.clients) as pool:
            futures = [pool.submit(send_batch, i) for i in range(args.clients)]
            for future in as_completed(
                futures, timeout=args.timeout * max(1, math.ceil(args.messages / args.clients)) + 5
            ):
                future.result()
        send_duration = time.perf_counter() - send_started

        with lock:
            all_delivered = lock.wait_for(
                lambda: all(
                    len({client_index for client_index, _message_id, _received_at in arrivals.get(client_id, [])})
                    >= args.clients
                    for client_id in acknowledgements
                ),
                timeout=args.timeout,
            )

        ack_latencies = [
            (acked_at - started_at[client_id]) * 1000 for client_id, (_message_id, acked_at) in acknowledgements.items()
        ]
        delivery_latencies = [
            (received_at - started_at[client_id]) * 1000
            for client_id, deliveries in arrivals.items()
            for _client_index, _message_id, received_at in deliveries
        ]
        per_message_delivery = [
            max((received_at - started_at[client_id]) * 1000 for _idx, _id, received_at in arrivals.get(client_id, []))
            for client_id in acknowledgements
            if arrivals.get(client_id)
        ]
        expected_message_ids = sorted(message_id for message_id, _acked_at in acknowledgements.values())
        ordering_failures = []
        ordering_examples = []
        for client_index, ordered_events in enumerate(arrival_order):
            observed_ids = [message_id for client_id, message_id in ordered_events if client_id in acknowledgements]
            inversion = next(
                (
                    position
                    for position in range(1, len(observed_ids))
                    if observed_ids[position] < observed_ids[position - 1]
                ),
                None,
            )
            if inversion is not None:
                ordering_failures.append(client_index)
                ordering_examples.append(
                    {
                        "receiver": client_index,
                        "previous_message_id": observed_ids[inversion - 1],
                        "next_message_id": observed_ids[inversion],
                        "first_observed_ids": observed_ids[:12],
                    }
                )

        all_clients_received_all = (
            bool(acknowledgements)
            and all_delivered
            and all(
                len({client_index for client_index, _message_id, _received_at in arrivals.get(client_id, [])})
                == args.clients
                for client_id in acknowledgements
            )
        )
        ordering_passed = not ordering_failures and len(acknowledgements) == args.messages
        criteria = {
            "at_least_20_clients_connected": args.clients >= MIN_CLIENTS
            and all(client.connected for client in clients),
            "every_message_acknowledged": len(acknowledgements) == args.messages and not errors,
            "every_client_received_every_message": all_clients_received_all,
            "message_ids_arrived_in_order": ordering_passed,
        }
        passed = all(criteria.values())
        report = {
            "registry_id": "T9",
            "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "status": "PASS" if passed else "FAIL",
            "target": args.url,
            "transport": args.transport,
            "authenticated_user": args.username,
            "concurrent_connections": args.clients,
            "unique_accounts": 1,
            "room": "#general",
            "requested_messages": args.messages,
            "acknowledged_messages": len(acknowledgements),
            "delivery_count": sum(len(deliveries) for deliveries in arrivals.values()),
            "connection_setup_seconds": round(connect_duration, 3),
            "send_phase_seconds": round(send_duration, 3),
            "ack_latency_ms": {
                "mean": round(statistics.mean(ack_latencies), 3) if ack_latencies else None,
                "p50": percentile(ack_latencies, 50),
                "p95": percentile(ack_latencies, 95),
                "max": round(max(ack_latencies), 3) if ack_latencies else None,
            },
            "delivery_latency_ms": {
                "mean": round(statistics.mean(delivery_latencies), 3) if delivery_latencies else None,
                "p50": percentile(delivery_latencies, 50),
                "p95": percentile(delivery_latencies, 95),
                "max": round(max(delivery_latencies), 3) if delivery_latencies else None,
                "per_message_max_p95": percentile(per_message_delivery, 95),
            },
            "ordering": {
                "passed": ordering_passed,
                "receivers_with_out_of_order_messages": ordering_failures,
                "out_of_order_examples": ordering_examples[:5],
                "message_ids": expected_message_ids,
            },
            "criteria": criteria,
            "latency_threshold": "Not evaluated: docs/test-plan.md specifies measurement but no numeric target.",
            "errors": errors,
            "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        }
        rendered = json.dumps(report, indent=2)
        print(rendered)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered + "\n", encoding="utf-8")
            print(f"Report written to {args.report}", file=sys.stderr)
        return 0 if passed else 1
    except Exception as exc:
        print(f"Load test failed: {exc}", file=sys.stderr)
        return 1
    finally:
        disconnect_threads = []
        for index, client in enumerate(clients):
            if client.connected:
                worker = threading.Thread(target=client.disconnect, daemon=True, name=f"load-disconnect-{index}")
                worker.start()
                disconnect_threads.append(worker)
        for worker in disconnect_threads:
            worker.join(timeout=5)
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
