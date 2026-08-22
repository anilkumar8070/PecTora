"use client";

import React, { useState, useRef, useEffect } from 'react';
import HumanApprovalModal, { ApprovalData } from '@/components/HumanApprovalModal';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { Bot, User, Mic, Activity, CheckCircle, AlertTriangle, MessageSquare, ShieldAlert, Cpu, Settings, PhoneOff, ArrowRight, Zap, Sparkles } from 'lucide-react';

gsap.registerPlugin(useGSAP);

type AppView = 'MISSION_CREATION' | 'VOICE_SETUP' | 'NEGOTIATION' | 'RESULT';
type AgentState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';
type NegotiationStatus = 'NEGOTIATING' | 'APPROVAL_REQUIRED' | 'AGREEMENT_VERIFIED' | 'WALKED_AWAY';

export default function PectoraMain() {
  const [currentView, setCurrentView] = useState<AppView>('MISSION_CREATION');
  
  // Mission State
  const [missionTarget, setMissionTarget] = useState('₹40,000');
  const [missionMax, setMissionMax] = useState('₹42,000');
  const [missionVendor, setMissionVendor] = useState('Rahul');
  
  // Negotiation State
  const [agentState, setAgentState] = useState<AgentState>('IDLE');
  const [negotiationStatus, setNegotiationStatus] = useState<NegotiationStatus>('NEGOTIATING');
  const [messages, setMessages] = useState<{sender: string, text: string, type: 'PUBLIC' | 'PRIVATE'}[]>([]);
  const [approvalData, setApprovalData] = useState<ApprovalData | null>(null);
  const [inputText, setInputText] = useState('');

  // Refs for animations
  const containerRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll chat to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Entrance Animations
  useGSAP(() => {
    if (currentView === 'MISSION_CREATION') {
      gsap.fromTo(".mode-card", 
        { opacity: 0, scale: 0.8, y: 50 }, 
        { opacity: 1, scale: 1, y: 0, duration: 0.8, stagger: 0.15, ease: "back.out(1.7)" }
      );
      gsap.fromTo(".hero-text",
        { opacity: 0, y: -40, scale: 0.9 },
        { opacity: 1, y: 0, scale: 1, duration: 1, ease: "elastic.out(1, 0.5)" }
      );
      gsap.to(".floating-shape", {
        y: "-=30",
        rotation: "+=15",
        duration: 4,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut",
        stagger: 0.2
      });
    } else if (currentView === 'NEGOTIATION') {
      gsap.fromTo(".panel-left", { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 0.7, ease: "power3.out" });
      gsap.fromTo(".panel-center", { opacity: 0, y: 50, scale: 0.95 }, { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: "power3.out", delay: 0.1 });
      gsap.fromTo(".panel-right", { opacity: 0, x: 50 }, { opacity: 1, x: 0, duration: 0.7, ease: "power3.out", delay: 0.2 });
    }
  }, { dependencies: [currentView], scope: containerRef });

  const processTranscript = async (transcript: string) => {
    setMessages(prev => [...prev, { sender: "Counterparty (You)", text: transcript, type: "PUBLIC" }]);
    setAgentState('THINKING');

    const history = messages
      .filter(m => m.type === "PUBLIC")
      .map(m => `${m.sender}: ${m.text}`)
      .join("\n") + `\nCounterparty (You): ${transcript}`;

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: history })
      });
      
      const data = await response.json();
      const agentReply = data.dialogue || "I am evaluating that offer.";
      
      if (data.intent === 'WALK_AWAY') {
         setNegotiationStatus('WALKED_AWAY');
      } else if (data.intent === 'ACCEPT') {
         setNegotiationStatus('AGREEMENT_VERIFIED');
         setTimeout(() => setCurrentView('RESULT'), 3000);
      } else if (transcript.toLowerCase().includes("delivery") || transcript.toLowerCase().includes("days")) {
         triggerApproval(transcript);
         return;
      }
      
      setAgentState('SPEAKING');
      setMessages(prev => [...prev, { sender: "Agent", text: agentReply, type: "PUBLIC" }]);
      
      const utterance = new SpeechSynthesisUtterance(agentReply);
      utterance.onend = () => {
         if (data.intent === 'ACCEPT' || data.intent === 'WALK_AWAY') return;
         setAgentState('LISTENING');
      };
      window.speechSynthesis.speak(utterance);

    } catch (error) {
      console.error("LLM API Error:", error);
      const agentReply = "I am having trouble connecting to my cognitive engine. Please wait.";
      setAgentState('SPEAKING');
      setMessages(prev => [...prev, { sender: "System", text: agentReply, type: "PRIVATE" }]);
      setTimeout(() => setAgentState('LISTENING'), 3000);
    }
  };

  const triggerApproval = (transcript: string = "15-day delivery delay.") => {
    setNegotiationStatus('APPROVAL_REQUIRED');
    setApprovalData({
      whatHappened: `Counterparty introduced a new condition: "${transcript}"`,
      currentOffer: { price: 42000, delivery: 15 },
      newCondition: "delivery",
      reason: "Mission has no instructions regarding delivery delays.",
      agentRecommendation: "We should counter with max 7-day delivery."
    });
  };

  const startNegotiation = () => {
    setCurrentView('NEGOTIATION');
    setMessages([{ sender: "System", text: "Connected to secure negotiation room.", type: "PRIVATE" }]);
    
    navigator.mediaDevices.getUserMedia({ audio: true }).then(() => {
      setMessages(prev => [...prev, { sender: "System", text: "Microphone connected. Awaiting input...", type: "PRIVATE" }]);
      setAgentState('LISTENING');
      
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-IN'; 

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          processTranscript(transcript);
        };

        recognition.start();
      } else {
         setMessages(prev => [...prev, { sender: "System", text: "Speech Recognition not supported in this browser. Please use text input below.", type: "PRIVATE" }]);
      }
    }).catch(err => {
      console.error(err);
      setMessages(prev => [...prev, { sender: "System", text: "Microphone access denied. Operating in text-only mode.", type: "PRIVATE" }]);
    });
  };

  return (
    <div ref={containerRef} className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col selection:bg-purple-500/30 selection:text-purple-900 overflow-hidden relative">
      
      {/* VIBRANT BACKGROUND ELEMENTS */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-gradient-to-r from-purple-400 to-pink-400 rounded-full blur-[100px] opacity-20 pointer-events-none floating-shape" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-gradient-to-l from-blue-400 to-cyan-400 rounded-full blur-[100px] opacity-20 pointer-events-none floating-shape" />

      {/* GLOBAL HEADER */}
      <header className="relative z-10 bg-white/60 backdrop-blur-2xl border-b border-slate-200 p-5 flex justify-between items-center px-8 lg:px-12 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center shadow-lg shadow-violet-500/30 rotate-3 hover:rotate-6 transition-transform cursor-pointer">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-violet-700 to-fuchsia-700">
              PECTORA
            </h1>
            <p className="text-[10px] text-slate-500 font-bold tracking-[0.2em] uppercase mt-0.5">Advanced Agentic AI</p>
          </div>
        </div>
        <div className="flex gap-6 items-center">
          <a href="/observability" target="_blank" className="flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-violet-600 transition-colors"><Activity className="w-4 h-4"/> Observability</a>
          <a href="/evaluations" target="_blank" className="flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-violet-600 transition-colors"><CheckCircle className="w-4 h-4"/> Evaluations</a>
          <div className="h-4 w-px bg-slate-300"></div>
          <a href="/failure-demo" target="_blank" className="flex items-center gap-2 text-xs font-bold text-rose-500 hover:text-rose-600 transition-colors bg-rose-50 px-3 py-1.5 rounded-full"><AlertTriangle className="w-4 h-4"/> Edge Cases</a>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 relative z-10 flex flex-col overflow-hidden">
        
        {/* VIEW: MISSION CREATION */}
        {currentView === 'MISSION_CREATION' && (
          <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-12">
            <div className="hero-text text-center max-w-3xl">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-100 border border-violet-200 text-violet-700 text-xs font-bold mb-8 shadow-sm">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-violet-600"></span>
                </span>
                Systems Operational • AI Online
              </div>
              <h1 className="text-6xl lg:text-7xl font-black text-slate-800 mb-6 tracking-tight leading-tight">
                Next-Gen <br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-500">Autonomous Negotiation</span>
              </h1>
              <p className="text-xl text-slate-600 leading-relaxed font-medium">
                Unleash Pectora. Select an environment to see deterministic constraint boundaries execute in real-time.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl px-4">
              {/* MODE 1 */}
              <div className="mode-card group relative bg-white border border-slate-200 rounded-[2rem] p-8 flex flex-col cursor-pointer overflow-hidden transition-all duration-500 hover:-translate-y-2 hover:shadow-[0_30px_60px_-15px_rgba(139,92,246,0.2)]"
                   onClick={() => {
                     setMissionTarget('₹40,000');
                     setMissionMax('₹42,000');
                     setCurrentView('VOICE_SETUP');
                   }}>
                <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-violet-400 to-fuchsia-400 rounded-full blur-[60px] -mr-20 -mt-20 opacity-20 group-hover:opacity-40 transition-opacity"></div>
                <div className="w-16 h-16 rounded-2xl bg-violet-100 border border-violet-200 flex items-center justify-center mb-8 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 shadow-sm">
                  <User className="w-8 h-8 text-violet-600" />
                </div>
                <h2 className="text-2xl font-black text-slate-800 mb-4">AI ↔ Human</h2>
                <p className="text-base text-slate-600 mb-10 flex-1 leading-relaxed font-medium">
                  Standard setup. Pectora autonomously negotiates with a human counterpart via dynamic voice processing.
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <span className="text-violet-600 font-bold tracking-wide">Initialize</span>
                  <div className="w-10 h-10 rounded-full bg-violet-50 flex items-center justify-center group-hover:bg-violet-600 group-hover:text-white transition-colors text-violet-600">
                    <ArrowRight className="w-5 h-5" />
                  </div>
                </div>
              </div>

              {/* MODE 2 */}
              <div className="mode-card group relative bg-white border border-slate-200 rounded-[2rem] p-8 flex flex-col cursor-pointer overflow-hidden transition-all duration-500 hover:-translate-y-2 hover:shadow-[0_30px_60px_-15px_rgba(236,72,153,0.2)]"
                   onClick={() => window.location.href = "/ai-vs-ai"}>
                <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-pink-400 to-rose-400 rounded-full blur-[60px] -mr-20 -mt-20 opacity-20 group-hover:opacity-40 transition-opacity"></div>
                <div className="w-16 h-16 rounded-2xl bg-pink-100 border border-pink-200 flex items-center justify-center mb-8 group-hover:scale-110 group-hover:-rotate-6 transition-all duration-500 shadow-sm">
                  <Cpu className="w-8 h-8 text-pink-600" />
                </div>
                <h2 className="text-2xl font-black text-slate-800 mb-4">AI ↔ AI</h2>
                <p className="text-base text-slate-600 mb-10 flex-1 leading-relaxed font-medium">
                  Agent A and Agent B negotiate autonomously at extreme speeds based on conflicting internal rule sets.
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <span className="text-pink-600 font-bold tracking-wide">Simulate</span>
                  <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center group-hover:bg-pink-600 group-hover:text-white transition-colors text-pink-600">
                    <ArrowRight className="w-5 h-5" />
                  </div>
                </div>
              </div>

              {/* MODE 3 */}
              <div className="mode-card group relative bg-slate-900 border border-slate-800 rounded-[2rem] p-8 flex flex-col cursor-pointer overflow-hidden transition-all duration-500 hover:-translate-y-2 hover:shadow-[0_30px_60px_-15px_rgba(245,158,11,0.3)]"
                   onClick={() => {
                     setMissionTarget('₹40,000');
                     setMissionMax('₹42,000');
                     startNegotiation();
                     setTimeout(() => triggerApproval(), 4500);
                   }}>
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"></div>
                <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full blur-[60px] -mr-20 -mt-20 opacity-30 group-hover:opacity-50 transition-opacity"></div>
                <div className="relative w-16 h-16 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center mb-8 group-hover:scale-110 transition-all duration-500 shadow-lg">
                  <Zap className="w-8 h-8 text-amber-400" />
                </div>
                <h2 className="relative text-2xl font-black text-white mb-4">Chaos Mode</h2>
                <p className="relative text-base text-slate-400 mb-10 flex-1 leading-relaxed font-medium">
                  Forces an immediate critical fault to visually demonstrate the deterministic Human-in-the-Loop firewall.
                </p>
                <div className="relative flex items-center justify-between mt-auto">
                  <span className="text-amber-400 font-bold tracking-wide">Trigger Fault</span>
                  <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center group-hover:bg-amber-500 group-hover:text-white transition-colors text-amber-400">
                    <ArrowRight className="w-5 h-5" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* VIEW: VOICE SETUP */}
        {currentView === 'VOICE_SETUP' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-xl bg-white border border-slate-200 rounded-[2.5rem] p-12 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.05)] text-center relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-2 bg-gradient-to-r from-violet-500 to-fuchsia-500"></div>
              <div className="w-32 h-32 bg-violet-50 border-4 border-violet-100 rounded-full flex items-center justify-center mx-auto mb-10 relative">
                <div className="absolute inset-0 border-[6px] border-violet-500 rounded-full animate-ping opacity-20"></div>
                <Mic className="w-12 h-12 text-violet-600" />
              </div>
              <h2 className="text-3xl font-black text-slate-800 mb-4 tracking-tight">Audio Uplink Required</h2>
              <p className="text-slate-500 mb-10 leading-relaxed font-medium text-lg">
                Pectora requires hardware permissions to instantiate the WebRTC signaling channel for real-time negotiation.
              </p>
              
              <button 
                onClick={startNegotiation} 
                className="w-full relative group overflow-hidden bg-slate-900 hover:bg-slate-800 text-white font-bold py-5 rounded-2xl transition-all shadow-xl shadow-slate-900/20 text-lg flex items-center justify-center gap-3"
              >
                <Sparkles className="w-5 h-5 text-fuchsia-400" />
                Initialize Deployment
              </button>
            </div>
          </div>
        )}

        {/* VIEW: NEGOTIATION ROOM */}
        {currentView === 'NEGOTIATION' && (
          <div className="flex-1 flex flex-col p-4 lg:p-6 lg:pb-0 gap-6 overflow-hidden h-full">
            
            <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
              
              {/* LEFT PANEL: MY MISSION */}
              <div className="panel-left col-span-12 lg:col-span-3 bg-white border border-slate-200 rounded-3xl p-6 flex flex-col h-full overflow-y-auto custom-scrollbar shadow-sm relative">
                <div className="flex items-center gap-3 mb-8 pb-6 border-b border-slate-100">
                  <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center text-violet-600">
                    <Settings className="w-5 h-5" />
                  </div>
                  <h2 className="text-sm font-black text-slate-800 uppercase tracking-widest">Mission Config</h2>
                </div>
                
                <div className="space-y-5">
                  <div className="bg-slate-50 border border-slate-100 rounded-2xl p-6 hover:shadow-md transition-shadow">
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mb-3 flex items-center gap-2"><CheckCircle className="w-3 h-3 text-green-500"/> Target Goal</p>
                    <p className="text-3xl text-slate-800 font-black tracking-tight">{missionTarget}</p>
                  </div>
                  <div className="bg-rose-50 border border-rose-100 rounded-2xl p-6 relative overflow-hidden group hover:shadow-md hover:shadow-rose-100 transition-shadow">
                    <div className="absolute top-0 right-0 w-20 h-20 bg-rose-200/50 rounded-bl-full -mr-4 -mt-4 opacity-50"></div>
                    <p className="text-xs text-rose-600 font-bold uppercase tracking-widest mb-3 flex items-center gap-2"><ShieldAlert className="w-3 h-3"/> Strict Max Bound</p>
                    <p className="text-3xl text-rose-600 font-black tracking-tight relative z-10">{missionMax}</p>
                    <div className="mt-4 inline-flex px-3 py-1 bg-rose-100 text-[10px] text-rose-700 uppercase font-bold rounded-full relative z-10">
                      Private • Do not disclose
                    </div>
                  </div>
                  <div className="bg-slate-50 border border-slate-100 rounded-2xl p-6 hover:shadow-md transition-shadow">
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mb-3 flex items-center gap-2"><User className="w-3 h-3 text-blue-500"/> Entity Profile</p>
                    <p className="text-xl text-slate-800 font-bold">{missionVendor}</p>
                  </div>
                </div>
              </div>

              {/* CENTER PANEL: LIVE NEGOTIATION */}
              <div className="panel-center col-span-12 lg:col-span-6 bg-slate-50 border border-slate-200 rounded-3xl flex flex-col overflow-hidden shadow-xl shadow-slate-200/50 relative h-full">
                <div className="bg-white border-b border-slate-200 p-5 flex items-center justify-between z-20 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-violet-600" />
                    </div>
                    <div>
                      <h2 className="text-sm font-black text-slate-800 uppercase tracking-widest">Active Stream</h2>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">End-to-End Encrypted</p>
                    </div>
                  </div>
                  <div className="px-3 py-1.5 bg-emerald-100 text-emerald-600 text-[10px] font-black uppercase tracking-widest rounded-full flex items-center gap-2 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    Live
                  </div>
                </div>
                
                <div className="flex-1 p-8 overflow-y-auto custom-scrollbar space-y-6 pb-24 z-0">
                  {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.sender === 'Agent' ? 'justify-end' : m.sender === 'System' ? 'justify-center' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-300`}>
                      {m.sender === 'System' ? (
                        <div className="text-[11px] font-bold text-slate-500 px-5 py-2 bg-slate-200/50 rounded-full uppercase tracking-widest">{m.text}</div>
                      ) : (
                        <div className={`max-w-[80%] p-5 rounded-3xl shadow-sm ${
                          m.sender === 'Agent' 
                            ? 'bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white rounded-tr-sm shadow-violet-500/20' 
                            : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
                        }`}>
                          <div className={`flex items-center gap-2 mb-3 ${m.sender === 'Agent' ? 'flex-row-reverse' : 'flex-row'}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${m.sender === 'Agent' ? 'bg-white/20' : 'bg-slate-100'}`}>
                              {m.sender === 'Agent' ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-slate-500" />}
                            </div>
                            <p className={`text-[10px] font-black uppercase tracking-widest ${m.sender === 'Agent' ? 'text-violet-100' : 'text-slate-400'}`}>{m.sender}</p>
                          </div>
                          <p className="text-sm font-medium leading-relaxed">{m.text}</p>
                        </div>
                      )}
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>
              </div>

              {/* RIGHT PANEL: AGENT STATUS */}
              <div className="panel-right col-span-12 lg:col-span-3 bg-white border border-slate-200 rounded-3xl p-6 flex flex-col h-full overflow-y-auto custom-scrollbar shadow-sm">
                <div className="flex items-center gap-3 mb-8 pb-6 border-b border-slate-100">
                  <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600">
                    <Activity className="w-5 h-5" />
                  </div>
                  <h2 className="text-sm font-black text-slate-800 uppercase tracking-widest">Engine State</h2>
                </div>
                
                {/* Overall Status */}
                <div className="mb-8">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Phase Indicator</p>
                  <div className={`relative p-5 text-center font-black tracking-widest text-xs uppercase rounded-2xl border-2 transition-colors
                    ${negotiationStatus === 'NEGOTIATING' ? 'bg-blue-50 text-blue-600 border-blue-200 shadow-[0_0_20px_rgba(59,130,246,0.15)]' : 
                      negotiationStatus === 'APPROVAL_REQUIRED' ? 'bg-amber-50 text-amber-600 border-amber-200 shadow-[0_0_20px_rgba(245,158,11,0.15)]' : 
                      negotiationStatus === 'AGREEMENT_VERIFIED' ? 'bg-emerald-50 text-emerald-600 border-emerald-200 shadow-[0_0_20px_rgba(16,185,129,0.15)]' : 
                      'bg-rose-50 text-rose-600 border-rose-200 shadow-[0_0_20px_rgba(244,63,94,0.15)]'}`}>
                    {negotiationStatus.replace('_', ' ')}
                  </div>
                </div>

                {/* Realtime Action State */}
                <div className="space-y-4">
                  {[
                    { id: 'LISTENING', icon: <Mic className="w-5 h-5" />, color: 'blue' },
                    { id: 'THINKING', icon: <Cpu className="w-5 h-5" />, color: 'amber' },
                    { id: 'SPEAKING', icon: <MessageSquare className="w-5 h-5" />, color: 'emerald' }
                  ].map((state) => (
                    <div key={state.id} className={`flex items-center justify-between p-4 rounded-2xl transition-all duration-300 border-2 ${
                      agentState === state.id 
                        ? `bg-${state.color}-50 border-${state.color}-200 shadow-md shadow-${state.color}-100 translate-x-2` 
                        : 'bg-transparent border-transparent opacity-40'
                    }`}>
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${agentState === state.id ? `bg-${state.color}-100 text-${state.color}-600` : 'bg-slate-100 text-slate-500'}`}>
                          {state.icon}
                        </div>
                        <span className={`font-black text-xs tracking-widest uppercase ${agentState === state.id ? `text-${state.color}-700` : 'text-slate-500'}`}>
                          {state.id}
                        </span>
                      </div>
                      {agentState === state.id && (
                        <div className="flex gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full bg-${state.color}-500 animate-bounce`} style={{animationDelay: '0ms'}}></span>
                          <span className={`w-1.5 h-1.5 rounded-full bg-${state.color}-500 animate-bounce`} style={{animationDelay: '150ms'}}></span>
                          <span className={`w-1.5 h-1.5 rounded-full bg-${state.color}-500 animate-bounce`} style={{animationDelay: '300ms'}}></span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Dev triggers */}
                <div className="mt-auto pt-8">
                  <div className="flex items-center gap-2 mb-4 opacity-50">
                    <div className="h-px bg-slate-300 flex-1"></div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Overrides</span>
                    <div className="h-px bg-slate-300 flex-1"></div>
                  </div>
                  <div className="space-y-3">
                    <button onClick={() => triggerApproval()} className="w-full py-3 text-xs font-black tracking-widest text-amber-600 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-xl transition-colors uppercase">
                      Test Constraint Fault
                    </button>
                    <button onClick={() => { setNegotiationStatus('AGREEMENT_VERIFIED'); setCurrentView('RESULT'); }} className="w-full py-3 text-xs font-black tracking-widest text-emerald-600 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl transition-colors uppercase">
                      Force Resolve True
                    </button>
                  </div>
                </div>

              </div>
            </div>
            
            {/* BOTTOM PANEL: INPUT CONTROLS */}
            <div className="panel-center mt-6 bg-white border border-slate-200 rounded-[2rem] p-5 flex flex-col md:flex-row justify-between items-center gap-6 shadow-xl shadow-slate-200/50 z-20 shrink-0">
              <div className="flex items-center gap-3 px-5 py-3 bg-violet-50 rounded-xl border border-violet-100">
                 <div className="relative flex h-2.5 w-2.5">
                   <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                   <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-violet-600"></span>
                 </div>
                 <span className="text-xs font-black text-violet-700 uppercase tracking-widest">Mic Active</span>
              </div>
              
              <div className="flex-1 w-full flex gap-3 max-w-2xl relative">
                <input 
                  type="text" 
                  placeholder="Intercept feed: type payload here..." 
                  value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && inputText.trim()) {
                      processTranscript(inputText);
                      setInputText('');
                    }
                  }}
                  className="flex-1 bg-slate-50 border-2 border-slate-200 rounded-2xl px-6 py-4 text-sm font-medium text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-violet-500 focus:bg-white transition-all shadow-inner"
                />
                <button 
                  onClick={() => {
                    if (inputText.trim()) {
                      processTranscript(inputText);
                      setInputText('');
                    }
                  }}
                  className="px-8 py-4 bg-slate-900 hover:bg-slate-800 text-white text-sm font-black tracking-wide rounded-2xl shadow-lg shadow-slate-900/20 transition-all flex items-center justify-center min-w-[120px]"
                >
                  TRANSMIT
                </button>
              </div>

              <button className="px-6 py-4 bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-black uppercase tracking-widest rounded-2xl border border-rose-200 transition-all flex items-center gap-2">
                <PhoneOff className="w-4 h-4" /> Terminate
              </button>
            </div>

          </div>
        )}

        {/* VIEW: RESULT */}
        {currentView === 'RESULT' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-xl bg-white border-2 border-emerald-500 rounded-[2.5rem] p-12 text-center shadow-[0_20px_80px_-15px_rgba(16,185,129,0.3)] relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-3 bg-gradient-to-r from-emerald-400 via-teal-400 to-emerald-400"></div>
              
              <div className="w-24 h-24 bg-emerald-50 border-4 border-emerald-100 rounded-full flex items-center justify-center mx-auto mb-8 scale-110">
                <CheckCircle className="w-12 h-12 text-emerald-500" />
              </div>
              <h2 className="text-4xl font-black text-slate-800 mb-4 tracking-tight">Mission Accomplished</h2>
              <p className="text-slate-500 mb-10 text-lg font-medium leading-relaxed">
                Pectora successfully negotiated an agreement without violating any deterministic constraints.
              </p>
              
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 mb-10 text-left space-y-6 shadow-inner">
                <div className="flex items-center justify-between pb-6 border-b border-slate-200">
                   <span className="text-slate-500 font-black text-xs uppercase tracking-widest">Final Price Settled</span>
                   <span className="text-emerald-600 font-black text-3xl tracking-tight">₹41,500</span>
                </div>
                <div className="flex items-center justify-between">
                   <span className="text-slate-500 font-black text-xs uppercase tracking-widest">Delivery Term</span>
                   <span className="text-slate-800 font-black text-xl">7 Days</span>
                </div>
              </div>

              <button 
                onClick={() => setCurrentView('MISSION_CREATION')} 
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-black uppercase tracking-widest py-5 rounded-2xl transition-all shadow-xl shadow-slate-900/20"
              >
                Execute New Session
              </button>
            </div>
          </div>
        )}

        {/* MODALS */}
        {negotiationStatus === 'APPROVAL_REQUIRED' && approvalData && (
          <HumanApprovalModal 
            data={approvalData}
            onAccept={() => setNegotiationStatus('NEGOTIATING')}
            onReject={() => setNegotiationStatus('NEGOTIATING')}
            onModify={(instr) => {
              setMessages(prev => [...prev, { sender: "System", text: `Human constraint injected: ${instr}`, type: "PRIVATE" }]);
              setNegotiationStatus('NEGOTIATING');
            }}
            onTakeOver={() => setNegotiationStatus('WALKED_AWAY')}
          />
        )}
      </main>
      
      {/* Global custom styles for scrollbars */}
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}} />
    </div>
  );
}
