import React, { useState } from 'react';

export interface ApprovalData {
  whatHappened: string;
  currentOffer: any;
  newCondition: string;
  reason: string;
  agentRecommendation: string;
}

interface Props {
  data: ApprovalData;
  onAccept: () => void;
  onReject: () => void;
  onModify: (instruction: string) => void;
  onTakeOver: () => void;
}

export default function HumanApprovalModal({ data, onAccept, onReject, onModify, onTakeOver }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [voiceInput, setVoiceInput] = useState('');
  const [isModifying, setIsModifying] = useState(false);

  const handleVoiceModify = () => {
    // In reality, this hooks into the VAD service / browser microphone
    setIsRecording(true);
    setTimeout(() => {
      setIsRecording(false);
      setVoiceInput("Delivery should be maximum 7 days."); // Mock transcription
    }, 2000);
  };

  const submitModification = () => {
    if (voiceInput) {
      onModify(voiceInput);
      setVoiceInput('');
      setIsModifying(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border-2 border-yellow-500/50 rounded-2xl shadow-2xl shadow-yellow-500/20 max-w-2xl w-full overflow-hidden">
        
        {/* Header */}
        <div className="bg-yellow-500/10 p-6 border-b border-yellow-500/20 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl animate-pulse">⚠️</span>
            <h2 className="text-xl font-bold text-yellow-500 uppercase tracking-widest">Approval Required</h2>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 space-y-6">
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-sm font-bold text-gray-500 uppercase">What Happened</h3>
              <p className="text-white mt-1">{data.whatHappened}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-bold text-gray-500 uppercase">Current Offer</h3>
                <pre className="text-blue-300 mt-1 font-mono text-sm">{JSON.stringify(data.currentOffer, null, 2)}</pre>
              </div>
              <div className="bg-gray-800 rounded-lg p-4 border border-yellow-700/50">
                <h3 className="text-sm font-bold text-yellow-600 uppercase">New Condition</h3>
                <p className="text-yellow-100 mt-1">{data.newCondition}</p>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-sm font-bold text-gray-500 uppercase">Why Approval Is Required</h3>
              <p className="text-white mt-1">{data.reason}</p>
            </div>

            <div className="bg-indigo-900/30 rounded-lg p-4 border border-indigo-500/30">
              <h3 className="text-sm font-bold text-indigo-400 uppercase flex items-center gap-2">
                <span>🤖</span> Agent Recommendation
              </h3>
              <p className="text-indigo-100 mt-1 italic">"{data.agentRecommendation}"</p>
            </div>
          </div>
          
          {/* Modify State */}
          {isModifying && (
            <div className="bg-gray-950 rounded-lg p-4 border border-gray-700 mt-4 animate-fadeIn">
               <h3 className="text-sm font-bold text-gray-400 mb-2">Speak your modification constraint:</h3>
               <div className="flex items-center gap-4">
                 <button 
                   onClick={handleVoiceModify}
                   className={`p-3 rounded-full ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-700 hover:bg-gray-600'} transition-colors`}
                 >
                   🎤
                 </button>
                 <input 
                   type="text" 
                   value={voiceInput}
                   onChange={e => setVoiceInput(e.target.value)}
                   className="flex-1 bg-gray-800 border border-gray-700 rounded p-2 text-white"
                   placeholder={isRecording ? "Listening..." : "Click mic or type..."}
                 />
                 <button onClick={submitModification} disabled={!voiceInput} className="bg-blue-600 px-4 py-2 rounded font-bold disabled:opacity-50">
                   Apply
                 </button>
               </div>
            </div>
          )}

          {/* Action Buttons */}
          {!isModifying && (
            <div className="grid grid-cols-4 gap-4 pt-4">
              <button onClick={onAccept} className="bg-green-600 hover:bg-green-500 text-white font-bold py-3 px-4 rounded-lg transition-colors">
                ACCEPT
              </button>
              <button onClick={() => setIsModifying(true)} className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg transition-colors">
                MODIFY
              </button>
              <button onClick={onReject} className="bg-red-600 hover:bg-red-500 text-white font-bold py-3 px-4 rounded-lg transition-colors">
                REJECT
              </button>
              <button onClick={onTakeOver} className="bg-gray-700 hover:bg-gray-600 border border-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors">
                TAKE OVER
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
