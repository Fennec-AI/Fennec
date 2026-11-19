import { Link } from 'react-router-dom';
import type { Finding } from '@/types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { severityClass } from './severity';

function Block({ title, value }: { title: string; value?: string | null }) {
  return value ? <section className="space-y-2"><h3 className="text-sm font-semibold text-foreground">{title}</h3><pre className="whitespace-pre-wrap break-words text-sm text-muted-foreground">{value}</pre></section> : null;
}

export default function FindingDetail({ finding: f, onRetry }: { finding: Finding; onRetry: () => void }) {
  return <div className="min-h-0 min-w-0 shrink-0 p-5 md:flex-1 md:overflow-y-auto">
    <div className="mb-5 space-y-2">
      <h2 className="text-[15px] font-semibold leading-5 tracking-[0.01em] text-foreground">{f.title}</h2>
      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span className={`rounded border px-2 py-1 font-semibold uppercase ${severityClass(f.severity)}`}>{f.severity}</span>
        {[f.host, f.location, f.parameter && `Parâmetro: ${f.parameter}`, f.cwe_id, f.owasp_category].filter(Boolean).map((x, i) => <span key={i} className="rounded border border-border px-2 py-1">{x}</span>)}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Link className="font-mono text-[11px] text-ds-fg-muted hover:text-ds-fg hover:underline" to={`/dashboard/status/${f.job_id}`}>Ver scan: {f.job_name}</Link>
        <button type="button" onClick={onRetry} className="rounded border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted">Refazer</button>
      </div>
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
      <TabsContent value="reproduction" className="space-y-5 py-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Como reproduzir esta falha</h3>
          <p className="mt-1 text-sm text-muted-foreground">Siga os passos na ordem e compare o resultado com a evidência registrada pelo agente.</p>
        </div>
        <section className="rounded border border-border bg-muted/30 p-4 text-sm">
          <h4 className="mb-2 font-semibold text-foreground">Antes de começar</h4>
          <p className="text-muted-foreground">Use um ambiente em que você tem autorização para testar.</p>
          <dl className="mt-3 space-y-1 text-muted-foreground">
            <div><dt className="inline font-medium text-foreground">Site: </dt><dd className="inline">{f.host}</dd></div>
            <div><dt className="inline font-medium text-foreground">Endpoint: </dt><dd className="inline break-all">{f.location}</dd></div>
            {f.parameter && <div><dt className="inline font-medium text-foreground">Parâmetro: </dt><dd className="inline">{f.parameter}</dd></div>}
            {f.description_breakdown?.access_required && <div><dt className="inline font-medium text-foreground">Acesso necessário: </dt><dd className="inline">{f.description_breakdown.access_required}</dd></div>}
          </dl>
        </section>
        {f.reproduction_steps?.length ? <ol className="space-y-3">
          {f.reproduction_steps.map((step, i) => <li key={i} className="rounded border border-border p-4">
            <span className="text-xs font-semibold uppercase text-fennec-purple-400">Passo {i + 1}</span>
            <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">{step.replace(/^\s*\d+[.)]\s*/, '')}</p>
          </li>)}
        </ol> : <p className="text-sm text-muted-foreground">O agente não registrou um passo a passo para esta falha. Consulte a evidência e os comandos abaixo.</p>}
        <Block title="Resultado que confirma a falha" value={f.evidence_observed} />
        {!!f.commands_executed?.length && <section className="space-y-3">
          <h4 className="text-sm font-semibold text-foreground">Comandos usados pelo agente</h4>
          <p className="text-sm text-muted-foreground">Abra um comando para ver os argumentos e a saída registrada.</p>
          {f.commands_executed.map((command, i) => <details key={i} className="rounded border border-border p-3 text-sm text-muted-foreground"><summary className="cursor-pointer">Comando {i + 1}: {String(command.tool_name || command.tool || '')}</summary><button className="mt-2 text-fennec-purple-400" onClick={() => navigator.clipboard.writeText(JSON.stringify(command, null, 2))}>Copiar</button><pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words">{JSON.stringify(command, null, 2)}</pre></details>)}
        </section>}
      </TabsContent>
      <TabsContent value="impact" className="space-y-5 py-4"><Block title="Impacto demonstrado" value={f.impact_demonstrated} /><Block title="Cenários de ataque" value={f.impact_attack_scenarios} /><Block title="Risco de negócio" value={f.impact_business_risk} /></TabsContent>
      <TabsContent value="remediation" className="space-y-5 py-4"><Block title="Mitigação principal" value={f.remediation_primary} /><Block title="Implementação" value={f.remediation_implementation} /><Block title="Endurecimento adicional" value={f.remediation_hardening} /></TabsContent>
    </Tabs>
  </div>;
}
