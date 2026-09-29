// Floating help chat backed by the in-house small language model.
// It only answers questions about the platform; decisions (recommendations,
// prices, approvals) are never made by it.
import { useEffect, useRef, useState } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { askAssistant } from '../../services/assistantService';

const SUGGESTIONS = ['How do I sell my phone?', 'How are recommendations decided?', 'How do I recycle a device?'];
const GREETING = {
  from: 'bot',
  text: "Hi! I'm the Circular assistant. Ask me how to repair, sell or recycle a device, or how anything here works.",
};

export default function AssistantChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, busy]);

  async function send(text) {
    const q = text.trim();
    if (!q || busy) return;
    setInput('');
    setMessages((m) => [...m, { from: 'user', text: q }]);
    setBusy(true);
    try {
      const r = await askAssistant(q);
      setMessages((m) => [...m, { from: 'bot', text: r.reply, fallback: r.source !== 'model' }]);
    } catch (err) {
      setMessages((m) => [...m, { from: 'bot', text: err.message, fallback: true }]);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Open the Circular assistant">
        <MessageCircle size={22} />
      </button>
    );
  }

  return (
    <div className="chat-panel" role="dialog" aria-label="Circular assistant">
      <div className="chat-head">
        <div>
          <strong>Circular assistant</strong>
          <span className="chat-sub">Small in-house language model</span>
        </div>
        <button className="icon-btn" onClick={() => setOpen(false)} aria-label="Close"><X size={18} /></button>
      </div>

      <div className="chat-list" ref={listRef} aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.from}${m.fallback ? ' fallback' : ''}`}>{m.text}</div>
        ))}
        {busy && <div className="chat-msg bot typing">Thinking…</div>}
        {messages.length === 1 && (
          <div className="chat-suggest">
            {SUGGESTIONS.map((s) => <button key={s} className="chip" onClick={() => send(s)}>{s}</button>)}
          </div>
        )}
      </div>

      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <input className="input" value={input} onChange={(e) => setInput(e.target.value)}
               placeholder="Ask a question…" maxLength={500} aria-label="Your question" />
        <button className="btn btn-primary" type="submit" disabled={busy || !input.trim()} aria-label="Send">
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
