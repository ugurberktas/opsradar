"""Rule-based incident detection and correlation engine.

No external AI is used. Detection is deterministic and based on regex
signatures, time-window correlation, and severity assignment.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DetectionRule:
    name: str
    display_name: str
    severity: str  # INFO | WARNING | CRITICAL
    patterns: List[str]  # compiled regexes matched against the message
    confidence: float
    root_cause_template: str
    investigation_steps: List[str]
    remediation_actions: List[str]
    root_cause_confidence: str = "speculative"  # speculative | likely | confirmed


# All detection rules. Order matters for first-match assignment.
DETECTION_RULES: List[DetectionRule] = [
    DetectionRule(
        name="k8s_crash_loop",
        display_name="Kubernetes CrashLoopBackOff",
        severity="CRITICAL",
        patterns=[r"CrashLoopBackOff", r"Back.?off.?restarting.?failed.?container", r"OOMKilled"],
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


def detect_signature(message: str) -> Optional[DetectionRule]:
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
    incidents: List[Dict[str, Any]]       # new incidents created
    linked_logs: List[int]                # log event ids that were linked
    total_events_processed: int


def detect_and_correlate(
    db,
    events: List[Dict[str, Any]],
    time_window_minutes: int = 15,
) -> DetectionResult:
    """Run detection over a list of normalized log-event dicts.

    Groups related errors into incidents keyed by signature. Avoids
    duplicate incidents for identical signatures that already exist
    in open status.
    """
    from app import models

    new_incidents: List[Dict[str, Any]] = []
    linked_log_ids: List[int] = []
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=time_window_minutes)

    # Load existing open incidents to avoid duplicates
    existing = (
        db.query(models.Incident)
        .filter(models.Incident.status == "open")
        .all()
    )
    existing_signatures = {inc.signature for inc in existing}

    # Group candidate events by signature
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for ev in events:
        level = (ev.get("level") or "INFO").upper()
        if level not in ("WARN", "WARNING", "ERROR", "FATAL"):
            continue
        rule = detect_signature(ev.get("message", ""))
        if not rule:
            continue
        sig = signature_for(rule, ev.get("service", "unknown"), ev.get("environment", "production"))
        groups.setdefault(sig, []).append({**ev, "_rule": rule})

    for sig, group in groups.items():
        rule = group[0]["_rule"]
        service = group[0].get("service", "unknown")
        environment = group[0].get("environment", "production")
        timestamps = [g.get("timestamp") for g in group if g.get("timestamp")]
        first_seen = min(timestamps) if timestamps else now
        last_seen = max(timestamps) if timestamps else now

        # Deduplicate: if an open incident with this signature exists, just link logs
        if sig in existing_signatures:
            inc = next(i for i in existing if i.signature == sig)
            inc.event_count = (inc.event_count or 0) + len(group)
            inc.last_seen = last_seen
            db.add(inc)
            # link log events
            for g in group:
                le = (
                    db.query(models.LogEvent)
                    .filter(
                        models.LogEvent.service == g.get("service"),
                        models.LogEvent.timestamp == g.get("timestamp"),
                        models.LogEvent.message == g.get("message"),
                    )
                    .first()
                )
                if le and not db.query(models.IncidentEvent).filter(
                    models.IncidentEvent.incident_id == inc.id,
                    models.IncidentEvent.log_event_id == le.id,
                ).first():
                    db.add(models.IncidentEvent(incident_id=inc.id, log_event_id=le.id))
                    linked_log_ids.append(le.id)
            continue

        # Create new incident
        title = f"{rule.display_name} — {service}"
        root_cause = rule.root_cause_template.format(
            service=service, pattern=group[0].get("message", "")[:80]
        )
        incident = models.Incident(
            title=title,
            severity=rule.severity,
            status="open",
            service=service,
            environment=environment,
            signature=sig,
            first_seen=first_seen,
            last_seen=last_seen,
            event_count=len(group),
            confidence=rule.confidence,
            root_cause=root_cause,
            root_cause_confidence=rule.root_cause_confidence,
            suggested_steps="\n".join(rule.investigation_steps),
            suggested_remediation="\n".join(rule.remediation_actions),
        )
        db.add(incident)
        db.flush()  # get id
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
        for g in group:
            le = (
                db.query(models.LogEvent)
                .filter(
                    models.LogEvent.service == g.get("service"),
                    models.LogEvent.timestamp == g.get("timestamp"),
                    models.LogEvent.message == g.get("message"),
                )
                .first()
            )
            if le:
                db.add(models.IncidentEvent(incident_id=incident.id, log_event_id=le.id))
                linked_log_ids.append(le.id)

    db.commit()
    return DetectionResult(
        incidents=new_incidents,
        linked_logs=linked_log_ids,
        total_events_processed=len(events),
    )
