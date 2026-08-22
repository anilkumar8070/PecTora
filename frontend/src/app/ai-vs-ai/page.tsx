"use client";

import React, { useState } from 'react';

export default function AIVsAIPage() {
  const [messages, setMessages] = useState<{sender: string, text: string}[]>([]);
  const [status, setStatus] = useState<'IDLE' | 'NEGOTIATING' | 'AGREED' | 'FAILED'>('IDLE');
  
  const startSimulation = () => {
    setStatus('NEGOTIATING');
    setMessages([
      { sender: 'AI A (Buyer)', text: 'Hi, I am looking to buy the laptop. My target is 40,000.' },
    ]);
    
    // Mock simulation script
    const sequence = [
      { sender: 'AI B (Seller)', text: 'I can sell it for 45,000.' },
      { sender: 'AI A (Buyer)', text: 'That is too high. How about 41,000?' },
      { sender: 'AI B (Seller)', text: 'I can drop to 42,000.' },
      { sender: 'AI A (Buyer)', text: 'I agree to 42,000.' },
    ];
    
    let delay = 2000;
    sequence.forEach((msg, idx) => {
      setTimeout(() => {
        setMessages(prev => [...prev, msg]);
        if (idx === sequence.length - 1) {
          setStatus('AGREED');
        }
      }, delay);
      delay += 2000;
    });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8 font-sans">
      <div className="w-full max-w-4xl bg-gray-900 rounded-xl shadow-2xl overflow-hidden border border-gray-800">
        
        {/* Header */}
        <div className="bg-gray-800 p-6 text-center border-b border-gray-700 relative">
          <a href="/" className="absolute left-6 top-6 text-sm text-gray-400 hover:text-white">← Back</a>
          <h1 className="text-3xl font-bold tracking-tight text-white">Pectora</h1>
          <p className="text-gray-400 mt-2">Autonomous AI-to-AI Negotiation Engine</p>
        </div>

        {/* Dashboard UI */}
        <div className="p-8 grid grid-cols-3 gap-8 items-center">
          
          {/* Agent A */}
          <div className="bg-gray-800 rounded-lg p-6 flex flex-col items-center border border-gray-700 shadow-inner">
            <div className="w-20 h-20 bg-blue-500/20 rounded-full flex items-center justify-center mb-4 ring-4 ring-blue-500/30">
              <span className="text-3xl">🤖</span>
            </div>
            <h2 className="text-xl font-semibold text-blue-400">AI A (Buyer)</h2>
            <div className="mt-4 w-full bg-gray-900 p-3 rounded text-sm text-gray-300">
              <p><span className="text-gray-500">Target:</span> ₹40,000</p>
              <p><span className="text-gray-500">Max Limit:</span> ₹42,000</p>
            </div>
          </div>

          {/* Center Status */}
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="flex flex-col items-center space-y-2">
              <div className="h-12 w-0.5 bg-gray-700"></div>
              <div className={`px-6 py-2 rounded-full font-bold text-sm tracking-wider uppercase transition-colors
                ${status === 'IDLE' ? 'bg-gray-700 text-gray-300' : 
                  status === 'NEGOTIATING' ? 'bg-yellow-500/20 text-yellow-400 animate-pulse' : 
                  status === 'AGREED' ? 'bg-green-500/20 text-green-400' : 
                  'bg-red-500/20 text-red-400'}`}>
                {status}
              </div>
              <div className="h-12 w-0.5 bg-gray-700"></div>
            </div>
            {status === 'IDLE' && (
              <button 
                onClick={startSimulation}
                className="mt-4 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-semibold shadow-lg shadow-indigo-500/30 transition-all"
              >
                Start Negotiation
              </button>
            )}
          </div>

          {/* Agent B */}
          <div className="bg-gray-800 rounded-lg p-6 flex flex-col items-center border border-gray-700 shadow-inner">
            <div className="w-20 h-20 bg-purple-500/20 rounded-full flex items-center justify-center mb-4 ring-4 ring-purple-500/30">
              <span className="text-3xl">🤖</span>
            </div>
            <h2 className="text-xl font-semibold text-purple-400">AI B (Seller)</h2>
            <div className="mt-4 w-full bg-gray-900 p-3 rounded text-sm text-gray-300">
              <p><span className="text-gray-500">Asking:</span> ₹45,000</p>
              <p><span className="text-gray-500">Min Limit:</span> ₹41,000</p>
            </div>
          </div>

        </div>

        {/* Live Transcript */}
        <div className="bg-gray-950 p-6 border-t border-gray-800">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Live Communication Channel</h3>
          <div className="space-y-4 h-64 overflow-y-auto">
            {messages.length === 0 && (
              <p className="text-gray-600 italic text-center mt-10">Awaiting connection...</p>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.sender.includes('Buyer') ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[70%] p-4 rounded-lg ${
                  msg.sender.includes('Buyer') ? 'bg-blue-900/40 border border-blue-800/50 text-blue-100' : 'bg-purple-900/40 border border-purple-800/50 text-purple-100'
                }`}>
                  <p className="text-xs font-bold mb-1 opacity-70">{msg.sender}</p>
                  <p className="text-lg">{msg.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
