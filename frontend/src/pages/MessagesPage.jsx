import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loader2, Send, MessageSquare, User } from 'lucide-react';
import useAuthStore from '../store/authStore';
import DashboardLayout from '../components/layout/DashboardLayout';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

function cn(...parts) {
  return parts.filter(Boolean).join(' ');
}

function ThreadTitle({ me, thread }) {
  const other = me?.user_type === 'recruiter' ? thread?.developer : thread?.recruiter;
  const name = other?.full_name || other?.email || 'Conversation';
  return (
    <div className="min-w-0">
      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{name}</p>
      <p className="text-xs text-gray-500 truncate">{other?.email || ''}</p>
    </div>
  );
}

export default function MessagesPage() {
  const me = useAuthStore((s) => s.user);
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedThreadId = Number(searchParams.get('thread') || '') || null;

  const [threads, setThreads] = useState([]);
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [threadsError, setThreadsError] = useState('');

  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState('');

  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);

  const Shell = me?.user_type === 'recruiter' ? RecruiterLayout : DashboardLayout;

  const selectedThread = useMemo(
    () => threads.find((t) => t.thread_id === selectedThreadId) || null,
    [threads, selectedThreadId]
  );

  const loadThreads = async () => {
    setThreadsLoading(true);
    setThreadsError('');
    try {
      const { data } = await api.get('/messages/threads/');
      setThreads(data?.threads || []);
    } catch {
      setThreadsError('Could not load conversations.');
    } finally {
      setThreadsLoading(false);
    }
  };

  const loadMessages = async (threadId) => {
    if (!threadId) return;
    setMessagesLoading(true);
    setMessagesError('');
    try {
      const { data } = await api.get(`/messages/threads/${threadId}/messages/`);
      setMessages(data?.messages || []);
      // Backend marks unread as read when opened; refresh badges.
      loadThreads();
    } catch {
      setMessagesError('Could not load messages.');
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  };

  useEffect(() => {
    loadThreads();
  }, []);

  useEffect(() => {
    if (selectedThreadId) loadMessages(selectedThreadId);
    else setMessages([]);
  }, [selectedThreadId]);

  const selectThread = (threadId) => {
    const next = new URLSearchParams(searchParams);
    next.set('thread', String(threadId));
    setSearchParams(next, { replace: true });
  };

  const sendMessage = async () => {
    if (!selectedThreadId) return;
    const body = draft.trim();
    if (!body) return;
    setSending(true);
    setMessagesError('');
    try {
      const { data } = await api.post(`/messages/threads/${selectedThreadId}/send/`, { body });
      setMessages((prev) => [...prev, data]);
      setDraft('');
      loadThreads();
    } catch {
      setMessagesError('Could not send message.');
    } finally {
      setSending(false);
    }
  };

  return (
    <Shell user={me}>
      <div className="max-w-6xl">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Messages</h1>
            <p className="text-sm text-gray-500 mt-1">Your conversations with recruiters and candidates.</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-[360px_1fr] gap-5">
          <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-gray-500" />
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Conversations</p>
            </div>
            {threadsLoading ? (
              <div className="py-14 flex justify-center">
                <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
              </div>
            ) : threadsError ? (
              <div className="p-4 text-sm text-red-600">{threadsError}</div>
            ) : threads.length ? (
              <div className="max-h-[70vh] overflow-y-auto">
                {threads.map((t) => {
                  const active = t.thread_id === selectedThreadId;
                  return (
                    <button
                      key={t.thread_id}
                      type="button"
                      onClick={() => selectThread(t.thread_id)}
                      className={cn(
                        'w-full text-left px-4 py-3 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors',
                        active && 'bg-primary-50 dark:bg-primary-900/20'
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                            <User className="w-4 h-4 text-gray-500" />
                          </div>
                          <ThreadTitle me={me} thread={t} />
                        </div>
                        {!!t.unread_count && (
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary-600 text-white">
                            {t.unread_count}
                          </span>
                        )}
                      </div>
                      {t.last_message?.body && (
                        <p className="text-xs text-gray-500 mt-2 line-clamp-2">{t.last_message.body}</p>
                      )}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="p-6 text-sm text-gray-500">No conversations yet.</div>
            )}
          </section>

          <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden flex flex-col min-h-[520px]">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {selectedThread ? <ThreadTitle me={me} thread={selectedThread} /> : 'Select a conversation'}
              </p>
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
              {messagesLoading ? (
                <div className="py-14 flex justify-center">
                  <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
                </div>
              ) : messagesError ? (
                <div className="text-sm text-red-600">{messagesError}</div>
              ) : !selectedThreadId ? (
                <div className="text-sm text-gray-500">Pick a conversation to view messages.</div>
              ) : messages.length ? (
                <div className="space-y-3">
                  {messages.map((m) => {
                    const mine = m?.sender?.id === me?.id;
                    return (
                      <div key={m.message_id} className={cn('flex', mine ? 'justify-end' : 'justify-start')}>
                        <div
                          className={cn(
                            'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm',
                            mine
                              ? 'bg-primary-600 text-white'
                              : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                          )}
                        >
                          <p className="whitespace-pre-wrap">{m.body}</p>
                          <p className={cn('text-[10px] mt-1', mine ? 'text-white/70' : 'text-gray-500')}>
                            {m.created_at ? new Date(m.created_at).toLocaleString() : ''}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No messages yet.</div>
              )}
            </div>

            <div className="p-3 border-t border-gray-200 dark:border-gray-800">
              <div className="flex items-end gap-2">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={2}
                  disabled={!selectedThreadId || sending}
                  placeholder={selectedThreadId ? 'Write a message…' : 'Select a conversation first'}
                  className="flex-1 resize-none px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 disabled:opacity-60"
                />
                <button
                  type="button"
                  onClick={sendMessage}
                  disabled={!selectedThreadId || sending || !draft.trim()}
                  className="h-11 px-4 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold border-none disabled:opacity-60 flex items-center gap-2"
                >
                  {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Send
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Shell>
  );
}

