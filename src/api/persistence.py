"""Atomic, opt-in persistence of dashboard state on a mounted data directory."""
import json
import os
from dataclasses import fields
from pathlib import Path

from .job_store import JOBS, TARGETS, CREDENTIALS, Job, TargetRecord, CredentialRecord

_TRANSIENT = {'task', 'subscribers', 'review_queue'}


def _path():
    directory = os.getenv('FENNEC_DATA_DIR')
    return Path(directory) / 'state.json' if directory else None


def _record(obj):
    return {f.name: getattr(obj, f.name) for f in fields(obj) if f.name not in _TRANSIENT}


def save_state():
    path = _path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {'version': 1, 'jobs': [_record(j) for j in JOBS.all()],
            'targets': [_record(t) for t in TARGETS.values()],
            'credentials': [_record(c) for c in CREDENTIALS.values()]}
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8', opener=lambda p, flags: os.open(p, flags, 0o600)) as f:
        json.dump(data, f, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_state():
    path = _path()
    if path is None or not path.exists():
        return
    data = json.loads(path.read_text())
    def build(cls, value):
        names = {f.name for f in fields(cls)} - _TRANSIENT
        return cls(**{k: v for k, v in value.items() if k in names})
    for value in data.get('jobs', []):
        job = build(Job, value)
        if job.status in {'running', 'queued', 'awaiting_review'}:
            job.status = 'failed'
            job.error = 'Execution interrupted by server restart; saved results preserved.'
        JOBS.put(job)
    for key, cls in [('targets', TargetRecord), ('credentials', CredentialRecord)]:
        store = TARGETS if key == 'targets' else CREDENTIALS
        for value in data.get(key, []):
            obj = build(cls, value)
            store[obj.id] = obj
