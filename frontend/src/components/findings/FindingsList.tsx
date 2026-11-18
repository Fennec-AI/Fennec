import { useState } from 'react';
import type { Finding } from '@/types';
import { severityClass } from './severity';

const rank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

interface Props { findings: Finding[]; selectedId: string | null; onSelect: (id: string) => void }

export default function FindingsList({ findings, selectedId, onSelect }: Props) {
  const [grouped, setGrouped] = useState(false);
  const ordered = [...findings].sort((a, b) => (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9));
  const groups = grouped ? [...new Set(ordered.map(f => f.host))] : [''];
  return <aside className="w-full border-r border-fennec-dark-700 md:w-[320px] md:min-w-[320px] overflow-y-auto">
    <label className="flex items-center gap-2 border-b border-fennec-dark-700 p-4 text-sm text-fennec-dark-300">
      <input type="checkbox" checked={grouped} onChange={e => setGrouped(e.target.checked)} /> Agrupar por site
    </label>
    {groups.map(group => <div key={group}>
      {grouped && <h3 className="px-4 py-2 text-xs font-semibold text-fennec-dark-400">{group}</h3>}
      {ordered.filter(f => !grouped || f.host === group).map(f => <button key={f.id} onClick={() => onSelect(f.id)} className={`w-full border-b border-fennec-dark-800 p-4 text-left hover:bg-fennec-dark-800 ${selectedId === f.id ? 'bg-fennec-dark-800' : ''}`}>
        <span className={`inline-flex rounded border px-2 py-0.5 text-xs font-bold uppercase ${severityClass(f.severity)}`}>{f.severity}</span>
        <span className="mt-1 block text-sm font-medium text-fennec-dark-100">{f.title}</span>
        <span className="mt-1 block truncate text-xs text-fennec-dark-400">{f.host} · {f.location}</span>
        <span className="mt-1 block text-xs text-fennec-dark-500">{new Date(f.discovered_at).toLocaleDateString()}</span>
      </button>)}
    </div>)}
  </aside>;
}
