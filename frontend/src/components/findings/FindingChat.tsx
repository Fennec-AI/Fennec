import { useEffect, useState } from 'react';
import { findingsApi } from '@/services/api';

type Message = { role: 'user' | 'assistant'; content: string };
const suggestions = ['Explique esta falha', 'Como corrigir no meu código?', 'Como confirmo que a correção funcionou?'];

// One-time migration for conversations saved by the older browser-only chat.
function legacyMessages(findingId: string): Message[] {
  try {
    const raw = localStorage.getItem(`fennec:finding-chat:v1:${findingId}`);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is Message =>
      item !== null && typeof item === 'object' &&
      (item.role === 'user' || item.role === 'assistant') &&
      typeof item.content === 'string' && item.content.length > 0 &&
      item.content.length <= (item.role === 'user' ? 4000 : 100000),
    ).slice(-2000);
  } catch {
    return [];
  }
}

export default function FindingChat({ findingId }: { findingId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const old = legacyMessages(findingId);
    const request = old.length ? findingsApi.importChat(findingId, old) : findingsApi.chatHistory(findingId);
    request.then(({ messages: history }) => {
      if (active) setMessages(history);
      if (old.length) {
        try { localStorage.removeItem(`fennec:finding-chat:v1:${findingId}`); } catch { /* imported already */ }
      }
    }).catch(e => {
      if (active) setError(e instanceof Error ? e.message : 'Não foi possível carregar o histórico.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [findingId]);

  async function clear() {
    if (busy || loading) return;
    setBusy(true); setError('');
    try {
      const result = await findingsApi.clearChat(findingId);
      setMessages(result.messages);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível limpar o histórico.');
    } finally { setBusy(false); }
  }

  async function send(content: string) {
    if (!content.trim() || busy || loading) return;
    const question = content.trim();
    setMessages([...messages, { role: 'user', content: question }]);
    setDraft(''); setBusy(true); setError('');
    try {
      const result = await findingsApi.chat(findingId, question);
      setMessages(result.messages);
    } catch (e) {
      setMessages(messages);
      setDraft(question);
      setError(e instanceof Error ? e.message : 'Não foi possível consultar a IA.');
    } finally { setBusy(false); }
  }

  return <aside className="flex max-h-[420px] min-h-[300px] w-full shrink-0 flex-col border-t border-border md:min-h-0 md:max-h-none md:w-[300px] md:min-w-[300px] md:border-l md:border-t-0">
    <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border p-4">
      <h3 className="text-sm font-semibold text-foreground">Converse com a IA sobre esta falha</h3>
      {messages.length > 0 && <button type="button" disabled={busy || loading} onClick={clear} className="text-xs text-muted-foreground hover:text-foreground disabled:opacity-50">Limpar</button>}
    </div>
    <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
      {loading && <p className="text-xs text-muted-foreground">Carregando histórico…</p>}
      {!loading && !error && <p className="text-xs text-muted-foreground">Histórico salvo no servidor.</p>}
      {!loading && !messages.length && suggestions.map(s => <button key={s} disabled={busy} onClick={() => send(s)} className="block w-full rounded border border-border p-2 text-left text-xs text-muted-foreground hover:bg-muted disabled:opacity-50">{s}</button>)}
      {messages.map((m, i) => <div key={i} className={`whitespace-pre-wrap rounded p-3 text-sm ${m.role === 'user' ? 'bg-fennec-purple-500/20 text-foreground' : 'bg-muted text-foreground'}`}>{m.content}</div>)}
      {busy && <p className="text-xs text-muted-foreground">A IA está respondendo…</p>}
      {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
    </div>
    <form className="flex shrink-0 gap-2 border-t border-border p-3" onSubmit={e => { e.preventDefault(); send(draft); }}>
      <input aria-label="Pergunta sobre a falha" value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} placeholder="Pergunte sobre a falha" className="min-w-0 flex-1 rounded bg-muted px-2 py-2 text-sm text-foreground" />
      <button disabled={busy || loading || !draft.trim()} className="rounded bg-fennec-purple-600 px-3 text-sm text-white disabled:opacity-50">Enviar</button>
    </form>
  </aside>;
}
