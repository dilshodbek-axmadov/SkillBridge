import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Send, Loader2, Plus, MessageSquare, X, Menu,
  GraduationCap, Target, Briefcase, HelpCircle,
  Bot, User as UserIcon, TrendingUp, DollarSign,
  BookOpen, Map, BarChart3, ChevronRight, Info,
  ExternalLink, ArrowRight,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ═══════════════════════════════════════════
   Constants
   ═══════════════════════════════════════════ */

const CONTEXT_TYPES = [
  { key: 'onboarding', labelKey: 'chatbot.context.onboarding', icon: GraduationCap, emoji: '🎓', color: 'text-purple-600', bg: 'bg-purple-50', activeBg: 'bg-purple-600' },
  { key: 'roadmap',    labelKey: 'chatbot.context.roadmap',    icon: Target,        emoji: '🎯', color: 'text-blue-600',   bg: 'bg-blue-50',   activeBg: 'bg-blue-600' },
  { key: 'career',     labelKey: 'chatbot.context.career',     icon: Briefcase,     emoji: '💼', color: 'text-emerald-600',bg: 'bg-emerald-50', activeBg: 'bg-emerald-600' },
  { key: 'help',       labelKey: 'chatbot.context.help',       icon: HelpCircle,    emoji: '❓', color: 'text-orange-600', bg: 'bg-orange-50',  activeBg: 'bg-orange-600' },
];

const INTENT_BADGES = {
  skill_inquiry:    { labelKey: 'chatbot.intent.skill_inquiry',    color: 'bg-blue-100 text-blue-700',    icon: Target },
  salary_inquiry:   { labelKey: 'chatbot.intent.salary_inquiry',   color: 'bg-emerald-100 text-emerald-700', icon: DollarSign },
  job_inquiry:      { labelKey: 'chatbot.intent.job_inquiry',      color: 'bg-purple-100 text-purple-700', icon: Briefcase },
  resource_inquiry: { labelKey: 'chatbot.intent.resource_inquiry', color: 'bg-orange-100 text-orange-700', icon: BookOpen },
  roadmap_inquiry:  { labelKey: 'chatbot.intent.roadmap_inquiry',  color: 'bg-teal-100 text-teal-700',    icon: Map },
  trend_inquiry:    { labelKey: 'chatbot.intent.trend_inquiry',    color: 'bg-red-100 text-red-700',      icon: TrendingUp },
};

const SUGGESTIONS = {
  onboarding: ['chatbot.suggestions.onboarding.1', 'chatbot.suggestions.onboarding.2', 'chatbot.suggestions.onboarding.3'],
  roadmap:    ['chatbot.suggestions.roadmap.1', 'chatbot.suggestions.roadmap.2', 'chatbot.suggestions.roadmap.3'],
  career:     ['chatbot.suggestions.career.1', 'chatbot.suggestions.career.2', 'chatbot.suggestions.career.3'],
  help:       ['chatbot.suggestions.help.1', 'chatbot.suggestions.help.2', 'chatbot.suggestions.help.3'],
};

const WELCOME = {
  onboarding: { titleKey: 'chatbot.welcome.onboarding.title', subKey: 'chatbot.welcome.onboarding.sub' },
  roadmap:    { titleKey: 'chatbot.welcome.roadmap.title',    subKey: 'chatbot.welcome.roadmap.sub' },
  career:     { titleKey: 'chatbot.welcome.career.title',     subKey: 'chatbot.welcome.career.sub' },
  help:       { titleKey: 'chatbot.welcome.help.title',       subKey: 'chatbot.welcome.help.sub' },
};

const LOADING_MESSAGES = {
  skill_inquiry:    'chatbot.loading.skill_inquiry',
  salary_inquiry:   'chatbot.loading.salary_inquiry',
  job_inquiry:      'chatbot.loading.job_inquiry',
  resource_inquiry: 'chatbot.loading.resource_inquiry',
  roadmap_inquiry:  'chatbot.loading.roadmap_inquiry',
  trend_inquiry:    'chatbot.loading.trend_inquiry',
  general:          'chatbot.loading.general',
};

/* ═══════════════════════════════════════════
   Main Page
   ═══════════════════════════════════════════ */

export default function ChatbotPage() {
  const { user } = useAuthStore();
  const { i18n, t } = useTranslation();

  // Conversation state
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [contextType, setContextType] = useState('help');

  // UI state
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showInfo, setShowInfo] = useState(null); // message_id for info popup

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* ─── Load conversations ────────────── */
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setLoadingConvs(true);
    try {
      const { data } = await api.get('/chatbot/conversations/', { params: { limit: 30 } });
      setConversations(data.conversations || []);
    } catch (err) {
      if (err.response?.status === 401) {
        window.location.href = '/login?redirect=/chat';
        return;
      }
    } finally {
      setLoadingConvs(false);
    }
  };

  /* ─── Load conversation history ─────── */
  const loadHistory = async (convId) => {
    try {
      const { data } = await api.get(`/chatbot/conversations/${convId}/history/`);
      setActiveConv(data);
      setContextType(data.context_type || 'help');
      setMessages(
        (data.messages || []).map((m) => ({
          id: m.message_id,
          sender: m.sender,
          text: m.text,
          timestamp: m.timestamp,
          context: m.context,
        }))
      );
      setSidebarOpen(false);
    } catch {
      // ignore
    }
  };

  /* ─── Start new conversation ────────── */
  const startNewConversation = async (type) => {
    setContextType(type || contextType);
    try {
      const { data } = await api.post('/chatbot/conversations/start/', {
        context_type: type || contextType,
        language: i18n.language || 'en',
      });
      setActiveConv({
        conversation_id: data.conversation_id,
        context_type: data.context_type,
        is_active: true,
        started_at: data.started_at,
      });
      setMessages([
        {
          id: Date.now(),
          sender: 'bot',
          text: data.greeting,
          timestamp: new Date().toISOString(),
          context: { response_type: 'greeting', context_type: data.context_type },
        },
      ]);
      setSidebarOpen(false);
      loadConversations();
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch {
      // ignore
    }
  };

  /* ─── Send message ──────────────────── */
  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    // If no active conversation, start one first
    if (!activeConv) {
      await startNewConversation(contextType);
      // Wait for state to update, then send
      return;
    }

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const { data } = await api.post(
        `/chatbot/conversations/${activeConv.conversation_id}/message/`,
        { message: text, language: i18n.language || 'en' }
      );

      if (data.success) {
        const botMsg = {
          id: data.message_id,
          sender: 'bot',
          text: data.response,
          timestamp: data.timestamp,
          context: data.context_data,
        };
        setMessages((prev) => [...prev, botMsg]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: t('chatbot.error.sendFailed'),
          timestamp: new Date().toISOString(),
          context: { response_type: 'error' },
        },
      ]);
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  /* ─── Handle suggestion click ───────── */
  const handleSuggestion = (text) => {
    setInput(text);
    setTimeout(() => {
      sendMessageWithText(text);
    }, 50);
  };

  const sendMessageWithText = async (text) => {
    if (!text || sending) return;

    if (!activeConv) {
      await startNewConversation(contextType);
      return;
    }

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const { data } = await api.post(
        `/chatbot/conversations/${activeConv.conversation_id}/message/`,
        { message: text, language: i18n.language || 'en' }
      );

      if (data.success) {
        setMessages((prev) => [
          ...prev,
          {
            id: data.message_id,
            sender: 'bot',
            text: data.response,
            timestamp: data.timestamp,
            context: data.context_data,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: t('chatbot.error.sendFailed'),
          timestamp: new Date().toISOString(),
          context: { response_type: 'error' },
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  /* ─── Switch context type ───────────── */
  const handleContextSwitch = (type) => {
    setContextType(type);
    if (!activeConv || messages.length <= 1) {
      startNewConversation(type);
    }
  };

  /* ─── Auto-scroll ───────────────────── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  /* ─── Key handler ───────────────────── */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ─── Render ────────────────────────── */
  return (
    <DashboardLayout user={user}>
      <div className="flex h-[calc(100vh-100px)] bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
        {/* Sidebar */}
        <ConversationSidebar
          conversations={conversations}
          activeConvId={activeConv?.conversation_id}
          loading={loadingConvs}
          isOpen={sidebarOpen}
          onSelect={loadHistory}
          onNew={() => startNewConversation('help')}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 bg-transparent border-none cursor-pointer"
            >
              <Menu className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>

            <div className="flex-1 flex items-center gap-2 overflow-x-auto scrollbar-hide">
              {CONTEXT_TYPES.map((ct) => (
                <button
                  key={ct.key}
                  onClick={() => handleContextSwitch(ct.key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap border-none cursor-pointer transition-all ${
                    contextType === ct.key
                      ? `${ct.activeBg} text-white`
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  <span>{ct.emoji}</span>
                  {t(ct.labelKey)}
                </button>
              ))}
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
            {messages.length === 0 ? (
              <WelcomeScreen
                contextType={contextType}
                suggestions={SUGGESTIONS[contextType]}
                onSuggestion={handleSuggestion}
              />
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    message={msg}
                    showInfo={showInfo === msg.id}
                    onToggleInfo={() => setShowInfo(showInfo === msg.id ? null : msg.id)}
                  />
                ))}

                {/* Typing indicator */}
                {sending && <TypingIndicator contextType={contextType} lastIntent={messages[messages.length - 1]?.context?.intent} />}

                {/* Smart suggestions after last bot message */}
                {!sending && messages.length > 0 && messages[messages.length - 1]?.sender === 'bot' && (
                  <SmartSuggestions
                    contextType={contextType}
                    onSuggestion={handleSuggestion}
                  />
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800">
            <div className="flex items-end gap-2 max-w-3xl mx-auto">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('chatbot.input.placeholder')}
                rows={1}
                className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 resize-none focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all max-h-32"
                style={{ minHeight: 42 }}
                disabled={sending}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || sending}
                className="p-2.5 rounded-xl bg-primary-600 text-white border-none cursor-pointer hover:bg-primary-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
              >
                {sending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

/* ═══════════════════════════════════════════
   Conversation Sidebar
   ═══════════════════════════════════════════ */

function ConversationSidebar({ conversations, activeConvId, loading, isOpen, onSelect, onNew, onClose }) {
  const { t } = useTranslation();
  const grouped = groupConversations(conversations);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 z-40 lg:hidden" onClick={onClose} />
      )}

      <div className={`
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
        fixed lg:relative z-50 lg:z-auto
        w-72 h-full bg-gray-50 dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800
        flex flex-col transition-transform duration-200
      `}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">{t('chatbot.sidebar.title')}</h3>
          <div className="flex items-center gap-1">
            <button
              onClick={onNew}
              className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 bg-transparent border-none cursor-pointer"
              title={t('chatbot.sidebar.newConversation')}
            >
              <Plus className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 bg-transparent border-none cursor-pointer lg:hidden"
            >
              <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto py-2">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 px-4">
              <MessageSquare className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-xs text-gray-400 dark:text-gray-500">{t('chatbot.sidebar.empty')}</p>
            </div>
          ) : (
            Object.entries(grouped).map(([group, convs]) =>
              convs.length > 0 && (
                <div key={group}>
                  <div className="px-4 py-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                    {t(`chatbot.groups.${group.toLowerCase().replace(/\s+/g, '_')}`, { defaultValue: group })}
                  </div>
                  {convs.map((conv) => {
                    const ct = CONTEXT_TYPES.find((c) => c.key === conv.context_type) || CONTEXT_TYPES[3];
                    return (
                      <button
                        key={conv.conversation_id}
                        onClick={() => onSelect(conv.conversation_id)}
                        className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left border-none cursor-pointer transition-colors ${
                          activeConvId === conv.conversation_id
                            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                            : 'bg-transparent text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                      >
                        <span className="text-base flex-shrink-0">{ct.emoji}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium truncate">{t(ct.labelKey)}</div>
                          <div className="text-[10px] text-gray-400 dark:text-gray-500">
                            {t('chatbot.sidebar.messagesCount', { count: conv.message_count })}
                          </div>
                        </div>
                        {conv.is_active && (
                          <span className="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )
            )
          )}
        </div>
      </div>
    </>
  );
}

/* ═══════════════════════════════════════════
   Welcome Screen
   ═══════════════════════════════════════════ */

function WelcomeScreen({ contextType, suggestions, onSuggestion }) {
  const { t } = useTranslation();
  const welcome = WELCOME[contextType] || WELCOME.help;
  const ct = CONTEXT_TYPES.find((c) => c.key === contextType) || CONTEXT_TYPES[3];

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center px-4">
      <div className={`w-16 h-16 ${ct.bg} rounded-2xl flex items-center justify-center mb-5`}>
        <span className="text-3xl">{ct.emoji}</span>
      </div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">{t(welcome.titleKey)}</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">{t(welcome.subKey)}</p>

      <div className="flex flex-wrap justify-center gap-2">
        {(suggestions || []).map((s) => (
          <button
            key={s}
            onClick={() => onSuggestion(t(s))}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-700 dark:text-gray-200 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-200 dark:hover:border-primary-800 hover:text-primary-700 dark:hover:text-primary-300 cursor-pointer transition-all"
          >
            {t(s)}
            <ArrowRight className="w-3.5 h-3.5 opacity-50" />
          </button>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Chat Message
   ═══════════════════════════════════════════ */

function ChatMessage({ message, showInfo, onToggleInfo }) {
  const { t } = useTranslation();
  const isUser = message.sender === 'user';
  const intent = message.context?.intent || message.context?.response_type;
  const badge = !isUser && intent ? INTENT_BADGES[intent] : null;

  return (
    <div className={`flex gap-2.5 max-w-3xl mx-auto ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-primary-600' : 'bg-purple-100'
      }`}>
        {isUser ? (
          <UserIcon className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-purple-600" />
        )}
      </div>

      {/* Bubble */}
      <div className={`flex flex-col max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Intent badge */}
        {badge && (
          <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full mb-1 ${badge.color}`}>
            <badge.icon className="w-3 h-3" />
            {t(badge.labelKey)}
          </span>
        )}

        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? 'bg-primary-600 text-white rounded-tr-md'
              : message.context?.response_type === 'error'
                ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-800 rounded-tl-md'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-tl-md'
          }`}
        >
          {message.text}
        </div>

        {/* Rich data cards */}
        {!isUser && message.context && (
          <RichDataCards context={message.context} />
        )}

        {/* Timestamp + Info */}
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            {formatTime(message.timestamp)}
          </span>
          {!isUser && message.context?.intent && (
            <div className="relative">
              <button
                onClick={onToggleInfo}
                className="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 bg-transparent border-none cursor-pointer"
              >
                <Info className="w-3 h-3 text-gray-300 hover:text-gray-500 dark:text-gray-400" />
              </button>
              {showInfo && (
                <div className="absolute bottom-6 left-0 w-56 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg p-3 z-30 text-xs">
                  <div className="font-semibold text-gray-700 dark:text-gray-300 mb-1.5">{t('chatbot.message.responseInfo')}</div>
                  <div className="space-y-1 text-gray-500 dark:text-gray-400 dark:text-gray-500">
                    <div>{t('chatbot.message.intent')}: <span className="text-gray-700 dark:text-gray-200">{message.context.intent}</span></div>
                    <div>{t('chatbot.message.type')}: <span className="text-gray-700 dark:text-gray-200">{message.context.response_type}</span></div>
                    {message.context.context_used && (
                      <div>{t('chatbot.message.context')}: <span className="text-gray-700 dark:text-gray-200">{message.context.context_used.join(', ')}</span></div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Rich Data Cards
   ═══════════════════════════════════════════ */

function RichDataCards({ context }) {
  const type = context?.response_type || context?.intent;
  if (!type) return null;

  // Skill market data card
  if ((type === 'skill_inquiry' || type === 'trend_inquiry') && context.market_data?.top_skills) {
    return <SkillMarketCard skills={context.market_data.top_skills} />;
  }

  // Salary card
  if (type === 'salary_inquiry' && context.market_data?.salaries) {
    return <SalaryCard salaries={context.market_data.salaries} />;
  }

  // Job market card
  if (type === 'job_inquiry' && context.job_data) {
    return <JobMarketCard data={context.job_data} />;
  }

  // Resources card
  if (type === 'resource_inquiry' && context.resources?.length > 0) {
    return <ResourcesCard resources={context.resources} />;
  }

  // Roadmap card
  if (type === 'roadmap_inquiry' && context.roadmap) {
    return <RoadmapCard roadmap={context.roadmap} />;
  }

  return null;
}

function SkillMarketCard({ skills }) {
  const { t } = useTranslation();
  return (
    <div className="mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 w-full max-w-sm">
      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-3 flex items-center gap-1.5">
        <TrendingUp className="w-3.5 h-3.5 text-blue-500" />
        {t('chatbot.cards.skills.title')}
      </h4>
      <div className="space-y-2.5">
        {skills.slice(0, 5).map((s, i) => (
          <div key={i}>
            <div className="flex items-center justify-between text-xs mb-0.5">
              <span className="font-medium text-gray-800 dark:text-gray-100">{s.name}</span>
              <span className="text-gray-400 dark:text-gray-500">{t('chatbot.cards.skills.jobsCount', { count: s.job_count })}</span>
            </div>
            <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all"
                style={{ width: `${Math.min(s.demand_score || 0, 100)}%` }}
              />
            </div>
            {s.growth_rate != null && (
              <span className={`text-[10px] ${s.growth_rate >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                {s.growth_rate >= 0 ? '+' : ''}{s.growth_rate}%
              </span>
            )}
          </div>
        ))}
      </div>
      <Link to="/market-analytics" className="flex items-center gap-1 text-xs text-primary-600 font-medium mt-3 no-underline hover:underline">
        {t('chatbot.cards.skills.cta')} <ExternalLink className="w-3 h-3" />
      </Link>
    </div>
  );
}

function SalaryCard({ salaries }) {
  const { t } = useTranslation();
  return (
    <div className="mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 w-full max-w-sm">
      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-3 flex items-center gap-1.5">
        <DollarSign className="w-3.5 h-3.5 text-emerald-500" />
        {t('chatbot.cards.salary.title')}
      </h4>
      <div className="space-y-2">
        {salaries.slice(0, 5).map((s, i) => (
          <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-gray-50 dark:border-gray-800 last:border-0">
            <span className="font-medium text-gray-800 dark:text-gray-100 truncate flex-1 mr-2">{s.job_title}</span>
            <span className="text-emerald-600 font-semibold whitespace-nowrap">
              {s.salary_avg ? formatSalary(s.salary_avg, t) : t('chatbot.na')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function JobMarketCard({ data }) {
  const { t } = useTranslation();
  return (
    <div className="mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 w-full max-w-sm">
      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-3 flex items-center gap-1.5">
        <Briefcase className="w-3.5 h-3.5 text-purple-500" />
        {t('chatbot.cards.jobs.title')}
      </h4>
      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">
        {(data.total_active_jobs || 0).toLocaleString()}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">{t('chatbot.cards.jobs.activePostings')}</div>
      {data.top_categories?.length > 0 && (
        <div className="space-y-1.5 mb-3">
          {data.top_categories.slice(0, 4).map((c, i) => (
            <div key={i} className="flex items-center justify-between text-xs">
              <span className="text-gray-600 dark:text-gray-300">{c.category}</span>
              <span className="font-medium text-gray-800 dark:text-gray-100">{c.count}</span>
            </div>
          ))}
        </div>
      )}
      {data.remote_jobs > 0 && (
        <span className="inline-flex text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
          {t('chatbot.cards.jobs.remoteCount', { count: data.remote_jobs })}
        </span>
      )}
      <Link to="/jobs" className="flex items-center gap-1 text-xs text-primary-600 font-medium mt-3 no-underline hover:underline">
        {t('chatbot.cards.jobs.cta')} <ExternalLink className="w-3 h-3" />
      </Link>
    </div>
  );
}

function ResourcesCard({ resources }) {
  const { t } = useTranslation();
  const typeIcons = { video: '🎬', book: '📖', tutorial: '📝', course: '🎓', documentation: '📄' };

  return (
    <div className="mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 w-full max-w-sm">
      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-3 flex items-center gap-1.5">
        <BookOpen className="w-3.5 h-3.5 text-orange-500" />
        {t('chatbot.cards.resources.title')}
      </h4>
      <div className="space-y-2.5">
        {resources.slice(0, 4).map((r, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-sm mt-0.5">{typeIcons[r.type] || '📄'}</span>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-gray-800 dark:text-gray-100 truncate">{r.title}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                {r.platform && <span className="text-[10px] bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-300 px-1.5 py-0.5 rounded">{r.platform}</span>}
                <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{r.skill}</span>
              </div>
            </div>
            {r.url && (
              <a href={r.url} target="_blank" rel="noopener noreferrer" className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded flex-shrink-0">
                <ExternalLink className="w-3 h-3 text-gray-400 dark:text-gray-500" />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function RoadmapCard({ roadmap }) {
  const { t } = useTranslation();
  return (
    <div className="mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 w-full max-w-sm">
      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2 flex items-center gap-1.5">
        <Map className="w-3.5 h-3.5 text-teal-500" />
        {t('chatbot.cards.roadmap.title')}
      </h4>
      {roadmap.target_role && (
        <span className="inline-flex text-[10px] bg-teal-50 text-teal-700 px-2 py-0.5 rounded-full font-medium mb-2">
          {roadmap.target_role}
        </span>
      )}
      <div className="flex items-center gap-3 mb-3">
        {/* Mini circular progress */}
        <svg width="40" height="40" className="flex-shrink-0">
          <circle cx="20" cy="20" r="16" fill="none" stroke="#e5e7eb" strokeWidth="4" />
          <circle
            cx="20" cy="20" r="16" fill="none" stroke="#14b8a6" strokeWidth="4"
            strokeDasharray={`${(roadmap.percentage || 0) * 1.005} 100.5`}
            strokeLinecap="round"
            transform="rotate(-90 20 20)"
          />
          <text x="20" y="24" textAnchor="middle" className="text-[9px] font-bold fill-gray-700 dark:fill-gray-200">
            {Math.round(roadmap.percentage || 0)}%
          </text>
        </svg>
        <div>
          <div className="text-sm font-semibold text-gray-800 dark:text-gray-100">{roadmap.completion}</div>
          <div className="text-[10px] text-gray-500 dark:text-gray-400 dark:text-gray-500">{t('chatbot.cards.roadmap.skillsCompleted')}</div>
        </div>
      </div>
      {roadmap.next_skills?.length > 0 && (
        <div>
          <div className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 mb-1">{t('chatbot.cards.roadmap.nextSkills')}</div>
          <div className="flex flex-wrap gap-1">
            {roadmap.next_skills.map((s, i) => (
              <span key={i} className="text-[10px] bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 px-2 py-0.5 rounded-full">{s}</span>
            ))}
          </div>
        </div>
      )}
      <Link to="/roadmap" className="flex items-center gap-1 text-xs text-primary-600 font-medium mt-3 no-underline hover:underline">
        {t('chatbot.cards.roadmap.cta')} <ExternalLink className="w-3 h-3" />
      </Link>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Typing Indicator
   ═══════════════════════════════════════════ */

function TypingIndicator({ contextType, lastIntent }) {
  const { t } = useTranslation();
  const loadingMsg = LOADING_MESSAGES[lastIntent] || LOADING_MESSAGES.general;

  return (
    <div className="flex gap-2.5 max-w-3xl mx-auto">
      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-purple-600" />
      </div>
      <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-md px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-xs text-gray-400 dark:text-gray-500">{t(loadingMsg)}</span>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Smart Suggestions
   ═══════════════════════════════════════════ */

function SmartSuggestions({ contextType, onSuggestion }) {
  const { t } = useTranslation();
  const suggestions = SUGGESTIONS[contextType] || SUGGESTIONS.help;

  return (
    <div className="flex flex-wrap gap-2 max-w-3xl mx-auto pl-11">
      {suggestions.map((s) => (
        <button
          key={s}
          onClick={() => onSuggestion(t(s))}
          className="inline-flex items-center gap-1 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-xs text-gray-600 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-200 dark:hover:border-primary-800 hover:text-primary-700 dark:hover:text-primary-300 cursor-pointer transition-all"
        >
          {t(s)}
          <ChevronRight className="w-3 h-3 opacity-40" />
        </button>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════
   Helpers
   ═══════════════════════════════════════════ */

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatSalary(amount, t) {
  if (!amount) return t('chatbot.na');
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M UZS`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(0)}K UZS`;
  return `${amount} UZS`;
}

function groupConversations(conversations) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const groups = { Active: [], Today: [], 'This Week': [], Older: [] };

  for (const c of conversations) {
    const date = new Date(c.started_at);
    if (c.is_active) {
      groups.Active.push(c);
    } else if (date >= today) {
      groups.Today.push(c);
    } else if (date >= weekAgo) {
      groups['This Week'].push(c);
    } else {
      groups.Older.push(c);
    }
  }

  return groups;
}
