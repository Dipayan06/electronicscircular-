// Notification bell (Feature 3). Shows the unread count, polls it every 30s,
// and opens a panel with the latest notifications. Clicking one marks it read
// (and jumps to the related listing when there is one).
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCheck } from 'lucide-react';
import { getNotifications, getUnreadCount, markRead, markAllRead } from '../../services/notificationService';
import { timeAgo } from '../../utils/format';

const POLL_MS = 30000;

export default function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const ref = useRef(null);

  const refreshCount = useCallback(() => {
    getUnreadCount().then(setUnread).catch(() => {});
  }, []);

  const loadList = useCallback(() => {
    setError(null);
    getNotifications()
      .then((d) => { setItems(d.items); setUnread(d.unread); })
      .catch((e) => setError(e.message));
  }, []);

  // Poll the unread count (pauses while the tab is hidden).
  useEffect(() => {
    refreshCount();
    const id = setInterval(() => { if (!document.hidden) refreshCount(); }, POLL_MS);
    return () => clearInterval(id);
  }, [refreshCount]);

  // Close on outside click.
  useEffect(() => {
    function onClick(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next) loadList();
  }

  async function openItem(n) {
    if (!n.read) {
      setItems((list) => list.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      setUnread((u) => Math.max(0, u - 1));
      markRead(n.id).catch(() => refreshCount());
    }
    if (n.meta?.listing_id) {
      setOpen(false);
      navigate(`/marketplace/${n.meta.listing_id}`);
    }
  }

  async function readAll() {
    setItems((list) => list?.map((x) => ({ ...x, read: true })));
    setUnread(0);
    markAllRead().catch(() => loadList());
  }

  return (
    <div className="notif" ref={ref}>
      <button className="icon-btn notif-btn" onClick={toggle} aria-label={`Notifications (${unread} unread)`}
              aria-haspopup="true" aria-expanded={open}>
        <Bell size={19} />
        {unread > 0 && <span className="notif-count">{unread > 99 ? '99+' : unread}</span>}
      </button>

      {open && (
        <div className="notif-panel" role="dialog" aria-label="Notifications">
          <div className="notif-head">
            <strong>Notifications</strong>
            {unread > 0 && (
              <button className="link-btn" onClick={readAll}><CheckCheck size={14} /> Mark all read</button>
            )}
          </div>
          <div className="notif-list">
            {error && <p className="notif-empty">{error}</p>}
            {!error && items === null && <p className="notif-empty">Loading…</p>}
            {items?.length === 0 && <p className="notif-empty">You're all caught up.</p>}
            {items?.map((n) => (
              <button key={n.id} className={`notif-item ${n.read ? '' : 'unread'}`} onClick={() => openItem(n)}>
                {!n.read && <span className="notif-dot" aria-label="unread" />}
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span className="notif-title">{n.title}</span>
                  <span className="notif-msg">{n.message}</span>
                  <span className="notif-time">{timeAgo(n.created_at)}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
