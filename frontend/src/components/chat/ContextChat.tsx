import { useEffect, useState } from 'react';
import { contextChatApi, type ChatMessage } from '@/services/api';

export default function ContextChat({ scope, contextId, title }: {
  scope: 'system' | 'assessment' | 'hypothesis'; contextId: string; title: string;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    setMessages([]);
    contextChatApi.history(scope, contextId)
      .then(result => { if (active) setMessages(result.messages); })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : 'Não foi possível carregar o histórico.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [scope, contextId]);

  async function send() {
    const question = draft.trim();
    if (!question || busy || loading) return;
    const previous = messages;
    setMessages([...previous, { role: 'user', content: question }]);
    setDraft(''); setBusy(true); setError('');
    try {
      const result = await contextChatApi.send(scope, contextId, question);
      setMessages(result.messages);
    } catch (e) {
      setMessages(previous);
      setDraft(question);
      setError(e instanceof Error ? e.message : 'Não foi possível consultar a IA.');
    } finally { setBusy(false); }
  }

  async function clear() {
    if (busy || loading) return;
    setBusy(true); setError('');
    try {
      const result = await contextChatApi.clear(scope, contextId);
      setMessages(result.messages);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível limpar o histórico.');
    } finally { setBusy(false); }
  }

  return <section className="flex min-h-[400px] flex-col rounded-lg border border-border bg-card">
    <div className="flex items-center justify-between border-b border-border p-4">
      <h2 className="text-sm font-semibold">{title}</h2>
      {messages.length > 0 && <button type="button" disabled={busy || loading} onClick={clear} className="text-xs text-muted-foreground hover:text-foreground disabled:opacity-50">Limpar</button>}
    </div>
    <div className="max-h-[55vh] min-h-[260px] flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
      {loading && <p className="text-sm text-muted-foreground">Carregando histórico…</p>}
      {!loading && messages.length === 0 && <p className="text-sm text-muted-foreground">Pergunte à IA sobre os dados deste contexto.</p>}
      {messages.map((message, index) => <div key={index} className={`whitespace-pre-wrap rounded border border-border p-3 text-sm ${message.role === 'user' ? 'ml-8 bg-ds-sunken' : 'mr-8 bg-ds-elevated'}`}>{message.content}</div>)}
      {busy && <p className="text-sm text-muted-foreground">A IA está respondendo…</p>}
      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
    </div>
    <form className="flex gap-2 border-t border-border p-3" onSubmit={e => { e.preventDefault(); void send(); }}>
      <input aria-label={`Pergunta sobre ${title}`} value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} placeholder="Escreva sua pergunta" className="min-w-0 flex-1 rounded bg-muted px-3 py-2 text-sm" />
      <button disabled={busy || loading || !draft.trim()} className="rounded border border-border px-4 text-sm disabled:opacity-50">Enviar</button>
    </form>
  </section>;
}
