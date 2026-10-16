# Security Policy

OpsRadar is a local portfolio application and does not currently receive
security fixes under a formal support SLA.

## Reporting

When this project is hosted on GitHub, report suspected vulnerabilities
privately through GitHub's private vulnerability reporting feature when
available. Do not include real credentials, production logs, customer data, or
exploit details in a public issue.

## Security boundary

The default build is intended for a trusted local machine or isolated
development network. It has no authentication, authorization, TLS termination,
multi-tenant isolation, retention enforcement, or immutable audit trail.
Sensitive-value redaction is defense in depth, not a guarantee that arbitrary
secrets cannot appear in stored logs.

Do not expose the application directly to the public internet or ingest
production data without adding the controls appropriate to that environment.
