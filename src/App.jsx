import React, { useState, useEffect } from 'react';
import GoalInput from './components/GoalInput';
import AgentPipeline from './components/AgentPipeline';
import FinalReport from './components/FinalReport';
import HistoryView from './components/HistoryView';
import { Terminal, FolderLock, Compass } from 'lucide-react';

export default function App() {
  const [screen, setScreen] = useState('landing'); // landing | executing | report | history
  const [goal, setGoal] = useState('');
  const [activeAgent, setActiveAgent] = useState(null); // ceo | research | finance | qa
  const [agentStates, setAgentStates] = useState({
    ceo: 'idle',
    research: 'idle',
    finance: 'idle',
    qa: 'idle'
  });
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const [reportData, setReportData] = useState(null);
  const [historyList, setHistoryList] = useState([]);

  const BACKEND_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

  // Persistent User ID generation for anonymous Supabase referencing
  const getUserId = () => {
    let userId = localStorage.getItem('aethercoo_user_id');
    if (!userId) {
      userId = '00000000-0000-4000-8000-' + Math.floor(100000000000 + Math.random() * 900000000000);
      try {
        if (window.crypto && window.crypto.randomUUID) {
          userId = window.crypto.randomUUID();
        }
      } catch (e) {}
      localStorage.setItem('aethercoo_user_id', userId);
    }
    return userId;
  };

  const refreshHistory = () => {
    const userId = getUserId();
    fetch(`${BACKEND_URL}/api/runs?user_id=${userId}`)
      .then(r => {
        if (!r.ok) throw new Error("Backend offline");
        return r.json();
      })
      .then(data => {
        const mapped = data.map(item => ({
          id: item.id,
          goal: item.idea_text,
          timestamp: new Date(item.created_at).getTime(),
          trustScore: item.viability_score || 0.0,
          industry: item.status === 'completed' ? 'Completed' : item.status.replace('_', ' ').toUpperCase()
        }));
        setHistoryList(mapped);
      })
      .catch(err => {
        console.warn("Failed to load history list. Backend might be offline.", err);
      });
  };

  // Load history on mount
  useEffect(() => {
    refreshHistory();
  }, []);

  const addLog = (agent, message) => {
    const time = new Date().toLocaleTimeString(undefined, {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    setLogs(prev => [...prev, { time, agent, message }]);
  };

  // Run the multi-agent simulation
  const handleLaunch = async (submittedGoal) => {
    setGoal(submittedGoal);
    setScreen('executing');
    setLogs([]);
    setProgress(0);
    setActiveAgent('ceo');
    setAgentStates({
      ceo: 'working',
      research: 'idle',
      finance: 'idle',
      qa: 'idle'
    });

    const userId = getUserId();

    try {
      const resp = await fetch(`${BACKEND_URL}/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea: submittedGoal, user_id: userId })
      });

      if (!resp.ok) {
        const errJson = await resp.json();
        throw new Error(errJson.detail || "Failed to start validation run.");
      }

      const { run_id } = await resp.json();

      // Connect to websocket stream
      const ws = new WebSocket(`${WS_URL}/api/runs/${run_id}/stream`);

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'log') {
          const msgAgent = message.agent.toLowerCase();
          setActiveAgent(msgAgent);
          
          setAgentStates(prev => {
            const nextStates = { ...prev };
            if (msgAgent === 'ceo') {
              nextStates.ceo = 'working';
            } else if (msgAgent === 'research') {
              nextStates.ceo = 'done';
              nextStates.research = 'working';
            } else if (msgAgent === 'finance') {
              nextStates.ceo = 'done';
              nextStates.research = 'done';
              nextStates.finance = 'working';
            } else if (msgAgent === 'qa') {
              nextStates.ceo = 'done';
              nextStates.research = 'done';
              nextStates.finance = 'done';
              nextStates.qa = 'working';
            }
            return nextStates;
          });

          addLog(message.agent, message.message);
          if (message.progress !== undefined) {
            setProgress(message.progress);
          }
        } 
        
        else if (message.type === 'completed') {
          setAgentStates({
            ceo: 'done',
            research: 'done',
            finance: 'done',
            qa: 'done'
          });
          setActiveAgent(null);
          setProgress(100);

          setReportData(message.dashboard);
          refreshHistory();

          setTimeout(() => {
            setScreen('report');
          }, 1200);

          ws.close();
        } 
        
        else if (message.type === 'failed') {
          addLog('SYSTEM', `❌ Agent Execution Failed: ${message.error}`);
          alert(`Execution failed: ${message.error}`);
          setScreen('landing');
          ws.close();
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket connection error:", err);
      };

      ws.onclose = () => {
        console.info("WebSocket connection closed");
      };

      window._activeWebSocket = ws;

    } catch (e) {
      alert(e.message);
      setScreen('landing');
    }
  };

  const handleFastTrack = () => {
    alert("Live Claude 3.5 executive agents are compiling. Fast-track skip is disabled in production.");
  };

  const handleClearHistory = async () => {
    if (window.confirm("Are you sure you want to delete all archived business goals?")) {
      try {
        for (const item of historyList) {
          await fetch(`${BACKEND_URL}/api/runs/${item.id}`, { method: 'DELETE' });
        }
        setHistoryList([]);
      } catch (e) {
        console.error("Failed to clear history", e);
      }
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col justify-between selection:bg-[#39FF14] selection:text-black">
      
      {/* Top Premium Navbar */}
      <header className="border-b border-white/5 bg-[#0C0C0E]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          
          {/* Logo */}
          <button 
            onClick={() => setScreen('landing')} 
            className="flex items-center gap-2.5 hover:opacity-85 transition-all text-left bg-transparent border-none cursor-pointer"
          >
            <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-[#0052FF] via-[#39FF14] to-[#FF007A] flex items-center justify-center p-[1px]">
              <div className="h-full w-full bg-[#0A0A0B] rounded-lg flex items-center justify-center">
                <span className="font-display font-extrabold text-xs text-white">Æ</span>
              </div>
            </div>
            <div className="leading-none">
              <span className="font-display font-extrabold text-lg text-white tracking-tight">
                Aether<span className="text-white/60">COO</span>
              </span>
            </div>
          </button>

          {/* Navigation links */}
          <nav className="flex items-center gap-4">
            <button
              onClick={() => setScreen('landing')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                screen === 'landing' || screen === 'executing' || screen === 'report'
                  ? 'bg-white/10 text-white'
                  : 'text-brand-muted hover:text-white'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              Launchpad
            </button>
            
            <button
              onClick={() => setScreen('history')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                screen === 'history'
                  ? 'bg-white/10 text-white'
                  : 'text-brand-muted hover:text-white'
              }`}
            >
              <FolderLock className="w-3.5 h-3.5" />
              Archives
              {historyList.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded bg-gradient-to-r from-[#0052FF] to-[#FF007A] text-[9px] font-bold text-white leading-none">
                  {historyList.length}
                </span>
              )}
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col justify-start items-center relative">
        {screen === 'landing' && (
          <GoalInput onSubmit={handleLaunch} />
        )}

        {screen === 'executing' && (
          <div className="w-full relative py-6">
            <AgentPipeline 
              activeAgent={activeAgent} 
              agentStates={agentStates} 
              logs={logs} 
              progress={progress} 
            />
            {/* Fast Track / Skip Action floating helper */}
            <div className="flex justify-center pt-2">
              <span className="text-[11px] text-[#39FF14] font-medium tracking-widest uppercase animate-pulse">
                Running live Claude 3.5 models...
              </span>
            </div>
          </div>
        )}

        {screen === 'report' && (
          <FinalReport 
            reportData={reportData} 
            onStartNew={() => setScreen('landing')} 
          />
        )}

        {screen === 'history' && (
          <HistoryView
            historyList={historyList}
            onViewReport={async (item) => {
              try {
                const resp = await fetch(`${BACKEND_URL}/api/runs/${item.id}`);
                if (!resp.ok) throw new Error("Failed to load archived dashboard details.");
                const fullReport = await resp.json();
                setReportData(fullReport);
                setScreen('report');
              } catch (e) {
                alert(e.message);
              }
            }}
            onClearHistory={handleClearHistory}
            onBackToInput={() => setScreen('landing')}
          />
        )}
      </main>

      {/* Premium Footer */}
      <footer className="border-t border-white/5 py-6 px-6 bg-black/40">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-brand-muted">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-brand-muted" />
            <span>AetherCOO Business Execution Engine (v1.0.4)</span>
          </div>
          <div>
            <span>© 2026 Autonomous Executive Suite. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
