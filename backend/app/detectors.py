"""Rule-based incident detection and correlation engine.

No external AI is used. Detection is deterministic and based on regex
signatures, time-window correlation, and severity assignment.
"""

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from app.time_utils import utc_now


@dataclass
class DetectionRule:
    name: str
    display_name: str
    severity: str  # INFO | WARNING | CRITICAL
    patterns: list[str]  # compiled regexes matched against the message
    confidence: float
    root_cause_template: str
    investigation_steps: list[str]
    remediation_actions: list[str]
    root_cause_confidence: str = "speculative"  # speculative | likely | confirmed
    min_events: int = 1


# All detection rules. Order matters for first-match assignment.
DETECTION_RULES: list[DetectionRule] = [
    DetectionRule(
        name="k8s_crash_loop",
        display_name="Kubernetes CrashLoopBackOff",
        severity="CRITICAL",
        patterns=[r"CrashLoopBackOff", r"Back.?off.?restarting.?failed.?container"],
        confidence=0.9,
        root_cause_template="Pod {service} is stuck in a crash loop ({pattern}). Container repeatedly exits non-zero.",
        investigation_steps=[
            "kubectl logs <pod> -n <namespace>",
            "kubectl describe pod <pod> -n <namespace>",
            "Check recent image deployments and configmap/secret changes",
        ],
        remediation_actions=[
            "Roll back the last deployment",
            "Fix container entrypoint or health-check configuration",
            "Increase resource limits if OOMKilled",
        ],
        root_cause_confidence="likely",
    ),
    DetectionRule(
        name="jdbc_connection_failure",
        display_name="JDBC Connection Failure",
        severity="CRITICAL",
        patterns=[
            r"java\.sql\.SQLException",
            r"CommunicationsException",
            r"Connection refused.*(?:port\s+)?(?:3306|5432|1521|1433)",
            r"jdbc:.*Connection refused",
            r"Pool.*exhausted|ConnectionPool.*exhausted",
        ],
        confidence=0.85,
        root_cause_template="Database connectivity failure for {service}. The application cannot obtain JDBC connections ({pattern}).",
        investigation_steps=[
            "Verify database server is reachable from the service namespace",
            "Check database max_connections and current connection count",
            "Inspect application HikariCP / connection-pool settings",
            "Review firewall / security-group rules on port 5432/3306",
        ],
        remediation_actions=[
            "Restart application pods to reset the connection pool",
            "Increase database max_connections or connection-pool max size",
            "Scale read replicas if read-heavy",
        ],
        root_cause_confidence="likely",
    ),
    DetectionRule(
        name="redis_connection_error",
        display_name="Redis Connectivity Problem",
        severity="CRITICAL",
        patterns=[
            r"redis\.exceptions\.ConnectionError",
            r"Redis connection refused",
            r"redis.*Connection timed out",
            r"ECONNREFUSED.*6379|6379.*ECONNREFUSED",
        ],
        confidence=0.88,
        root_cause_template="Redis cache/service unreachable for {service} ({pattern}). Sessions or cache-dependent paths may fail.",
        investigation_steps=[
            "Check Redis pod/service status: kubectl get svc,pod -l app=redis",
            "Test connectivity: redis-cli -h <redis-host> -p 6379 ping",
            "Inspect Redis maxmemory and eviction policy",
        ],
        remediation_actions=[
            "Restart Redis pod or failover to replica",
            "Clear stale keys / increase maxmemory",
            "Verify service discovery (DNS) for Redis endpoint",
        ],
        root_cause_confidence="likely",
    ),
    DetectionRule(
        name="http_5xx_spike",
        display_name="HTTP 5xx Spike",
        severity="WARNING",
        patterns=[r"HTTP/1\.[01]\"?\s+5\d{2}", r"status=5\d{2}", r"response_code=5\d{2}", r"500 Internal Server Error"],
        confidence=0.7,
        root_cause_template="Elevated HTTP 5xx responses from {service} ({pattern}). Possibly related to a recent deployment or downstream dependency failure.",
        investigation_steps=[
            "Correlate with recent deployment timestamps",
            "Check downstream service health (database, Redis, external APIs)",
            "Inspect application error stack traces around the spike",
        ],
        remediation_actions=[
            "Roll back the deployment if correlated with a release",
            "Increase replica count and enable circuit breakers",
            "Page on-call if the spike persists >5 minutes",
        ],
        root_cause_confidence="speculative",
        min_events=3,
    ),
    DetectionRule(
        name="connection_timeout",
        display_name="Connection Timeout",
        severity="WARNING",
        patterns=[r"Connection timed out", r"ReadTimeout|Read timed out", r"ConnectTimeout|Connect timed out", r"max retries exceeded with url"],
        confidence=0.75,
        root_cause_template="Network timeout detected for {service} ({pattern}). Downstream dependency may be slow or unreachable.",
        investigation_steps=[
            "Identify the target host/port from surrounding log context",
            "Check target service latency and CPU/memory pressure",
            "Review timeout and retry configuration in the client",
        ],
        remediation_actions=[
            "Scale the slow downstream dependency",
            "Add client-side timeouts with jittered retries",
            "Enable keep-alive / connection pooling",
        ],
        root_cause_confidence="speculative",
        min_events=2,
    ),
    DetectionRule(
        name="oom_killed",
        display_name="Out of Memory (OOM)",
        severity="CRITICAL",
        patterns=[r"OOMKilled", r"OutOfMemoryError|out of memory", r"Java heap space", r"Cannot allocate memory"],
        confidence=0.9,
        root_cause_template="Process for {service} was killed due to memory exhaustion ({pattern}). Container memory limit may be too low or a leak exists.",
        investigation_steps=[
            "kubectl top pod <pod> and kubectl describe pod",
            "Review heap dumps and GC logs if JVM",
            "Compare memory usage before and after recent deployments",
        ],
        remediation_actions=[
            "Increase container memory limit/request",
            "Investigate and fix memory leak",
            "Restart affected pods to restore service",
        ],
        root_cause_confidence="likely",
    ),
]


def detect_signature(message: str) -> DetectionRule | None:
    """Return the first matching detection rule, or None."""
    for rule in DETECTION_RULES:
        for pat in rule.patterns:
            if re.search(pat, message, re.IGNORECASE):
                return rule
    return None


def signature_for(rule: DetectionRule, service: str, environment: str) -> str:
    """Stable incident signature: rule + service + environment."""
    return f"{rule.name}:{service}:{environment}"


@dataclass
class DetectionResult:
    incidents: list[dict[str, Any]]       # new incidents created
    linked_logs: list[int]                # log event ids that were linked
    total_events_processed: int


def detect_and_correlate(
    db,
    events: list[dict[str, Any]],
    time_window_minutes: int = 15,
) -> DetectionResult:
    """Run detection over a list of normalized log-event dicts.

    Groups related errors into time-bounded clusters keyed by signature. Open
    and acknowledged incidents are considered active. Callers should include a
    ``_log_event_id`` on each event so links are unambiguous and idempotent.
    """
    from app import models

    new_incidents: list[dict[str, Any]] = []
    linked_log_ids: list[int] = []
    affected_service_ids: set[int] = set()
    if time_window_minutes <= 0:
        raise ValueError("time_window_minutes must be positive")
    now = utc_now()
    window = timedelta(minutes=time_window_minutes)

    # Group candidate events by signature
    groups: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        level = (ev.get("level") or "INFO").upper()
        if level not in ("WARN", "WARNING", "ERROR", "FATAL"):
            continue
        rule = detect_signature(ev.get("message", ""))
        if not rule:
            continue
        sig = signature_for(rule, ev.get("service", "unknown"), ev.get("environment", "production"))
        groups.setdefault(sig, []).append({**ev, "_rule": rule})

    signatures = list(groups)
    existing = (
        db.query(models.Incident)
        .filter(
            models.Incident.signature.in_(signatures),
            models.Incident.status.in_(("open", "acknowledged")),
        )
        .order_by(models.Incident.last_seen.desc())
        .all()
        if signatures
        else []
    )
    existing_by_signature: dict[str, list[Any]] = {}
    for incident in existing:
        existing_by_signature.setdefault(incident.signature, []).append(incident)

    for sig, signature_group in groups.items():
        ordered = sorted(signature_group, key=lambda item: item.get("timestamp") or now)
        clusters: list[list[dict[str, Any]]] = []
        for event in ordered:
            event_ts = event.get("timestamp") or now
            if not clusters:
                clusters.append([event])
                continue
            previous_ts = clusters[-1][-1].get("timestamp") or now
            if event_ts - previous_ts > window:
                clusters.append([event])
            else:
                clusters[-1].append(event)

        for group in clusters:
            rule = group[0]["_rule"]
            service = group[0].get("service", "unknown")
            environment = group[0].get("environment", "production")
            timestamps = [g.get("timestamp") for g in group if g.get("timestamp")]
            first_seen = min(timestamps) if timestamps else now
            last_seen = max(timestamps) if timestamps else now
            candidates = existing_by_signature.get(sig, [])
            incident = next(
                (
                    item
                    for item in candidates
                    if item.last_seen >= first_seen - window
                    and item.first_seen <= last_seen + window
                ),
                None,
            )

            log_ids = list(dict.fromkeys(g.get("_log_event_id") for g in group if g.get("_log_event_id")))
            if not log_ids and timestamps:
                # Compatibility for direct engine callers. Ingestion supplies IDs,
                # which is the preferred unambiguous and query-efficient path.
                log_ids = [
                    row[0]
                    for row in db.query(models.LogEvent.id)
                    .filter(
                        models.LogEvent.service == service,
                        models.LogEvent.environment == environment,
                        models.LogEvent.timestamp.in_(timestamps),
                    )
                    .all()
                ]
            if incident:
                linked_already = {
                    row[0]
                    for row in db.query(models.IncidentEvent.log_event_id)
                    .filter(
                        models.IncidentEvent.incident_id == incident.id,
                        models.IncidentEvent.log_event_id.in_(log_ids),
                    )
                    .all()
                } if log_ids else set()
                new_log_ids = [log_id for log_id in log_ids if log_id not in linked_already]
                for log_id in new_log_ids:
                    db.add(models.IncidentEvent(incident_id=incident.id, log_event_id=log_id))
                if new_log_ids:
                    incident.event_count = (incident.event_count or 0) + len(new_log_ids)
                    incident.first_seen = min(incident.first_seen, first_seen)
                    incident.last_seen = max(incident.last_seen, last_seen)
                    linked_log_ids.extend(new_log_ids)
                continue

            if len(log_ids) < rule.min_events:
                unlinked_evidence = (
                    db.query(models.LogEvent)
                    .outerjoin(
                        models.IncidentEvent,
                        models.IncidentEvent.log_event_id == models.LogEvent.id,
                    )
                    .filter(
                        models.IncidentEvent.id.is_(None),
                        models.LogEvent.service == service,
                        models.LogEvent.environment == environment,
                        models.LogEvent.level.in_(("WARN", "ERROR", "FATAL")),
                        models.LogEvent.timestamp >= first_seen - window,
                        models.LogEvent.timestamp <= last_seen + window,
                    )
                    .order_by(models.LogEvent.timestamp.desc())
                    .limit(1_000)
                    .all()
                )
                matching_evidence = [
                    log
                    for log in unlinked_evidence
                    if (matched_rule := detect_signature(log.message))
                    and signature_for(matched_rule, service, environment) == sig
                ]
                log_ids = list(dict.fromkeys([*log_ids, *(log.id for log in matching_evidence)]))
                if matching_evidence:
                    evidence_timestamps = [log.timestamp for log in matching_evidence]
                    first_seen = min(first_seen, *evidence_timestamps)
                    last_seen = max(last_seen, *evidence_timestamps)

            if len(log_ids) < rule.min_events:
                continue

            root_cause = rule.root_cause_template.format(
                service=service, pattern=group[0].get("message", "")[:80]
            )
            service_id = group[0].get("_service_id")
            if service_id is None:
                service_row = (
                    db.query(models.Service.id)
                    .filter(
                        models.Service.name == service,
                        models.Service.environment == environment,
                    )
                    .first()
                )
                service_id = service_row[0] if service_row else None
            incident = models.Incident(
                title=f"{rule.display_name} — {service}",
                severity=rule.severity,
                status="open",
                service_id=service_id,
                service=service,
                environment=environment,
                signature=sig,
                first_seen=first_seen,
                last_seen=last_seen,
                event_count=len(log_ids) if log_ids else len(group),
                confidence=rule.confidence,
                root_cause=f"Potential cause: {root_cause}",
                root_cause_confidence=rule.root_cause_confidence,
                suggested_steps="\n".join(rule.investigation_steps),
                suggested_remediation="\n".join(rule.remediation_actions),
            )
            db.add(incident)
            db.flush()
            existing_by_signature.setdefault(sig, []).append(incident)
            for log_id in log_ids:
                db.add(models.IncidentEvent(incident_id=incident.id, log_event_id=log_id))
            linked_log_ids.extend(log_ids)
            new_incidents.append(
                {
                    "id": incident.id,
                    "title": incident.title,
                    "severity": incident.severity,
                    "service": incident.service,
                    "signature": incident.signature,
                    "event_count": incident.event_count,
                    "confidence": incident.confidence,
                    "root_cause": incident.root_cause,
                    "root_cause_confidence": incident.root_cause_confidence,
                }
            )

            if incident.service_id:
                affected_service_ids.add(incident.service_id)

    for service_id in affected_service_ids:
        recompute_service_status(db, service_id)
    db.flush()
    return DetectionResult(
        incidents=new_incidents,
        linked_logs=linked_log_ids,
        total_events_processed=len(events),
    )


def recompute_service_status(db, service_id: int | None) -> None:
    """Set service health from its highest-severity active incident."""
    if service_id is None:
        return
    from app import models

    severities = {
        row[0]
        for row in db.query(models.Incident.severity)
        .filter(
            models.Incident.service_id == service_id,
            models.Incident.status.in_(("open", "acknowledged")),
        )
        .all()
    }
    service = db.get(models.Service, service_id)
    if service:
        service.status = (
            "critical" if "CRITICAL" in severities else "warning" if "WARNING" in severities else "healthy"
        )
