"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Bot, User, Mic, MicOff, Activity, Settings, ShieldAlert, Cpu, CheckCircle, Link as LinkIcon, Radio, ShieldCheck, Phone } from 'lucide-react';

type AppView = 'MISSION_SETUP' | 'NEGOTIATION_ROOM';
type Role = 'OWNER' | 'FRIEND';

export default function ProxyPact() {
  const [view, setView] = useState<AppView>('MISSION_SETUP');
  const [role, setRole] = useState<Role>('OWNER');
  
  // Mission state
  const [objective, setObjective] = useState('');
  const [privateConstraints, setPrivateConstraints] = useState('');
  const [requiredConditions, setRequiredConditions] = useState('');
  const [preferences, setPreferences] = useState('');
  const [authorityRules, setAuthorityRules] = useState('');
  
  // Chat state
  const [messages, setMessages] = useState<{sender: string, text: string, action?: string}[]>([]);
  const [inputText, setInputText] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  // AI Status & Connection & Call Mode
  const [aiStatus, setAiStatus] = useState('Idle'); 
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [isCallMode, setIsCallMode] = useState(false);
  const [setupError, setSetupError] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const recognitionRef = useRef<any>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('role') === 'friend') {
        setRole('FRIEND');
        joinAsFriend();
      }
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const joinAsFriend = () => {
    connectWebSocket();
    setView('NEGOTIATION_ROOM');
  };

  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const websocket = new WebSocket(`${protocol}//${window.location.host}/ws`);
      
      websocket.onopen = () => {
        setWs(websocket);
        setConnectionStatus('Connected');
        setAiStatus('Listening');
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'SYSTEM') {
          setMessages(prev => [...prev, { sender: 'System', text: data.text }]);
        } else if (data.sender === 'Friend' || data.sender === 'Agent' || data.sender === 'Owner') {
          setMessages(prev => [...prev, { sender: data.sender, text: data.text, action: data.action }]);
          if (data.sender === 'Agent') {
            setAiStatus('Speaking');
            
            // Text to speech for agent response
            const utterance = new SpeechSynthesisUtterance(data.text);
            utterance.onend = () => setAiStatus('Listening');
            window.speechSynthesis.speak(utterance);
          }
        }
      };
      
      websocket.onclose = () => {
        setConnectionStatus('Disconnected');
        setAiStatus('Offline');
      };
      
    } catch (err) {
      console.error(err);
      setConnectionStatus('Error');
    }
  };

  const startSession = async () => {
    setSetupError('');
    if (!objective.trim()) {
      setSetupError("Please enter an objective.");
      return;
    }
    
    setIsStarting(true);
    try {
      const res = await fetch('/api/mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objective,
          private_constraints: privateConstraints.split('\n').filter(Boolean),
          required_conditions: requiredConditions.split('\n').filter(Boolean),
          preferences: preferences.split('\n').filter(Boolean),
          authority_rules: authorityRules.split('\n').filter(Boolean),
        })
      });
      
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      
      connectWebSocket();
      setView('NEGOTIATION_ROOM');
      
    } catch (err: any) {
      console.error(err);
      setSetupError("Failed to connect to backend: " + err.message);
    } finally {
      setIsStarting(false);
    }
  };
  
  const sendMessage = (text: string) => {
    if (!text.trim() || !ws) return;
    
    if (role === 'FRIEND') {
      ws.send(JSON.stringify({ text }));
    } else {
      ws.send(JSON.stringify({ text, sender: 'Owner' })); 
    }
    
    setAiStatus('Thinking');
  };
  
  const toggleCallMode = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in this browser. Try Chrome.");
      return;
    }
    
    if (isCallMode) {
      // Turn off
      setIsCallMode(false);
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      return;
    }
    
    // Turn on
    setIsCallMode(true);
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = true; // Listen continuously for mobile call scenario
    recognition.interimResults = false;
    
    recognition.onresult = (event: any) => {
      const current = event.resultIndex;
      const transcript = event.results[current][0].transcript;
      sendMessage(transcript);
    };
    
    recognition.onerror = (event: any) => {
      console.error("Speech recognition error", event.error);
      if (event.error === 'not-allowed') setIsCallMode(false);
    };
    
    recognition.onend = () => {
      // Restart if still in call mode (some browsers stop continuous after a while)
      if (isCallMode && recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch(e) {}
      }
    };
    
    recognitionRef.current = recognition;
    recognition.start();
  };

  const copyFriendLink = () => {
    const link = `${window.location.origin}${window.location.pathname}?role=friend`;
    navigator.clipboard.writeText(link);
    alert("Friend link copied to clipboard!");
  };

  if (view === 'MISSION_SETUP') {
    return (
      <div className="min-h-screen bg-slate-50 p-4 py-8 md:p-12 selection:bg-violet-200 selection:text-violet-900">
        <div className="w-full max-w-2xl mx-auto bg-white rounded-3xl md:rounded-[2rem] shadow-2xl shadow-violet-900/5 border border-slate-200 p-6 md:p-10 relative h-auto">
          <div className="absolute top-0 inset-x-0 h-2 bg-gradient-to-r from-violet-600 to-fuchsia-600"></div>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 md:w-14 md:h-14 bg-violet-100 text-violet-600 rounded-2xl flex items-center justify-center rotate-3 shrink-0">
                <Bot className="w-6 h-6 md:w-8 md:h-8" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-black text-slate-800 tracking-tight">ProxyPact</h1>
                <p className="text-[10px] md:text-xs font-bold uppercase tracking-widest text-slate-400 mt-1">Owner Initialization</p>
              </div>
            </div>
            <button onClick={copyFriendLink} className="flex items-center justify-center gap-2 text-[10px] md:text-xs font-bold text-violet-600 bg-violet-50 hover:bg-violet-100 px-4 py-3 md:py-2 rounded-full transition-colors w-full md:w-auto">
              <LinkIcon className="w-4 h-4" /> Copy Friend Link
            </button>
          </div>
          
          <div className="space-y-4 md:space-y-6">
            <div className="bg-slate-50 p-4 md:p-6 rounded-2xl border border-slate-100">
              <label className="block text-[10px] md:text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 md:mb-3">Core Objective</label>
              <input type="text" value={objective} onChange={e => setObjective(e.target.value)} placeholder="What are you negotiating?" className="w-full p-3 md:p-4 border-2 border-slate-200 rounded-xl focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 outline-none transition-all font-medium text-slate-800 text-sm md:text-base" />
            </div>
            
            <div className="bg-rose-50 p-4 md:p-6 rounded-2xl border border-rose-100 relative">
              <div className="absolute top-4 right-4"><ShieldAlert className="w-4 h-4 md:w-5 md:h-5 text-rose-300"/></div>
              <label className="block text-[10px] md:text-xs font-bold uppercase tracking-widest text-rose-600 mb-2 md:mb-3">Private Boundaries (1 per line)</label>
              <textarea value={privateConstraints} onChange={e => setPrivateConstraints(e.target.value)} placeholder="Max price, walk-away conditions..." className="w-full p-3 md:p-4 border-2 border-rose-200/50 rounded-xl focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 outline-none transition-all font-medium text-slate-800 h-20 md:h-24 resize-none text-sm md:text-base" />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
              <div className="bg-slate-50 p-4 md:p-6 rounded-2xl border border-slate-100">
                <label className="block text-[10px] md:text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 md:mb-3">Required Conditions</label>
                <textarea value={requiredConditions} onChange={e => setRequiredConditions(e.target.value)} className="w-full p-3 md:p-4 border-2 border-slate-200 rounded-xl focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 outline-none transition-all font-medium text-slate-800 h-20 md:h-24 resize-none text-sm md:text-base" />
              </div>
              
              <div className="bg-slate-50 p-4 md:p-6 rounded-2xl border border-slate-100">
                <label className="block text-[10px] md:text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 md:mb-3">Preferences</label>
                <textarea value={preferences} onChange={e => setPreferences(e.target.value)} className="w-full p-3 md:p-4 border-2 border-slate-200 rounded-xl focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 outline-none transition-all font-medium text-slate-800 h-20 md:h-24 resize-none text-sm md:text-base" />
              </div>
            </div>
            
            <div className="bg-slate-50 p-4 md:p-6 rounded-2xl border border-slate-100">
              <label className="block text-[10px] md:text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 md:mb-3">Authority Rules</label>
              <textarea value={authorityRules} onChange={e => setAuthorityRules(e.target.value)} className="w-full p-3 md:p-4 border-2 border-slate-200 rounded-xl focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 outline-none transition-all font-medium text-slate-800 h-20 resize-none text-sm md:text-base" />
            </div>
            
            {setupError && (
              <div className="p-4 bg-rose-50 text-rose-600 border border-rose-200 rounded-xl text-sm font-bold flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" />
                {setupError}
              </div>
            )}
            
            <button 
              onClick={(e) => {
                e.preventDefault();
                startSession();
              }} 
              disabled={isStarting}
              className={`w-full text-white font-black uppercase tracking-widest py-4 md:py-5 rounded-xl transition-all shadow-xl mt-4 text-sm md:text-base flex justify-center items-center gap-2 ${
                isStarting ? 'bg-slate-400 cursor-not-allowed shadow-none' : 'bg-slate-900 hover:bg-slate-800 shadow-slate-900/10'
              }`}
            >
              {isStarting ? <Activity className="w-5 h-5 animate-spin" /> : null}
              {isStarting ? 'Connecting...' : 'Start Agent'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans selection:bg-violet-200 selection:text-violet-900">
      {/* GLOBAL HEADER */}
      <header className="bg-white border-b border-slate-200 p-3 md:p-4 px-4 md:px-8 flex justify-between items-center z-50 sticky top-0">
        <div className="flex items-center gap-2 md:gap-3">
          <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white rounded-lg md:rounded-xl flex items-center justify-center shadow-md">
            <Bot className="w-4 h-4 md:w-5 md:h-5" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg md:text-xl font-black text-slate-800 tracking-tight leading-tight">ProxyPact</h1>
            <p className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-slate-400">{role === 'OWNER' ? 'Owner Console' : 'Guest Interface'}</p>
          </div>
        </div>
        
        {/* Mobile Header Status */}
        <div className="flex items-center gap-2 md:gap-4">
          <button 
            onClick={toggleCallMode}
            className={`flex items-center gap-2 px-3 py-1.5 md:px-4 md:py-2 rounded-full text-[10px] font-black uppercase tracking-widest shadow-sm transition-all border ${
              isCallMode 
                ? 'bg-rose-500 text-white border-rose-600 animate-pulse' 
                : 'bg-emerald-50 text-emerald-600 border-emerald-100'
            }`}
          >
            {isCallMode ? <Phone className="w-3 h-3 fill-current" /> : <Mic className="w-3 h-3" />}
            {isCallMode ? 'Live Call' : 'Auto-Listen'}
          </button>
          
          {role === 'OWNER' && (
            <div className="hidden sm:flex px-4 py-2 bg-rose-50 border border-rose-100 text-rose-600 font-black uppercase tracking-widest rounded-full text-[10px] items-center gap-2 shadow-sm">
              <ShieldCheck className="w-3 h-3" />
              Privacy Protected
            </div>
          )}
        </div>
      </header>
      
      <div className="flex-1 p-3 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6 min-h-0 flex-col md:flex-row">
        
        {/* LEFT PANEL: MISSION (OWNER ONLY) - Hidden on mobile by default, could be a tab, but we'll stack it at the bottom on mobile */}
        {role === 'OWNER' && (
          <div className="lg:col-span-3 bg-white rounded-2xl md:rounded-3xl p-4 md:p-6 border border-slate-200 shadow-sm overflow-y-auto lg:h-[calc(100vh-100px)] custom-scrollbar order-3 lg:order-1">
            <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-8 pb-3 md:pb-4 border-b border-slate-100">
              <div className="w-6 h-6 md:w-8 md:h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
                <Settings className="w-3 h-3 md:w-4 md:h-4" />
              </div>
              <h2 className="text-xs md:text-sm font-black uppercase tracking-widest text-slate-800">Mission Parameters</h2>
            </div>
            
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-3 md:gap-5 flex-1">
              <div className="bg-slate-50 p-3 md:p-5 rounded-xl md:rounded-2xl border border-slate-100">
                <span className="text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-1 md:gap-1.5 mb-1 md:mb-2"><CheckCircle className="w-3 h-3 text-emerald-500"/> Objective</span>
                <p className="text-xs md:text-sm font-medium text-slate-700 leading-relaxed truncate lg:whitespace-normal">{objective}</p>
              </div>
              
              <div className="bg-rose-50 p-3 md:p-5 rounded-xl md:rounded-2xl border border-rose-100">
                <span className="text-[8px] md:text-[10px] font-black text-rose-600 uppercase tracking-widest flex items-center gap-1 md:gap-1.5 mb-1 md:mb-2"><ShieldAlert className="w-3 h-3"/> Constraints</span>
                <ul className="list-disc pl-3 md:pl-4 text-xs md:text-sm font-medium text-rose-900 leading-relaxed truncate lg:whitespace-normal">
                  {privateConstraints.split('\n').filter(Boolean).map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {/* CENTER PANEL: TRANSCRIPT */}
        <div className={`${role === 'OWNER' ? 'lg:col-span-6' : 'lg:col-span-9'} bg-white rounded-2xl md:rounded-3xl border border-slate-200 shadow-lg shadow-slate-200/50 flex flex-col h-[50vh] lg:h-[calc(100vh-100px)] overflow-hidden order-1 lg:order-2`}>
          <div className="p-3 md:p-5 border-b border-slate-100 bg-white z-10 flex justify-between items-center shadow-sm shrink-0">
            <h2 className="text-xs md:text-sm font-black uppercase tracking-widest text-slate-800">Live Transcript</h2>
            <span className="text-[8px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest bg-slate-100 px-2 md:px-3 py-1 rounded-full">Encrypted</span>
          </div>
          
          <div className="flex-1 p-3 md:p-6 overflow-y-auto space-y-4 md:space-y-6 custom-scrollbar bg-slate-50/50">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-50 space-y-4">
                <Bot className="w-12 h-12" />
                <p className="text-xs uppercase tracking-widest font-bold">Waiting for transmission...</p>
              </div>
            )}
            {messages.map((m, i) => {
              const isAI = m.sender === 'Agent';
              const isSystem = m.sender === 'System';
              const isMe = (role === 'FRIEND' && m.sender === 'Friend') || (role === 'OWNER' && m.sender === 'Owner');
              
              if (isSystem) {
                return (
                  <div key={i} className="flex justify-center">
                    <span className="text-[8px] md:text-[10px] font-black text-slate-400 bg-slate-200/50 px-3 py-1 rounded-full uppercase tracking-widest">{m.text}</span>
                  </div>
                );
              }
              
              return (
                <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                  <div className={`max-w-[85%] md:max-w-[80%] p-3 md:p-5 rounded-2xl md:rounded-[2rem] shadow-sm ${
                    isAI 
                      ? 'bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white rounded-tl-sm shadow-violet-500/20' 
                      : isMe 
                        ? 'bg-slate-900 text-white rounded-tr-sm shadow-slate-900/10'
                        : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
                  }`}>
                    <div className={`flex items-center gap-1.5 md:gap-2 mb-1.5 md:mb-2 ${isMe ? 'flex-row-reverse' : ''}`}>
                      <div className={`w-5 h-5 md:w-6 md:h-6 rounded-full flex items-center justify-center ${isAI || isMe ? 'bg-white/20' : 'bg-slate-100'}`}>
                        {isAI ? <Bot className="w-3 h-3 text-white" /> : <User className={`w-3 h-3 ${isMe ? 'text-white' : 'text-slate-500'}`} />}
                      </div>
                      <div className={`text-[8px] md:text-[10px] uppercase font-black tracking-widest ${isAI ? 'text-violet-200' : isMe ? 'text-slate-300' : 'text-slate-400'}`}>
                        {m.sender}
                      </div>
                    </div>
                    <p className="text-xs md:text-sm font-medium leading-relaxed">{m.text}</p>
                  </div>
                </div>
              );
            })}
            <div ref={chatEndRef} />
          </div>
          
          {/* Mobile Input Bar */}
          <div className="p-2 md:p-4 border-t border-slate-100 bg-white z-10 flex gap-2 shrink-0">
            <button 
              onClick={toggleCallMode} 
              className={`p-3 md:p-4 rounded-xl md:rounded-2xl transition-colors flex items-center justify-center shrink-0 border ${
                isCallMode ? 'bg-rose-50 border-rose-200 text-rose-500 animate-pulse' : 'bg-slate-50 border-slate-200 text-slate-500 hover:bg-slate-100'
              }`}
            >
              {isCallMode ? <MicOff className="w-4 h-4 md:w-5 md:h-5" /> : <Mic className="w-4 h-4 md:w-5 md:h-5" />}
            </button>
            <input 
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  sendMessage(inputText);
                  setInputText('');
                }
              }}
              placeholder={isCallMode ? "Listening..." : "Message..."}
              className="flex-1 px-3 py-2 md:p-4 bg-slate-50 border border-slate-200 rounded-xl md:rounded-2xl focus:outline-none focus:border-violet-500 focus:bg-white transition-all text-xs md:text-sm font-medium text-slate-800 placeholder:text-slate-400"
            />
            <button 
              onClick={() => { sendMessage(inputText); setInputText(''); }} 
              className="px-4 md:px-8 py-3 md:py-4 bg-slate-900 text-white text-xs md:text-sm font-black uppercase tracking-widest rounded-xl md:rounded-2xl hover:bg-slate-800 transition-all shadow-lg shadow-slate-900/10 shrink-0"
            >
              Send
            </button>
          </div>
        </div>
        
        {/* RIGHT PANEL: AI STATUS */}
        <div className="lg:col-span-3 bg-white rounded-2xl md:rounded-3xl p-4 md:p-6 border border-slate-200 shadow-sm flex flex-col h-auto lg:h-[calc(100vh-100px)] order-2 lg:order-3">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-8 pb-3 md:pb-4 border-b border-slate-100">
            <div className="w-6 h-6 md:w-8 md:h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
              <Activity className="w-3 h-3 md:w-4 md:h-4" />
            </div>
            <h2 className="text-xs md:text-sm font-black uppercase tracking-widest text-slate-800">Telemetry</h2>
          </div>
          
          <div className="flex lg:flex-col gap-4 lg:gap-6 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
            <div className="min-w-[120px] lg:min-w-0">
              <span className="text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 md:mb-3">Connection</span>
              <div className={`px-3 py-2 md:p-4 rounded-xl md:rounded-2xl border-2 text-[10px] md:text-xs font-black uppercase tracking-widest text-center transition-colors ${
                connectionStatus === 'Connected' ? 'bg-emerald-50 border-emerald-200 text-emerald-600' :
                connectionStatus === 'Disconnected' ? 'bg-slate-50 border-slate-200 text-slate-500' :
                'bg-rose-50 border-rose-200 text-rose-600'
              }`}>
                {connectionStatus}
              </div>
            </div>

            <div className="min-w-[120px] lg:min-w-0 flex-1">
              <span className="text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 md:mb-3">Engine State</span>
              <div className="flex lg:flex-col gap-2 md:gap-3">
                {['Listening', 'Thinking', 'Speaking'].map((state) => (
                  <div key={state} className={`flex items-center gap-2 md:gap-4 px-3 py-2 md:p-4 rounded-xl md:rounded-2xl border-2 transition-all duration-300 ${
                    aiStatus === state 
                      ? 'bg-violet-50 border-violet-200 text-violet-700 shadow-sm lg:translate-x-1' 
                      : 'bg-white border-slate-100 text-slate-400 opacity-60'
                  }`}>
                    <Cpu className={`w-3 h-3 md:w-5 md:h-5 ${aiStatus === state && state === 'Thinking' ? 'animate-pulse' : ''}`} />
                    <span className="text-[8px] md:text-xs font-black uppercase tracking-widest hidden sm:inline">{state}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {messages.length > 0 && messages[messages.length - 1].sender === 'Agent' && (
              <div className="mt-auto lg:mt-8 min-w-[150px] lg:min-w-0">
                <span className="text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 md:mb-3">Last Action</span>
                <div className="px-4 py-2 md:p-5 bg-slate-900 rounded-xl md:rounded-2xl text-white shadow-xl shadow-slate-900/20">
                  <p className="font-black text-sm md:text-xl tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-fuchsia-400">
                    {messages[messages.length - 1].action || 'REPLY'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
        
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #e2e8f0;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #cbd5e1;
        }
      `}} />
    </div>
  );
}
