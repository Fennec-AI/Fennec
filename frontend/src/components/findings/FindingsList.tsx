import { useState } from 'react';
import type { Finding } from '@/types';

const rank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

interface Props { findings: Finding[]; selectedId: string | null; onSelect: (id: string) => void }

export default function FindingsList({ findings, selectedId, onSelect }: Props) {
  const [grouped, setGrouped] = useState(false);
  const ordered = [...findings].sort((a, b) => (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9));
  const groups = grouped ? [...new Set(ordered.map(f => f.host))] : [''];
  return <aside className="max-h-64 min-h-0 w-full shrink-0 overflow-y-auto border-r border-border md:max-h-none md:w-[320px] md:min-w-[320px]">
    <label className="flex items-center gap-2 border-b border-border p-4 text-sm text-muted-foreground">
      <input type="checkbox" checked={grouped} onChange={e => setGrouped(e.target.checked)} /> Agrupar por site
    </label>
    {groups.map(group => <div key={group}>
      {grouped && <h3 className="px-4 py-2 text-xs font-semibold text-muted-foreground">{group}</h3>}
      {ordered.filter(f => !grouped || f.host === group).map(f => <button key={f.id} onClick={() => onSelect(f.id)} className={`w-full border-b border-border p-4 text-left hover:bg-muted ${selectedId === f.id ? 'bg-muted' : ''}`}>
        <span className="text-xs font-bold uppercase text-fennec-purple-400">{f.severity}</span>
        <span className="mt-1 block text-sm font-medium text-foreground">{f.title}</span>
        <span className="mt-1 block truncate text-xs text-muted-foreground">{f.host} · {f.location}</span>
        <span className="mt-1 block text-xs text-muted-foreground">{new Date(f.discovered_at).toLocaleDateString()}</span>
      </button>)}
    </div>)}
  </aside>;
}
