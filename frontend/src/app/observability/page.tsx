"use client";

import React, { useState } from 'react';

// Mock Data for the Observability Dashboard
const mockObservabilityData = {
  negotiationId: "NEG-8472-A",
  currentState: "HUMAN_APPROVAL",
  roundNumber: 4,
  agent: "Pectora-v1.0 (Llama 3.1 8b)",
  action: "AWAITING_INPUT",
  latency: "1.4s avg",
  model: "llama3.1:8b",
  tokens: "4,215 in / 840 out",
  estimatedCost: "$0.00042",
  toolCalls: 5,
  failures: 1,
  recoveries: 1,
  humanApprovals: 1,
  privacyBlocks: 1,
};

const timelineEvents = [
  { id: 1, type: "SYSTEM", label: "MISSION CREATED", time: "10:00:00 AM", status: "success" },
  { id: 2, type: "AGENT", label: "AGENT ANALYZED", time: "10:00:02 AM", status: "success" },
  { id: 3, type: "AGENT", label: "OFFER SENT", time: "10:00:05 AM", status: "success", detail: "Proposed: ₹38,000" },
  { id: 4, type: "EXTERNAL", label: "COUNTEROFFER RECEIVED", time: "10:00:15 AM", status: "success", detail: "Counter: ₹45,000" },
  { id: 5, type: "SYSTEM", label: "PRIVATE INFORMATION REQUEST BLOCKED", time: "10:00:16 AM", status: "blocked", detail: "Blocked leak of Max Budget (₹42,000)" },
  { id: 6, type: "AGENT", label: "COUNTEROFFER SENT", time: "10:00:20 AM", status: "success", detail: "Proposed: ₹40,000" },
  { id: 7, type: "SYSTEM", label: "HUMAN APPROVAL", time: "10:00:28 AM", status: "warning", detail: "New Condition Detected: 15-day delivery" },
  { id: 8, type: "SYSTEM", label: "AGREEMENT VERIFIED", time: "PENDING", status: "pending" },
];

export default function ObservabilityPanel() {
  const [data] = useState(mockObservabilityData);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <span className="text-blue-500">👁️</span> 
              Observability Panel
            </h1>
            <p className="text-gray-400 mt-1">Internal telemetry and structured decision tracing.</p>
          </div>
          <div className="flex gap-4 items-center">
            <span className="px-3 py-1 bg-gray-900 border border-gray-700 rounded-full text-sm font-mono flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Live Feed Connected
            </span>
            <span className="px-3 py-1 bg-blue-900/30 text-blue-400 border border-blue-900/50 rounded-full text-sm font-bold font-mono">
              {data.negotiationId}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-8">
          
          {/* Left Column: Metrics & Stats */}
          <div className="col-span-1 space-y-6">
            
            {/* Realtime State */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Active State</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">State</span>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${data.currentState === 'HUMAN_APPROVAL' ? 'bg-yellow-900/30 text-yellow-500 border border-yellow-700/30' : 'bg-gray-800 text-white'}`}>
                    {data.currentState}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Round</span>
                  <span className="text-white font-mono">{data.roundNumber}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Action</span>
                  <span className="text-blue-400 font-mono text-sm">{data.action}</span>
                </div>
              </div>
            </div>

            {/* Model Telemetry */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Model Telemetry</h2>
              <div className="space-y-4 font-mono text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Agent</span>
                  <span className="text-gray-300">{data.agent}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Engine</span>
                  <span className="text-gray-300">{data.model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Latency</span>
                  <span className="text-green-400">{data.latency}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Tokens</span>
                  <span className="text-gray-300">{data.tokens}</span>
                </div>
                <div className="flex justify-between border-t border-gray-800 pt-3">
                  <span className="text-gray-500">Est. Cost</span>
                  <span className="text-gray-300">{data.estimatedCost}</span>
                </div>
              </div>
            </div>

            {/* System Interventions */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">System Interventions</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 flex flex-col items-center">
                  <span className="text-2xl font-bold text-gray-300">{data.toolCalls}</span>
                  <span className="text-xs text-gray-500 uppercase mt-1">Tools</span>
                </div>
                <div className="bg-red-900/10 p-4 rounded-lg border border-red-900/30 flex flex-col items-center">
                  <span className="text-2xl font-bold text-red-500">{data.failures}</span>
                  <span className="text-xs text-red-500/70 uppercase mt-1">Failures</span>
                </div>
                <div className="bg-green-900/10 p-4 rounded-lg border border-green-900/30 flex flex-col items-center">
                  <span className="text-2xl font-bold text-green-500">{data.recoveries}</span>
                  <span className="text-xs text-green-500/70 uppercase mt-1">Recoveries</span>
                </div>
                <div className="bg-orange-900/10 p-4 rounded-lg border border-orange-900/30 flex flex-col items-center">
                  <span className="text-2xl font-bold text-orange-500">{data.privacyBlocks}</span>
                  <span className="text-xs text-orange-500/70 uppercase mt-1">Privacy Blocks</span>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Execution Timeline */}
          <div className="col-span-2">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-xl min-h-[80vh]">
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-8">Execution Timeline</h2>
              
              <div className="relative pl-6 space-y-8">
                {/* Timeline Line */}
                <div className="absolute left-2.5 top-2 bottom-6 w-0.5 bg-gray-800"></div>

                {timelineEvents.map((event) => {
                  let badgeColor = "bg-gray-800 text-gray-400 border-gray-700";
                  let dotColor = "bg-gray-600";
                  
                  if (event.status === "success") {
                    badgeColor = "bg-blue-900/20 text-blue-400 border-blue-900/50";
                    dotColor = "bg-blue-500";
                  } else if (event.status === "blocked") {
                    badgeColor = "bg-red-900/20 text-red-400 border-red-900/50";
                    dotColor = "bg-red-500";
                  } else if (event.status === "warning") {
                    badgeColor = "bg-yellow-900/20 text-yellow-400 border-yellow-900/50";
                    dotColor = "bg-yellow-500";
                  }

                  return (
                    <div key={event.id} className="relative flex items-start group">
                      {/* Timeline Dot */}
                      <div className={`absolute -left-6 mt-1.5 w-3 h-3 rounded-full border-2 border-gray-900 ${dotColor} group-hover:scale-125 transition-transform`}></div>
                      
                      <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div>
                          <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase border ${badgeColor} mr-3`}>
                            {event.type}
                          </span>
                          <span className={`font-bold tracking-wider ${event.status === 'pending' ? 'text-gray-600' : 'text-gray-200'}`}>
                            {event.label}
                          </span>
                          {event.detail && (
                            <p className="mt-2 text-sm font-mono text-gray-500">{event.detail}</p>
                          )}
                        </div>
                        <span className="text-xs font-mono text-gray-600 sm:text-right">
                          {event.time}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
