import { Link } from 'react-router-dom';
import type { Finding } from '@/types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { severityClass } from './severity';

function Block({ title, value }: { title: string; value?: string | null }) {
  return value ? <section className="space-y-2"><h3 className="text-sm font-semibold text-foreground">{title}</h3><pre className="whitespace-pre-wrap break-words text-sm text-muted-foreground">{value}</pre></section> : null;
}

export default function FindingDetail({ finding: f }: { finding: Finding }) {
  return <div className="min-h-0 min-w-0 shrink-0 p-5 md:flex-1 md:overflow-y-auto">
    <div className="mb-5 space-y-2">
      <h2 className="text-[15px] font-semibold leading-5 tracking-[0.01em] text-foreground">{f.title}</h2>
      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span className={`rounded border px-2 py-1 font-semibold uppercase ${severityClass(f.severity)}`}>{f.severity}</span>
        {[f.host, f.location, f.parameter && `Parâmetro: ${f.parameter}`, f.cwe_id, f.owasp_category].filter(Boolean).map((x, i) => <span key={i} className="rounded border border-border px-2 py-1">{x}</span>)}
      </div>
      <Link className="font-mono text-[11px] text-ds-fg-muted hover:text-ds-fg hover:underline" to={`/dashboard/status/${f.job_id}`}>Ver scan: {f.job_name}</Link>
    </div>
    <Tabs defaultValue="description" key={f.id}>
      <TabsList className="h-auto flex-wrap">
        <TabsTrigger value="description">Descrição</TabsTrigger><TabsTrigger value="evidence">Evidência</TabsTrigger><TabsTrigger value="reproduction">Reprodução</TabsTrigger><TabsTrigger value="impact">Impacto</TabsTrigger><TabsTrigger value="remediation">Remediação</TabsTrigger>
      </TabsList>
      <TabsContent value="description" className="space-y-5 py-4">
        <Block title="Resumo" value={f.description} />
        {f.description_breakdown && <section><h3 className="mb-2 text-sm font-semibold text-foreground">Detalhes</h3><dl className="space-y-1 text-sm">{Object.entries(f.description_breakdown).map(([k, v]) => <div key={k} className="flex gap-3"><dt className="text-muted-foreground">{k}</dt><dd className="text-muted-foreground">{v}</dd></div>)}</dl></section>}
        <Block title="Detalhes técnicos" value={f.description_technical} /><Block title="Hipótese de origem" value={f.hypothesis_description} />
      </TabsContent>
      <TabsContent value="evidence" className="space-y-5 py-4">
        {f.evidence_logged?.map((pair, i) => <section key={i} className="space-y-3 rounded border border-border p-3"><Block title={`Request ${i + 1}`} value={pair.request} /><Block title="Response" value={pair.response} /></section>)}
        {f.evidence?.map((item, i) => <Block key={i} title={`Evidência ${i + 1}`} value={item} />)}
        {f.evidence_payloads?.map((item, i) => <Block key={i} title={`Payload ${i + 1}`} value={item} />)}
        <Block title="Comportamento observado" value={f.evidence_observed} />
        {!f.evidence_logged?.length && !f.evidence?.length && !f.evidence_payloads?.length && !f.evidence_observed && <p className="text-sm text-muted-foreground">Sem evidências registradas.</p>}
      </TabsContent>
      <TabsContent value="reproduction" className="space-y-4 py-4">
        {f.reproduction_steps?.length ? <ol className="list-decimal space-y-2 pl-5 text-sm text-muted-foreground">{f.reproduction_steps.map((step, i) => <li key={i} className="whitespace-pre-wrap">{step}</li>)}</ol> : <p className="text-sm text-muted-foreground">Sem passos registrados.</p>}
        {f.commands_executed?.map((command, i) => <details key={i} className="rounded border border-border p-3 text-sm text-muted-foreground"><summary className="cursor-pointer">Comando {i + 1}: {String(command.tool_name || command.tool || '')}</summary><button className="mt-2 text-fennec-purple-400" onClick={() => navigator.clipboard.writeText(JSON.stringify(command, null, 2))}>Copiar</button><pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words">{JSON.stringify(command, null, 2)}</pre></details>)}
      </TabsContent>
      <TabsContent value="impact" className="space-y-5 py-4"><Block title="Impacto demonstrado" value={f.impact_demonstrated} /><Block title="Cenários de ataque" value={f.impact_attack_scenarios} /><Block title="Risco de negócio" value={f.impact_business_risk} /></TabsContent>
      <TabsContent value="remediation" className="space-y-5 py-4"><Block title="Mitigação principal" value={f.remediation_primary} /><Block title="Implementação" value={f.remediation_implementation} /><Block title="Endurecimento adicional" value={f.remediation_hardening} /></TabsContent>
    </Tabs>
  </div>;
}
