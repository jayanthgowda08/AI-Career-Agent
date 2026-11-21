import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import API from '../services/api';
import {
  Send,
  Bot,
  User,
  Wrench,
  Sparkles,
  Bookmark,
  Briefcase,
  HelpCircle,
  CornerDownLeft,
} from 'lucide-react';

export default function AgentChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello! I am your AI Career Agent. I have access to real job listings, skill gap diagnostics, and career guidance documents. How can I assist your job search today?",
      tools_used: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 9));
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await API.post('/agent/chat', {
        message: userMsg,
        session_id: sessionId,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.message,
          tools_used: res.data.tools_used || [],
          referenced_jobs: res.data.referenced_jobs || [],
        },
      ]);
    } catch (err) {
      console.error("Agent chat error:", err);
      const errorMsg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "I encountered an error executing this request. Please verify the backend is running.";
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${errorMsg}`,
          tools_used: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    "What jobs do you recommend for my profile?",
    "Find remote Python FastAPI jobs",
    "What skills am I missing for Junior AI Engineer?",
    "Show me my saved jobs",
  ];

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-hidden">
      <Navbar
        title="AI Career Assistant"
        subtitle="LangGraph state machine with autonomous tool calling"
      />

      {/* Chat scroll area */}
      <div className="flex-1 overflow-y-auto p-6 max-w-4xl w-full mx-auto space-y-6">
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={idx}
              className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 text-indigo-400 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-[85%] space-y-2`}>
                {/* Tool Badge Indicator */}
                {!isUser && msg.tools_used && msg.tools_used.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pb-1">
                    {msg.tools_used.map((tool, tIdx) => (
                      <span
                        key={tIdx}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-950/80 border border-indigo-500/30 text-[11px] font-semibold text-indigo-300 shadow-sm"
                      >
                        <Wrench className="w-3 h-3 text-indigo-400" />
                        <span>Executed: {tool.tool_name}()</span>
                      </span>
                    ))}
                  </div>
                )}

                {/* Bubble */}
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-tr-sm shadow-lg shadow-indigo-600/20'
                      : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm shadow-md'
                  }`}
                >
                  {msg.content}
                </div>
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300 mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-3.5 items-center text-slate-400 text-xs">
            <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 text-indigo-400">
              <Bot className="w-4 h-4 animate-pulse" />
            </div>
            <div className="flex items-center gap-2 p-3 rounded-2xl bg-slate-900 border border-slate-800">
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"></div>
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]"></div>
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.4s]"></div>
              <span className="text-[11px] text-slate-400 font-medium ml-1">Agent reasoning & tool calling...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested prompts if only 1 message */}
      {messages.length === 1 && (
        <div className="max-w-4xl w-full mx-auto px-6 pb-2">
          <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {samplePrompts.map((p, i) => (
              <button
                key={i}
                onClick={() => { setInput(p); }}
                className="text-xs px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input box */}
      <div className="p-4 bg-slate-900/80 border-t border-slate-800/80">
        <form
          onSubmit={handleSend}
          className="max-w-4xl mx-auto flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-2xl p-2 focus-within:border-indigo-500/60 transition-colors shadow-xl"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your career assistant to search, compare, or analyze skill gaps..."
            className="flex-1 bg-transparent px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white transition-all shadow-md shadow-indigo-600/30"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
