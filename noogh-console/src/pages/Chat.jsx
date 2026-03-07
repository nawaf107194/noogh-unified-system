import React, { useState, useRef, useEffect } from 'react';
import {
  Send, Bot, User, RefreshCw, Cpu, Activity,
  Mic, MicOff, Image, Paperclip, X, Volume2,
  VolumeX, Sparkles, Zap, Shield, Lock, Unlock,
  Terminal, Eye, EyeOff, AlertTriangle, CheckCircle,
  ChevronDown, ChevronUp, BrainCircuit, MessageSquare,
  CommandLine, Info
} from 'lucide-react';

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'أهلاً بك يا قائد! 👋\nأنا **نوقة** (NOOGH) — شريكك الاستراتيجي في السيادة التقنية.\n\nكيف يمكنني مساعدتك في إدارة النظام اليوم؟',
      timestamp: new Date()
    }
  ]);
  const [showThought, setShowThought] = useState({}); // Tracking which thought boxes are open
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [attachedImage, setAttachedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // ═══════════════════════════════════════════════════════════
  // Execution Mode State
  // ═══════════════════════════════════════════════════════════
  const [executionMode, setExecutionMode] = useState(false);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordVerified, setPasswordVerified] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ═══════════════════════════════════════════════════════════
  // Voice Recording (Microphone)
  // ═══════════════════════════════════════════════════════════
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await handleVoiceInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('لا يمكن الوصول للميكروفون. تأكد من صلاحيات المتصفح.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleVoiceInput = async (audioBlob) => {
    // For now, we'll use browser's speech recognition as a fallback
    // In production, this would send to a speech-to-text API

    try {
      // Check if SpeechRecognition is available
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'ar-SA'; // Arabic
        recognition.interimResults = false;

        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          setInput(transcript);
        };

        recognition.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
        };

        recognition.start();
      } else {
        // Fallback: Add voice message indicator
        setInput('🎤 [رسالة صوتية]');
      }
    } catch (error) {
      console.error('Voice processing error:', error);
    }
  };

  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // ═══════════════════════════════════════════════════════════
  // Image Attachment
  // ═══════════════════════════════════════════════════════════
  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setAttachedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeAttachedImage = () => {
    setAttachedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ═══════════════════════════════════════════════════════════
  // Text-to-Speech
  // ═══════════════════════════════════════════════════════════
  const speakMessage = (text) => {
    if ('speechSynthesis' in window) {
      // Stop any current speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text.replace(/\*\*/g, '').replace(/[🔐🛡️👋📊✅⚠️]/g, ''));
      utterance.lang = 'ar-SA';
      utterance.rate = 0.9;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  // ═══════════════════════════════════════════════════════════
  // Content Parser (DeepSeek Style)
  // ═══════════════════════════════════════════════════════════
  const parseMessage = (content) => {
    // Search for "نوقة (تفكير):" markers
    const thoughtMarker = "نوقة (تفكير):";
    const decisionMarker = "القرار (JSON):";
    const answerMarker = "الاستنتاج:"; // Optional if AI adds it

    let thought = "";
    let action = "";
    let answer = content;

    if (content.includes(thoughtMarker)) {
      const parts = content.split(thoughtMarker);
      const afterThought = parts[1] || "";

      // Look for the end of thought (either decision or just the rest)
      if (afterThought.includes(decisionMarker)) {
        const subParts = afterThought.split(decisionMarker);
        thought = subParts[0].trim();
        answer = subParts[1].trim(); // Rest as answer for now
      } else {
        // Find where thought likely ends (e.g., after a few paragraphs or explicit markers)
        // If there's no decision marker, we might need a delimiter or detect the shift in tone
        // For now, if "الخلاصة:" exists:
        if (afterThought.includes("الخلاصة:")) {
          const sub = afterThought.split("الخلاصة:");
          thought = sub[0].trim();
          answer = sub[1].trim();
        } else {
          // Take the first few lines as thought if it's long, or the whole thing if no other markers
          thought = afterThought.trim();
          answer = ""; // Answer will be typed or processed
        }
      }
    } else if (content.includes("THINK:")) {
      const parts = content.split("THINK:");
      const afterThink = parts[1] || "";
      if (afterThink.includes("ANSWER:")) {
        const sub = afterThink.split("ANSWER:");
        thought = sub[0].trim();
        answer = sub[1].trim();
      } else {
        thought = afterThink.trim();
        answer = "";
      }
    }

    return { thought, action, answer: answer || content };
  };

  const toggleThought = (idx) => {
    setShowThought(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  // ═══════════════════════════════════════════════════════════
  // Render
  // ═══════════════════════════════════════════════════════════
  return (
    <div className="flex flex-col h-[calc(100vh-100px)] bg-[#0A0C10] rounded-3xl border border-white/5 overflow-hidden shadow-2xl shadow-black">

      {/* ═══════════════════════════════════════════════════════════
          Header
          ═══════════════════════════════════════════════════════════ */}
      <div className="px-6 py-4 border-b border-white/5 bg-[#0D1117]/80 backdrop-blur-xl flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="relative group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#3B82F6] to-[#8B5CF6] flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.5)] group-hover:scale-105 transition-transform">
              <Sparkles className="text-white" size={24} />
            </div>
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-[#0A0C10] shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
          </div>
          <div>
            <h2 className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
              نوقة السيادي <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">v12.9.2</span>
            </h2>
            <div className="flex items-center gap-2 text-xs mt-0.5 text-slate-400">
              <Activity size={12} className="text-blue-500 animate-pulse" />
              <span>المحرك العصبي في قمة الجاهزية</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Execution Mode Toggle */}
          <button
            onClick={() => {
              setExecutionMode(!executionMode);
              if (executionMode) {
                setPassword('');
                setPasswordVerified(false);
              }
            }}
            className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all font-medium text-sm ${executionMode
              ? 'bg-orange-500/20 border border-orange-500/50 text-orange-400'
              : 'bg-slate-800/50 border border-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            title={executionMode ? 'تعطيل وضع التنفيذ' : 'تفعيل وضع التنفيذ'}
          >
            {executionMode ? <Unlock size={16} /> : <Lock size={16} />}
            <span className="hidden md:inline">{executionMode ? 'وضع التنفيذ' : 'القراءة فقط'}</span>
          </button>

          {/* Clear Button */}
          <button
            onClick={() => setMessages([messages[0]])}
            className="p-3 hover:bg-slate-700/50 rounded-xl text-slate-400 hover:text-white transition-all"
            title="مسح المحادثة"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Messages Area
          ═══════════════════════════════════════════════════════════ */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-[#0A0C10] scrollbox-premium">
        {messages.map((msg, idx) => {
          const { thought, answer } = msg.role === 'assistant' ? parseMessage(msg.content) : { thought: "", answer: msg.content };
          const isUser = msg.role === 'user';

          return (
            <div
              key={idx}
              className={`flex gap-5 ${isUser ? 'flex-row-reverse' : ''} animate-message-entry`}
            >
              {/* Avatar */}
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-2xl transition-all duration-500 ${isUser
                ? 'bg-[#1E293B] border border-white/5'
                : 'bg-gradient-to-br from-blue-600 to-indigo-700 shadow-blue-500/20'
                }`}>
                {isUser ? <User size={18} className="text-slate-400" /> : <Bot size={20} className="text-white" />}
              </div>

              {/* Message Content Container */}
              <div className={`flex flex-col gap-2 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>

                {/* Thinking Block (DeepSeek Style) */}
                {!isUser && thought && (
                  <div className="w-full mb-1">
                    <button
                      onClick={() => toggleThought(idx)}
                      className="flex items-center gap-3 text-xs font-semibold text-slate-500 hover:text-blue-400 transition-colors py-1 group"
                    >
                      <div className={`p-1 rounded-full bg-slate-800/50 group-hover:bg-blue-500/10 transition-colors ${showThought[idx] ? 'rotate-180' : ''}`}>
                        <ChevronDown size={14} />
                      </div>
                      <span className="flex items-center gap-2">
                        <BrainCircuit size={14} className={loading && idx === messages.length - 1 ? 'animate-pulse text-blue-500' : ''} />
                        {showThought[idx] ? 'إخفاء مسار التفكير' : 'عرض مسار التفكير'}
                      </span>
                    </button>

                    {showThought[idx] && (
                      <div className="mt-2 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] text-slate-400 text-sm italic leading-relaxed whitespace-pre-wrap animate-fade-in border-r-2 border-r-blue-500/30">
                        {thought}
                      </div>
                    )}
                  </div>
                )}

                {/* Main Bubble */}
                <div className={`relative px-6 py-4 rounded-3xl shadow-sm text-[15px] leading-relaxed transition-all duration-300 ${isUser
                  ? 'bg-[#3B82F6] text-white rounded-tr-none'
                  : 'bg-[#161B22] border border-white/5 text-slate-200 rounded-tl-none'
                  }`}>
                  {/* Image Attachment inside bubble */}
                  {msg.image && (
                    <div className="mb-4 rounded-xl overflow-hidden border border-white/10 shadow-lg">
                      <img src={msg.image} alt="Uploaded" className="max-w-full h-auto object-cover" />
                    </div>
                  )}

                  <div className="prose prose-invert max-w-none" dir="auto">
                    {answer.split('\n').map((line, li) => {
                      // Horizontal rule
                      if (line.trim() === '---') return <hr key={li} className="border-white/10 my-3" />;
                      // Code block markers
                      if (line.trim().startsWith('```')) return null;
                      // Bullet points
                      if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
                        const bulletContent = line.trim().replace(/^[-•]\s+/, '');
                        return (
                          <div key={li} className="flex gap-2 py-0.5" style={{ paddingRight: '0.5rem' }}>
                            <span className="text-blue-400 mt-0.5 shrink-0">●</span>
                            <span>{bulletContent.split('**').map((p, j) =>
                              j % 2 === 1 ? <strong key={j} className="text-white font-bold">{p}</strong> : p
                            )}</span>
                          </div>
                        );
                      }
                      // Numbered lists
                      if (/^\d+[\.\)]\s/.test(line.trim())) {
                        return (
                          <div key={li} className="flex gap-2 py-0.5" style={{ paddingRight: '0.5rem' }}>
                            <span className="text-blue-400 shrink-0 font-mono text-xs mt-1">{line.trim().match(/^\d+/)[0]}.</span>
                            <span>{line.trim().replace(/^\d+[\.\)]\s+/, '').split('**').map((p, j) =>
                              j % 2 === 1 ? <strong key={j} className="text-white font-bold">{p}</strong> : p
                            )}</span>
                          </div>
                        );
                      }
                      // Empty line = spacing
                      if (!line.trim()) return <div key={li} className="h-2" />;
                      // Regular text with bold support + inline code
                      return (
                        <div key={li} className="py-0.5">
                          {line.split('**').map((p, j) =>
                            j % 2 === 1 ? <strong key={j} className="text-white font-bold">{p}</strong> :
                              p.split('`').map((cp, ck) =>
                                ck % 2 === 1 ? <code key={ck} className="bg-white/10 px-1.5 py-0.5 rounded text-blue-300 text-xs font-mono">{cp}</code> : cp
                              )
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Footer Info */}
                <div className={`flex items-center gap-3 mt-1 px-2 group-hover:opacity-100 transition-opacity ${isUser ? 'flex-row-reverse' : ''}`}>
                  <span className="text-[10px] text-slate-600 font-mono">
                    {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {!isUser && (
                    <button
                      onClick={() => isSpeaking ? stopSpeaking() : speakMessage(answer)}
                      className="p-1 hover:bg-white/5 rounded-md text-slate-600 hover:text-blue-400 transition-colors"
                    >
                      {isSpeaking ? <VolumeX size={12} /> : <Volume2 size={12} />}
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-5 animate-pulse">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center shrink-0">
              <Zap size={20} className="text-blue-500" />
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-blue-400 mb-1">
                <RefreshCw size={14} className="animate-spin" />
                جاري توليد الاستجابة...
              </div>
              <div className="bg-[#161B22] border border-white/5 p-4 rounded-2xl rounded-tl-sm w-32 h-10 skeleton-pulse"></div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Image Preview
          ═══════════════════════════════════════════════════════════ */}
      {imagePreview && (
        <div className="px-4 py-3 border-t border-slate-700/50 bg-slate-900/80">
          <div className="relative inline-block">
            <img
              src={imagePreview}
              alt="Preview"
              className="h-20 rounded-xl border border-slate-600/50"
            />
            <button
              onClick={removeAttachedImage}
              className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white hover:bg-red-600 transition-colors shadow-lg"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Execution Mode Password Panel
          ═══════════════════════════════════════════════════════════ */}
      {executionMode && (
        <div className="px-4 py-3 border-t border-orange-500/30 bg-orange-500/10">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-orange-400">
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">وضع التنفيذ مفعّل</span>
            </div>

            <div className="flex-1 flex items-center gap-3">
              <div className="relative flex-1 max-w-xs">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setPasswordVerified(e.target.value.length >= 6);
                  }}
                  placeholder="أدخل كلمة السر للتنفيذ..."
                  className="w-full bg-slate-800/80 border border-orange-500/30 text-white rounded-lg px-4 py-2 pr-10 focus:outline-none focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/20 transition-all placeholder-slate-500 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {passwordVerified && (
                <div className="flex items-center gap-1.5 text-green-400 text-sm">
                  <CheckCircle size={16} />
                  <span>جاهز</span>
                </div>
              )}
            </div>

            <div className="text-xs text-orange-400/70">
              الأوامر التنفيذية تحتاج كلمة سر
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Input Area
          ═══════════════════════════════════════════════════════════ */}
      <form onSubmit={handleSend} className="p-4 glass-dark border-t border-slate-700/50">
        <div className="flex gap-3">
          {/* Image Attach Button */}
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700/50 hover:border-slate-600 transition-all"
            title="إرفاق صورة"
          >
            <Image size={20} />
          </button>

          {/* Voice Recording Button */}
          <button
            type="button"
            onClick={toggleRecording}
            className={`p-3 rounded-xl border transition-all ${isRecording
              ? 'bg-red-500/20 border-red-500/50 text-red-400 animate-pulse'
              : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700/50 hover:border-slate-600'
              }`}
            title={isRecording ? 'إيقاف التسجيل' : 'تسجيل صوتي'}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isRecording ? '🎤 جاري التسجيل...' : executionMode ? '🔓 أدخل أمر التنفيذ السيادي...' : 'اسأل نوقة عن أي شيء...'}
            disabled={isRecording}
            className={`flex-1 bg-[#161B22]/50 border text-white rounded-2xl px-6 py-4 focus:outline-none focus:ring-1 transition-all placeholder-slate-600 disabled:opacity-50 ${executionMode
              ? 'border-orange-500/30 focus:border-orange-500/60 focus:ring-orange-500/30'
              : 'border-white/5 focus:border-blue-500/40 focus:ring-blue-500/20'
              }`}
            autoFocus
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={loading || (!input.trim() && !attachedImage)}
            className={`px-8 rounded-2xl text-white font-bold flex items-center gap-2 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${executionMode && passwordVerified
              ? 'bg-gradient-to-r from-orange-600 to-red-600 hover:shadow-[0_0_20px_rgba(234,88,12,0.4)]'
              : 'bg-[#3B82F6] hover:bg-[#2563EB] shadow-[0_0_15px_rgba(59,130,246,0.2)]'
              }`}
          >
            {loading ? <RefreshCw className="animate-spin" size={18} /> : (executionMode ? <Terminal size={18} /> : <Send size={18} />)}
            <span className="hidden sm:inline">{loading ? '...' : (executionMode ? 'تنفيذ' : 'إرسال')}</span>
          </button>
        </div>

        {/* Input Help */}
        <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Image size={12} />
              صور
            </span>
            <span className="flex items-center gap-1">
              <Mic size={12} />
              صوت
            </span>
            {executionMode && (
              <span className="flex items-center gap-1 text-orange-400">
                <Terminal size={12} />
                تنفيذ مفعّل
              </span>
            )}
          </div>
          <span>اضغط Enter للإرسال</span>
        </div>
      </form>
    </div>
  );
};

export default Chat;
