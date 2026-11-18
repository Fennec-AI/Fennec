import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import FindingsFilters from '@/components/findings/FindingsFilters';
import FindingsList from '@/components/findings/FindingsList';
import FindingDetail from '@/components/findings/FindingDetail';
import FindingChat from '@/components/findings/FindingChat';
import { findingsApi } from '@/services/api';
import type { Finding, FindingFacets } from '@/types';

const emptyFacets: FindingFacets = { hosts: [], severities: [], scans: [] };
const filterKeys = ['host', 'target_id', 'severity', 'job_id', 'q'];

export default function FindingsPage() {
  const [params, setParams] = useSearchParams();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [facets, setFacets] = useState<FindingFacets>(emptyFacets);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const filters = useMemo(() => Object.fromEntries(filterKeys.map(k => [k, params.get(k) || ''])), [params]);
  const query = params.toString();

  useEffect(() => {
    findingsApi.facets().then(setFacets).catch(() => {});
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    findingsApi.list(Object.fromEntries(filterKeys.filter(k => params.get(k)).map(k => [k, params.get(k)!])))
      .then(data => { if (active) { setFindings(data); setSelectedId(previous => {
        const deep = data.find(f => f.id === params.get('finding_id'));
        const hypothesis = data.find(f => f.job_id === params.get('job_id') && f.hypothesis_id === params.get('hypothesis_id') && !!f.hypothesis_id);
        return deep?.id || hypothesis?.id || (data.some(f => f.id === previous) ? previous : data[0]?.id || null);
      }); } })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : 'Erro ao carregar falhas'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query]);

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    if (key === 'host') next.delete('target_id');
    next.delete('finding_id'); next.delete('hypothesis_id');
    setParams(next);
  }

  const hasFilters = filterKeys.some(k => filters[k]);
  const status = params.get('status') || 'open';
  const visible = findings.filter(f => {
    const value = f.status.toLowerCase();
    if (status === 'resolved') return ['resolved', 'fixed'].includes(value);
    if (status === 'archived') return ['archived', 'dismissed'].includes(value);
    return !['resolved', 'fixed', 'archived', 'dismissed'].includes(value);
  });
  const visibleSelected = visible.find(f => f.id === selectedId) || visible[0];
  return <DashboardLayout>
    <div className="flex min-h-[75vh] flex-col bg-fennec-dark-950">
      <div className="border-b border-fennec-dark-700 p-4"><h1 className="text-xl font-semibold text-fennec-dark-100">Falhas</h1><p className="text-sm text-fennec-dark-400">{visible.length} falha(s) encontradas</p></div>
      <FindingsFilters facets={facets} values={filters} update={update} />
      <div className="flex gap-2 border-b border-fennec-dark-700 px-4 py-2">{(['open', 'resolved', 'archived'] as const).map(tab => <button key={tab} className={`rounded px-3 py-1 text-sm capitalize ${status === tab ? 'bg-fennec-dark-700 text-fennec-dark-100' : 'text-fennec-dark-400'}`} onClick={() => update('status', tab === 'open' ? '' : tab)}>{tab}</button>)}</div>
      {loading ? <p className="p-6 text-sm text-fennec-dark-400">Carregando falhas…</p> : error ? <div className="p-6 text-sm text-red-400">{error}<button className="ml-3 underline" onClick={() => window.location.reload()}>Tentar novamente</button></div> : !visible.length ? <div className="p-6 text-sm text-fennec-dark-400">{hasFilters || status !== 'open' ? 'Nenhuma falha com esses filtros.' : 'Nenhuma falha ainda.'}{(hasFilters || status !== 'open') && <button className="ml-3 text-fennec-purple-400 underline" onClick={() => setParams({})}>Limpar filtros</button>}</div> : <div className="flex min-h-[600px] flex-1 flex-col md:flex-row">
        <FindingsList findings={visible} selectedId={visibleSelected?.id || null} onSelect={setSelectedId} />
        {visibleSelected && <><FindingDetail finding={visibleSelected} /><FindingChat key={visibleSelected.id} findingId={visibleSelected.id} /></>}
      </div>}
    </div>
  </DashboardLayout>;
}
