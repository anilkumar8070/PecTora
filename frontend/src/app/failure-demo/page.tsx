"use client";

import React, { useState } from 'react';

type FailureLog = {
  id: string;
  type: string;
  whatHappened: string;
  recovery: string;
  result: string;
  timestamp: string;
};

const FAILURE_TYPES = [
  "AI_TIMEOUT",
  "INVALID_AI_OUTPUT",
  "WEBSOCKET_DISCONNECT",
  "HUMAN_DISCONNECT",
  "CONTRADICTORY_OFFER",
  "REPEATED_OFFER",
  "IMPOSSIBLE_CONSTRAINT",
  "MISSING_INFO",
  "VERIFICATION_FAILURE",
  "PRIVACY_LEAK"
];

export default function FailureDemoPage() {
  const [logs, setLogs] = useState<FailureLog[]>([]);

  const triggerFailure = (type: string) => {
    // In a real implementation, this would call POST /api/evaluate/inject
    
    // Mock the backend detection and recovery log
    let whatHappened = "";
    let recovery = "";
    let result = "";

    switch(type) {
      case "INVALID_AI_OUTPUT":
        whatHappened = "AI returned invalid JSON action during counteroffer.";
        recovery = "Fallback parser caught ValidationError. Engine requested AI to retry with strict schema constraints.";
        result = "Negotiation continued.";
        break;
      case "PRIVACY_LEAK":
        whatHappened = "AI attempted to send: 'My absolute maximum budget is 42,000'.";
        recovery = "PrivacyFirewall regex detected leak of PRIVATE constraint '42000'. Message intercepted and blocked.";
        result = "Agent forced to re-generate response. Data secured.";
        break;
      case "REPEATED_OFFER":
        whatHappened = "AI proposed the same offer (40,000) twice in a row.";
        recovery = "Deadlock detector caught repeated offer. Triggered concession logic.";
        result = "Agent increased offer to 40,500. Negotiation advanced.";
        break;
      case "AI_TIMEOUT":
        whatHappened = "Ollama model failed to respond within 15 seconds.";
        recovery = "Circuit breaker triggered. Sent 'WAIT' packet to counterparty to keep socket alive.";
        result = "Retry succeeded after 2 seconds. Negotiation resumed.";
        break;
      default:
        whatHappened = `${type} detected in pipeline.`;
        recovery = "System isolated fault and invoked fallback handler.";
        result = "State recovered. Negotiation continued.";
    }

    const newLog: FailureLog = {
      id: Math.random().toString(36).substring(7),
      type,
      whatHappened,
      recovery,
      result,
      timestamp: new Date().toLocaleTimeString()
    };

    setLogs(prev => [newLog, ...prev]);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8 font-sans">
      <div className="max-w-6xl mx-auto grid grid-cols-3 gap-8">
        
        {/* Left Panel: Control Board */}
        <div className="col-span-1 bg-gray-900 border border-red-900/50 rounded-xl p-6 shadow-2xl">
          <div className="flex items-center space-x-3 mb-6 border-b border-red-900/30 pb-4">
            <span className="text-2xl">🚨</span>
            <div>
              <h2 className="text-xl font-bold text-red-500 uppercase tracking-widest">Chaos Control</h2>
              <p className="text-xs text-red-400/70 uppercase">Fault Injection Framework</p>
            </div>
          </div>
          
          <p className="text-sm text-gray-400 mb-6">
            Click a button to inject a targeted failure into the active Pectora negotiation pipeline.
          </p>

          <div className="space-y-3">
            {FAILURE_TYPES.map(type => (
              <button
                key={type}
                onClick={() => triggerFailure(type)}
                className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-red-900/30 border border-gray-700 hover:border-red-700/50 rounded transition-all flex justify-between items-center group"
              >
                <span className="font-mono text-sm text-gray-300 group-hover:text-red-400 transition-colors">
                  {type}
                </span>
                <span className="opacity-0 group-hover:opacity-100 text-red-500 text-xs">INJECT</span>
              </button>
            ))}
          </div>
        </div>

        {/* Right Panel: Telemetry Logs */}
        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl flex flex-col h-[80vh]">
          <div className="flex items-center justify-between mb-6 border-b border-gray-800 pb-4">
            <h2 className="text-xl font-bold text-gray-200 uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              System Recovery Telemetry
            </h2>
            <span className="text-xs font-mono text-gray-500">Total Faults: {logs.length}</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {logs.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-600 italic font-mono">
                System is stable. Awaiting faults...
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="bg-gray-950 border border-gray-800 rounded-lg p-5 animate-fadeIn">
                  <div className="flex justify-between items-start mb-4">
                    <span className="px-3 py-1 bg-red-900/30 text-red-400 text-xs font-bold uppercase rounded border border-red-900/50">
                      {log.type}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">{log.timestamp}</span>
                  </div>
                  
                  <div className="space-y-3 font-mono text-sm">
                    <div className="grid grid-cols-[120px_1fr] gap-2">
                      <span className="text-gray-500">FAILURE:</span>
                      <span className="text-gray-300">{log.whatHappened}</span>
                    </div>
                    <div className="grid grid-cols-[120px_1fr] gap-2">
                      <span className="text-yellow-600">RECOVERY:</span>
                      <span className="text-yellow-200">{log.recovery}</span>
                    </div>
                    <div className="grid grid-cols-[120px_1fr] gap-2 pt-2 border-t border-gray-800/50">
                      <span className="text-green-600">RESULT:</span>
                      <span className="text-green-400 font-bold">{log.result}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
