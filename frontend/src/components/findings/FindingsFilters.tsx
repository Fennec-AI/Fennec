import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import type { FindingFacets } from '@/types';
import { severityClass } from './severity';

interface Props {
  facets: FindingFacets;
  values: Record<string, string>;
  update: (key: string, value: string) => void;
}

const selectClass = 'rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground';

export default function FindingsFilters({ facets, values, update }: Props) {
  return <div className="shrink-0 space-y-3 border-b border-border p-4">
    {values.target_id && <button className="rounded border border-fennec-purple-500 px-3 py-1 text-xs text-foreground" onClick={() => update('target_id', '')}>Alvo selecionado: {values.target_id} ×</button>}
    <div className="flex flex-wrap gap-2">
      <Select value={values.host || '__all__'} onValueChange={value => update('host', value === '__all__' ? '' : value)}>
        <SelectTrigger aria-label="Site" className="w-full bg-card text-foreground sm:w-64"><SelectValue placeholder="Todos os sites" /></SelectTrigger>
        <SelectContent className="max-h-80"><SelectItem value="__all__">Todos os sites</SelectItem>{facets.hosts.map(x => <SelectItem key={x.value} value={x.value}>{x.value} ({x.count})</SelectItem>)}</SelectContent>
      </Select>
      <Select value={values.job_id || '__all__'} onValueChange={value => update('job_id', value === '__all__' ? '' : value)}>
        <SelectTrigger aria-label="Scan" className="w-full bg-card text-foreground sm:w-64"><SelectValue placeholder="Todos os scans" /></SelectTrigger>
        <SelectContent className="max-h-80"><SelectItem value="__all__">Todos os scans</SelectItem>{facets.scans.map(x => <SelectItem key={x.value} value={x.value}>{x.label} ({x.count})</SelectItem>)}</SelectContent>
      </Select>
      <Input aria-label="Buscar falhas" className="min-w-[180px] flex-1 bg-card text-foreground" placeholder="Buscar por título, endpoint, CWE..." value={values.q || ''} onChange={e => update('q', e.target.value)} />
    </div>
    <div className="flex flex-wrap gap-2">
      <button className={`${selectClass} ${!values.severity ? 'border-fennec-purple-500' : ''}`} onClick={() => update('severity', '')}>Todas</button>
      {facets.severities.map(x => <button key={x.value} className={`rounded border px-3 py-2 text-sm capitalize ${severityClass(x.value)} ${values.severity === x.value ? 'ring-2 ring-white/50' : ''}`} onClick={() => update('severity', x.value)}>{x.value} ({x.count})</button>)}
    </div>
  </div>;
}
