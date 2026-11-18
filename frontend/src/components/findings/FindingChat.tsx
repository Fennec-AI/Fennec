import { useState } from 'react';
import { findingsApi } from '@/services/api';

type Message = { role: 'user' | 'assistant'; content: string };
const suggestions = ['Explique esta falha', 'Como corrigir no meu código?', 'Como confirmo que a correção funcionou?'];

export default function FindingChat({ findingId }: { findingId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function send(content: string) {
    if (!content.trim() || busy) return;
    const next: Message[] = [...messages, { role: 'user', content: content.trim() }];
    setMessages(next); setDraft(''); setBusy(true); setError('');
    try {
      const { reply } = await findingsApi.chat(findingId, next);
      setMessages([...next, { role: 'assistant', content: reply }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível consultar a IA.');
    } finally { setBusy(false); }
  }

  return <aside className="flex max-h-[420px] min-h-[300px] w-full shrink-0 flex-col md:min-h-0 border-t border-border md:max-h-none md:w-[300px] md:min-w-[300px] md:border-l md:border-t-0">
    <h3 className="shrink-0 border-b border-border p-4 text-sm font-semibold text-foreground">Converse com a IA sobre esta falha</h3>
    <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
      {!messages.length && suggestions.map(s => <button key={s} onClick={() => send(s)} className="block w-full rounded border border-border p-2 text-left text-xs text-muted-foreground hover:bg-muted">{s}</button>)}
      {messages.map((m, i) => <div key={i} className={`whitespace-pre-wrap rounded p-3 text-sm ${m.role === 'user' ? 'bg-fennec-purple-500/20 text-foreground' : 'bg-muted text-foreground'}`}>{m.content}</div>)}
      {busy && <p className="text-xs text-muted-foreground">A IA está respondendo…</p>}
      {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
    </div>
    <form className="flex shrink-0 gap-2 border-t border-border p-3" onSubmit={e => { e.preventDefault(); send(draft); }}>
      <input aria-label="Pergunta sobre a falha" value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} placeholder="Pergunte sobre a falha" className="min-w-0 flex-1 rounded bg-muted px-2 py-2 text-sm text-foreground" />
      <button disabled={busy || !draft.trim() || messages.length >= 19} className="rounded bg-fennec-purple-600 px-3 text-sm text-white disabled:opacity-50">Enviar</button>
    </form>
  </aside>;
}
