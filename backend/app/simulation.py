"""Simulation engine: reproducible synthetic microservice log generation.

Fixed random seed makes every demo run identical unless a new seed is given.
"""

import random
from datetime import timedelta
from typing import Any

from app.time_utils import utc_now

SERVICES = [
    {"name": "payment-api", "env": "production"},
    {"name": "order-service", "env": "production"},
    {"name": "inventory-svc", "env": "staging"},
    {"name": "user-session", "env": "production"},
    {"name": "notification-svc", "env": "production"},
    {"name": "catalog-api", "env": "staging"},
]

NORMAL_TEMPLATES = [
    "GET /api/v1/payments 200 45ms",
    "GET /api/v1/orders/{id} 200 32ms",
    "POST /api/v1/inventory 201 110ms",
    "GET /api/v1/sessions/validate 200 18ms",
    "POST /api/v1/notifications 202 55ms",
    "GET /api/v1/catalog 200 28ms",
    "Health check passed",
    "Cache hit for key product:{id}",
    "DB query executed 12ms",
]

INCIDENT_SCENARIOS = [
    {
        "name": "database_connection_pool_exhaustion",
        "services": ["payment-api", "order-service"],
        "messages": [
            "java.sql.SQLException: Unable to acquire connection from pool within 30s",
            "HikariCP pool DataSource is exhausted, max pool size 20 reached",
            "CommunicationsException: Communications link failure",
            "jdbc:postgresql://db.internal:5432/payments Connection refused",
            "Could not obtain pooled connection after 30000ms",
        ],
        "severity": "ERROR",
    },
    {
        "name": "redis_connection_error",
        "services": ["user-session", "payment-api"],
        "messages": [
            "redis.exceptions.ConnectionError: Connection refused",
            "Redis connection refused at 10.0.4.12:6379",
            "ECONNREFUSED ::1:6379",
            "redis-cli ping failed: connection timed out",
        ],
        "severity": "ERROR",
    },
    {
        "name": "k8s_crash_loop",
        "services": ["inventory-svc"],
        "messages": [
            "Back off restarting failed container",
            "CrashLoopBackOff: container inventory-svc exited with code 1",
            "OOMKilled: container memory limit exceeded",
        ],
        "severity": "ERROR",
    },
    {
        "name": "http_5xx_spike",
        "services": ["catalog-api", "notification-svc"],
        "messages": [
            "HTTP/1.1 500 Internal Server Error",
            "status=502 response_time=1240ms",
            "500 Internal Server Error at /api/v1/catalog",
            "response_code=503 service unavailable",
        ],
        "severity": "ERROR",
    },
    {
        "name": "connection_timeout",
        "services": ["order-service", "catalog-api"],
        "messages": [
            "Connection timed out after 10s",
            "Read timed out calling downstream inventory-svc",
            "ConnectTimeout connecting to redis.internal:6379",
            "max retries exceeded with url /api/v1/payments",
        ],
        "severity": "WARN",
    },
]


def generate_events(seed: int = 42, total_events: int = 200) -> list[dict[str, Any]]:
    """Generate reproducible synthetic log events.

    Returns normalized events ready for insertion into the DB.
    """
    rng = random.Random(seed)
    events: list[dict[str, Any]] = []
    now = utc_now()

    for _ in range(total_events):
        service_entry = rng.choice(SERVICES)
        offset_minutes = rng.randint(0, 360)
        ts = now - timedelta(minutes=offset_minutes)
        level = rng.choice(["INFO", "INFO", "INFO", "WARN", "ERROR"])
        msg = rng.choice(NORMAL_TEMPLATES).format(id=rng.randint(1000, 9999))
        events.append(
            {
                "timestamp": ts,
                "service": service_entry["name"],
                "environment": service_entry["env"],
                "level": level,
                "message": msg,
                "raw": msg,
                "_simulation": True,
            }
        )

    # Inject 2-4 incident scenarios
    chosen = rng.sample(INCIDENT_SCENARIOS, k=rng.randint(2, 4))
    for scenario in chosen:
        svc = rng.choice(scenario["services"])
        env = next(s["env"] for s in SERVICES if s["name"] == svc)
        n_msgs = rng.randint(3, 7)
        base = now - timedelta(minutes=rng.randint(5, 60))
        for _ in range(n_msgs):
            ts = base + timedelta(seconds=rng.randint(0, 300))
            msg = rng.choice(scenario["messages"])
            events.append(
                {
                    "timestamp": ts,
                    "service": svc,
                    "environment": env,
                    "level": scenario["severity"],
                    "message": msg,
                    "raw": msg,
                    "_simulation": True,
                }
            )

    events.sort(key=lambda e: e["timestamp"])
    return events
