import { useState } from 'react';
import { findingsApi } from '@/services/api';

type Message = { role: 'user' | 'assistant'; content: string };
const suggestions = ['Explique esta falha', 'Como corrigir no meu código?', 'Como confirmo que a correção funcionou?'];
const storageKey = (findingId: string) => `fennec:finding-chat:v1:${findingId}`;

function loadMessages(findingId: string): { messages: Message[]; error: boolean } {
  try {
    const saved = localStorage.getItem(storageKey(findingId));
    if (!saved) return { messages: [], error: false };
    const parsed: unknown = JSON.parse(saved);
    if (!Array.isArray(parsed)) return { messages: [], error: false };
    return {
      messages: parsed.filter((item): item is Message =>
        item !== null && typeof item === 'object' &&
        (item.role === 'user' || item.role === 'assistant') &&
        typeof item.content === 'string' && item.content.length > 0 &&
        item.content.length <= (item.role === 'user' ? 4000 : 100000),
      ),
      error: false,
    };
  } catch {
    return { messages: [], error: true };
  }
}

export default function FindingChat({ findingId }: { findingId: string }) {
  const [stored] = useState(() => loadMessages(findingId));
  const [messages, setMessages] = useState<Message[]>(stored.messages);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [storageError, setStorageError] = useState(stored.error);

  function save(next: Message[]) {
    setMessages(next);
    try {
      localStorage.setItem(storageKey(findingId), JSON.stringify(next));
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }

  function clear() {
    setMessages([]);
    setError('');
    try {
      localStorage.removeItem(storageKey(findingId));
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }

  async function send(content: string) {
    if (!content.trim() || busy) return;
    const next: Message[] = [...messages, { role: 'user', content: content.trim() }];
    save(next); setDraft(''); setBusy(true); setError('');
    try {
      const { reply } = await findingsApi.chat(findingId, next.slice(-20).map(message => ({
        ...message, content: message.content.slice(0, 4000),
      })));
      save([...next, { role: 'assistant', content: reply }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível consultar a IA.');
    } finally { setBusy(false); }
  }

  return <aside className="flex max-h-[420px] min-h-[300px] w-full shrink-0 flex-col md:min-h-0 border-t border-border md:max-h-none md:w-[300px] md:min-w-[300px] md:border-l md:border-t-0">
    <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border p-4">
      <h3 className="text-sm font-semibold text-foreground">Converse com a IA sobre esta falha</h3>
      {messages.length > 0 && <button type="button" disabled={busy} onClick={clear} className="text-xs text-muted-foreground hover:text-foreground disabled:opacity-50">Limpar</button>}
    </div>
    <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
      {!storageError && <p className="text-xs text-muted-foreground">Histórico salvo neste navegador.</p>}
      {!messages.length && suggestions.map(s => <button key={s} onClick={() => send(s)} className="block w-full rounded border border-border p-2 text-left text-xs text-muted-foreground hover:bg-muted">{s}</button>)}
      {messages.map((m, i) => <div key={i} className={`whitespace-pre-wrap rounded p-3 text-sm ${m.role === 'user' ? 'bg-fennec-purple-500/20 text-foreground' : 'bg-muted text-foreground'}`}>{m.content}</div>)}
      {busy && <p className="text-xs text-muted-foreground">A IA está respondendo…</p>}
      {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
      {storageError && <p role="alert" className="text-xs text-amber-400">Não foi possível salvar o histórico neste navegador.</p>}
    </div>
    <form className="flex shrink-0 gap-2 border-t border-border p-3" onSubmit={e => { e.preventDefault(); send(draft); }}>
      <input aria-label="Pergunta sobre a falha" value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} placeholder="Pergunte sobre a falha" className="min-w-0 flex-1 rounded bg-muted px-2 py-2 text-sm text-foreground" />
      <button disabled={busy || !draft.trim()} className="rounded bg-fennec-purple-600 px-3 text-sm text-white disabled:opacity-50">Enviar</button>
    </form>
  </aside>;
}
