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

  return <aside className="flex max-h-[420px] min-h-[300px] w-full flex-col border-t border-fennec-dark-700 md:max-h-none md:w-[300px] md:min-w-[300px] md:border-l md:border-t-0">
    <h3 className="border-b border-fennec-dark-700 p-4 text-sm font-semibold text-fennec-dark-200">Converse com a IA sobre esta falha</h3>
    <div className="flex-1 space-y-3 overflow-y-auto p-4">
      {!messages.length && suggestions.map(s => <button key={s} onClick={() => send(s)} className="block w-full rounded border border-fennec-dark-700 p-2 text-left text-xs text-fennec-dark-300 hover:bg-fennec-dark-800">{s}</button>)}
      {messages.map((m, i) => <div key={i} className={`whitespace-pre-wrap rounded p-3 text-sm ${m.role === 'user' ? 'bg-fennec-purple-500/20 text-fennec-dark-100' : 'bg-fennec-dark-800 text-fennec-dark-200'}`}>{m.content}</div>)}
      {busy && <p className="text-xs text-fennec-dark-400">A IA está respondendo…</p>}
      {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
    </div>
    <form className="flex gap-2 border-t border-fennec-dark-700 p-3" onSubmit={e => { e.preventDefault(); send(draft); }}>
      <input aria-label="Pergunta sobre a falha" value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} placeholder="Pergunte sobre a falha" className="min-w-0 flex-1 rounded bg-fennec-dark-800 px-2 py-2 text-sm text-fennec-dark-100" />
      <button disabled={busy || !draft.trim() || messages.length >= 19} className="rounded bg-fennec-purple-600 px-3 text-sm text-white disabled:opacity-50">Enviar</button>
    </form>
  </aside>;
}
