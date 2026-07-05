"use client";

import { useState } from "react";
import { Send, Cpu, Cloud, Zap, Network } from "lucide-react";
import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer } from "recharts";
import { motion, AnimatePresence } from "framer-motion";

const initialGraphData = [
  { time: "10:00", local: 0, cloud: 0 },
  { time: "10:05", local: 450, cloud: 120 },
];

export default function CommandNexus() {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [isRouting, setIsRouting] = useState(false);
  const [tokensSaved, setTokensSaved] = useState(450);
  const [avgLatency, setAvgLatency] = useState(112);
  const [graphData, setGraphData] = useState(initialGraphData);
  const [auditLog, setAuditLog] = useState<any[]>([]);

  const handleExecute = () => {
    if (!prompt.trim()) return;
    
    setMessages(prev => [...prev, { role: "user", content: prompt }]);
    setIsRouting(true);
    setPrompt("");
    
    setTimeout(() => {
      const isComplex = prompt.length > 50 || prompt.toLowerCase().includes("analyze");
      
      const mockApiResponse = {
        task_id: `req_${Math.random().toString(36).substring(2, 8)}`,
        route_decision: {
          target: isComplex ? "cloud" : "local",
          reason: isComplex ? "High complexity keyword detected." : "Task complexity is low. Routing to Edge.",
        },
        execution: {
          model_used: isComplex ? "fireworks/llama-v3-70b-instruct" : "ollama/llama3-8b",
          response_text: isComplex 
            ? "Cloud execution complete. Massive datasets analyzed via Fireworks AI on AMD Hardware."
            : "Local execution complete. Handled securely on zero-cost edge node.",
          latency_ms: isComplex ? 1204.5 : 412.5
        },
        metrics: {
          estimated_cloud_cost_tokens: 150,
          actual_paid_tokens: isComplex ? 150 : 0,
          tokens_saved: isComplex ? 0 : 150
        }
      };

      setMessages(prev => [...prev, { role: "ai", content: mockApiResponse.execution.response_text, route: mockApiResponse.route_decision.target }]);
      setTokensSaved(prev => prev + mockApiResponse.metrics.tokens_saved);
      setAvgLatency(mockApiResponse.execution.latency_ms);
      setAuditLog(prev => [mockApiResponse, ...prev].slice(0, 5));
      
      const timeNow = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      setGraphData(prev => [...prev, { 
        time: timeNow, 
        local: mockApiResponse.route_decision.target === 'local' ? mockApiResponse.metrics.estimated_cloud_cost_tokens : 0, 
        cloud: mockApiResponse.metrics.actual_paid_tokens 
      }]);

      setIsRouting(false);
    }, 1500);
  };

  return (
    <div className="grid grid-cols-12 gap-6 h-[calc(100vh-8rem)]">
      <div className="col-span-8 flex flex-col bg-[#171717] border border-[#262626] rounded-xl shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-[#262626] bg-[#0A0A0A]/50 flex justify-between items-center">
          <span className="text-xs font-semibold text-[#A3A3A3] uppercase tracking-wider">Agent Execution Terminal</span>
          <div className="flex gap-3">
            <span className="text-[10px] bg-blue-500/10 text-blue-500 px-2 py-1 rounded border border-blue-500/20 flex items-center gap-1 font-medium">
              <Cpu className="w-3 h-3" /> OLLAMA EDGE
            </span>
            <span className="text-[10px] bg-red-500/10 text-red-500 px-2 py-1 rounded border border-red-500/20 flex items-center gap-1 font-medium">
              <Cloud className="w-3 h-3" /> AMD CLOUD
            </span>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-[#A3A3A3]">
              <Network className="w-8 h-8 mb-4 opacity-50" />
              <p className="text-sm">RouteIQ Engine standing by. Input prompt below.</p>
            </div>
          )}
          <AnimatePresence>
            {messages.map((msg, idx) => (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-[85%] p-4 rounded-xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none shadow-lg shadow-blue-500/10' : 'bg-[#0A0A0A] border border-[#262626] rounded-bl-none'}`}>
                  {msg.content}
                </div>
                {msg.role === 'ai' && (
                  <div className="flex items-center gap-1.5 mt-2 text-[11px] text-[#A3A3A3] ml-1">
                    Routed via: <span className={msg.route === 'cloud' ? 'text-red-500 font-bold' : 'text-blue-500 font-bold'}>
                      {msg.route === 'cloud' ? 'Fireworks AI (Paid)' : 'Local Node (Zero Cost)'}
                    </span>
                  </div>
                )}
              </motion.div>
            ))}
            {isRouting && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 text-[#A3A3A3] text-sm p-4">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                Evaluating Complexity & Routing...
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-4 bg-[#0A0A0A]/50 border-t border-[#262626]">
          <div className="relative flex items-center">
            <input 
              value={prompt} onChange={(e) => setPrompt(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
              placeholder="Enter task (Short = Local, Long/Analyze = Cloud)..."
              className="w-full bg-[#171717] border border-[#262626] text-white text-sm rounded-lg pl-4 pr-12 py-3.5 focus:outline-none focus:border-blue-500 transition-all placeholder:text-[#A3A3A3]/50"
            />
            <button onClick={handleExecute} className="absolute right-2 p-2 bg-blue-600 hover:bg-blue-500 rounded-md text-white transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="col-span-4 flex flex-col gap-6 h-full">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-[#171717] border border-[#262626] p-5 rounded-xl shadow-lg">
            <div className="text-[#A3A3A3] text-xs font-medium mb-2 uppercase tracking-wider">Tokens Saved</div>
            <div className="text-3xl font-bold text-white flex items-center gap-2">
              {tokensSaved} <Zap className="w-5 h-5 text-green-500" />
            </div>
          </div>
          <div className="bg-[#171717] border border-[#262626] p-5 rounded-xl shadow-lg">
            <div className="text-[#A3A3A3] text-xs font-medium mb-2 uppercase tracking-wider">Last Latency</div>
            <div className="text-3xl font-bold text-white">{avgLatency}ms</div>
          </div>
        </div>

        <div className="bg-[#171717] border border-[#262626] p-5 rounded-xl shadow-lg flex-1 flex flex-col min-h-0">
          <div className="text-xs font-semibold mb-6 text-[#A3A3A3] uppercase tracking-wider">Routing Distribution</div>
          <div className="flex-1 w-full h-full min-h-[150px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={graphData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <Tooltip contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid #262626', borderRadius: '8px' }} />
                <XAxis dataKey="time" stroke="#525252" fontSize={10} tickLine={false} axisLine={false} />
                <Line type="monotone" dataKey="local" stroke="#3B82F6" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="cloud" stroke="#ED1C24" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-[#171717] border border-[#262626] p-5 rounded-xl shadow-lg flex-1 overflow-hidden flex flex-col min-h-[200px]">
          <div className="text-xs font-semibold mb-4 text-[#A3A3A3] uppercase tracking-wider">Execution Audit Trace</div>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {auditLog.length === 0 && <span className="text-xs text-[#A3A3A3]">No logs yet.</span>}
            {auditLog.map((log) => (
              <div key={log.task_id} className="flex justify-between items-center text-sm p-3 rounded-lg bg-[#0A0A0A]/50 border border-[#262626]/50">
                <div>
                  <div className="text-white font-medium text-xs">{log.task_id}</div>
                  <div className={`text-[10px] mt-1 ${log.route_decision.target === 'cloud' ? 'text-red-400' : 'text-blue-400'}`}>
                    {log.execution.model_used}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-green-400 font-medium text-[11px]">{log.metrics.tokens_saved} saved</div>
                  <div className="text-[10px] text-[#A3A3A3] mt-1">{log.execution.latency_ms}ms</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
