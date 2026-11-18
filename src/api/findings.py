"""Build, merge, and filter dashboard findings without losing scan context."""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from .job_store import Job


def host_of(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"//{url}")
    return (parsed.hostname or "").lower()


def build_job_findings(job: Job, rich: list[dict], now: str) -> list[dict]:
    records = []
    for i, item in enumerate(rich):
        breakdown = item.get("description_breakdown") or {}
        title = item.get("title") or f"Finding {i + 1}"
        records.append({
            **item,
            "id": f"{job.id}-finding-{i}",
            "job_id": job.id,
            "title": title,
            "description": item.get("description_overview") or item.get("hypothesis_description") or title,
            "severity": item.get("severity") or "info",
            "status": "confirmed",
            "location": breakdown.get("affected_endpoint") or job.target_url,
            "parameter": item.get("affected_parameter") or breakdown.get("affected_parameter") or "",
            "evidence": "\n".join(item.get("evidence") or []),
            "reproduction_steps": item.get("reproduction_steps") or [],
            "vulnerability_type": breakdown.get("vuln_type") or "",
            "cwe_id": item.get("cwe_id"),
            "hypothesis_id": item.get("hypothesis_id"),
            "discovered_at": now,
            "discovered_by": "pentester",
        })
    return records


def merged_findings(job: Job) -> list[dict]:
    by_hypothesis: dict[str, dict] = {}
    for result in job.pentester_results:
        hid = result.get("hypothesis_id")
        if hid:
            by_hypothesis[hid] = result
    records = []
    for i, basic in enumerate(job.findings):
        hid = basic.get("hypothesis_id")
        rich = by_hypothesis.get(hid) if hid else None
        if rich is None and i < len(job.pentester_results):
            candidate = job.pentester_results[i]
            if not hid or not candidate.get("hypothesis_id"):
                rich = candidate
        rich = rich or {}
        evidence = basic.get("evidence")
        if not isinstance(evidence, list):
            evidence = [evidence] if evidence else []
        records.append({
            **rich,
            **basic,
            "id": str(basic.get("id") or f"{job.id}-finding-{i}"),
            "job_id": job.id,
            "evidence": rich.get("evidence") or evidence,
            "description_overview": rich.get("description_overview") or basic.get("description_overview") or basic.get("description"),
            "description_breakdown": rich.get("description_breakdown") or basic.get("description_breakdown"),
            "reproduction_steps": basic.get("reproduction_steps") or rich.get("reproduction_steps") or [],
            "cwe_id": basic.get("cwe_id") or rich.get("cwe_id"),
            "commands_executed": basic.get("commands_executed") or rich.get("commands_executed") or [],
            "target_id": job.target_id,
            "target_url": job.target_url,
            "host": host_of(job.target_url),
            "job_name": job.name,
            "job_created_at": job.created_at,
        })
    return records


def filter_findings(records: list[dict], severity: str | None = None,
                    target_id: str | None = None, host: str | None = None,
                    job_id: str | None = None, q: str | None = None) -> list[dict]:
    result = []
    for record in records:
        if severity and (record.get("severity") or "").lower() != severity.lower():
            continue
        if target_id and record.get("target_id") != target_id:
            continue
        if host and (record.get("host") or "").lower() != host.lower():
            continue
        if job_id and record.get("job_id") != job_id:
            continue
        if q and q.lower() not in " ".join(str(record.get(k) or "") for k in
                                      ("title", "description", "location", "parameter", "cwe_id", "owasp_category")).lower():
            continue
        result.append(record)
    return result


def facets(records: list[dict]) -> dict:
    hosts = Counter(r.get("host") for r in records if r.get("host"))
    severities = Counter(r.get("severity") for r in records if r.get("severity"))
    jobs = Counter(r.get("job_id") for r in records if r.get("job_id"))
    names = {r["job_id"]: r.get("job_name") or r["job_id"] for r in records if r.get("job_id")}
    return {
        "hosts": [{"value": k, "count": v} for k, v in sorted(hosts.items())],
        "severities": [{"value": k, "count": v} for k, v in sorted(severities.items())],
        "scans": [{"value": k, "label": names[k], "count": v} for k, v in jobs.items()],
    }
