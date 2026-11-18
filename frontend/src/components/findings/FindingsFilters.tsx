import type { FindingFacets } from '@/types';
import { severityClass } from './severity';

interface Props {
  facets: FindingFacets;
  values: Record<string, string>;
  update: (key: string, value: string) => void;
}

const selectClass = 'rounded-md border border-fennec-dark-700 bg-fennec-dark-900 px-3 py-2 text-sm text-fennec-dark-200';

export default function FindingsFilters({ facets, values, update }: Props) {
  return <div className="space-y-3 border-b border-fennec-dark-700 p-4">
    {values.target_id && <button className="rounded border border-fennec-purple-500 px-3 py-1 text-xs text-fennec-dark-200" onClick={() => update('target_id', '')}>Alvo selecionado: {values.target_id} ×</button>}
    <div className="flex flex-wrap gap-2">
      <select aria-label="Site" className={selectClass} value={values.host || ''} onChange={e => update('host', e.target.value)}>
        <option value="">Todos os sites</option>
        {facets.hosts.map(x => <option key={x.value} value={x.value}>{x.value} ({x.count})</option>)}
      </select>
      <select aria-label="Scan" className={selectClass} value={values.job_id || ''} onChange={e => update('job_id', e.target.value)}>
        <option value="">Todos os scans</option>
        {facets.scans.map(x => <option key={x.value} value={x.value}>{x.label} ({x.count})</option>)}
      </select>
      <input aria-label="Buscar falhas" className={`${selectClass} min-w-[180px] flex-1`} placeholder="Buscar por título, endpoint, CWE..." value={values.q || ''} onChange={e => update('q', e.target.value)} />
    </div>
    <div className="flex flex-wrap gap-2">
      <button className={`${selectClass} ${!values.severity ? 'border-fennec-purple-500' : ''}`} onClick={() => update('severity', '')}>Todas</button>
      {facets.severities.map(x => <button key={x.value} className={`rounded border px-3 py-2 text-sm capitalize ${severityClass(x.value)} ${values.severity === x.value ? 'ring-2 ring-white/50' : ''}`} onClick={() => update('severity', x.value)}>{x.value} ({x.count})</button>)}
    </div>
  </div>;
}
