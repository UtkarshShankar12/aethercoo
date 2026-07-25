import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Shield, TrendingUp, Users, Activity, CheckCircle2, ChevronRight } from 'lucide-react';

const AGENT_INFO = [
  {
    id: 'ceo',
    name: 'CEO Agent',
    role: 'Strategist & Coordinator',
    icon: Users,
    glowClass: 'glow-card-pulse',
    activeColor: '#0052FF',
  },
  {
    id: 'research',
    name: 'Research Agent',
    role: 'Market & Competitor Intel',
    icon: Activity,
    glowClass: 'glow-card-pulse',
    activeColor: '#39FF14',
  },
  {
    id: 'finance',
    name: 'Finance Agent',
    role: 'Quantitative Projections',
    icon: TrendingUp,
    glowClass: 'glow-card-pulse',
    activeColor: '#0052FF',
  },
  {
    id: 'qa',
    name: 'QA Risk Agent',
    role: 'Consistency & Compliance Check',
    icon: Shield,
    glowClass: 'glow-card-pulse-qa',
    activeColor: '#FF007A',
  }
];

export default function AgentPipeline({ activeAgent, agentStates, logs, progress }) {
  const terminalEndRef = useRef(null);

  // Auto-scroll the terminal logs
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const getAgentBadgeColor = (agentId) => {
    switch (agentId) {
      case 'CEO': return 'text-[#0052FF] bg-[#0052FF]/10 border-[#0052FF]/20';
      case 'Research': return 'text-[#39FF14] bg-[#39FF14]/10 border-[#39FF14]/20';
      case 'Finance': return 'text-white bg-white/10 border-white/20';
      case 'QA': return 'text-[#FF007A] bg-[#FF007A]/10 border-[#FF007A]/20';
      default: return 'text-white/50 bg-white/5 border-white/10';
    }
  };

  return (
    <div className="max-w-6xl mx-auto w-full px-6 py-10 space-y-12">
      {/* Page Header */}
      <div className="text-center space-y-3">
        <h2 className="font-display font-extrabold text-4xl md:text-5xl tracking-tight">
          Assembling Executive Reports
        </h2>
        <p className="text-brand-muted text-sm md:text-base max-w-xl mx-auto font-light">
          Watch our virtual executive suite coordinate. Each agent researches, forecasts, and audits recommendations.
        </p>
      </div>

      {/* Connection pipeline and Cards */}
      <div className="relative">
        {/* Animated Connecting Lines for Handoffs */}
        <div className="absolute top-1/2 left-0 w-full h-[2px] bg-white/5 -translate-y-1/2 hidden md:block z-0">
          {/* Animated beam travelling through */}
          {activeAgent && (
            <motion.div
              className="h-full bg-gradient-to-r from-transparent via-[#39FF14] to-transparent w-32"
              animate={{
                left: ['0%', '100%']
              }}
              style={{ position: 'absolute' }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "linear"
              }}
            />
          )}
        </div>

        {/* Pipeline Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
          {AGENT_INFO.map((agent, index) => {
            const status = agentStates[agent.id] || 'idle'; // idle | working | done
            const isWorking = status === 'working';
            const isDone = status === 'done';
            const Icon = agent.icon;

            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.15 }}
                className={`relative p-6 rounded-2xl border bg-brand-card/90 transition-all duration-500 overflow-hidden ${
                  isWorking
                    ? `border-white/20 shadow-lg ${agent.glowClass}`
                    : isDone
                    ? 'border-[#39FF14]/30 shadow-[0_0_15px_rgba(57,255,20,0.06)]'
                    : 'border-white/5 opacity-55'
                }`}
              >
                {/* Floating active background beam */}
                {isWorking && (
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent"
                    animate={{ x: ['-100%', '100%'] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                  />
                )}

                {/* Card Header Info */}
                <div className="flex flex-col items-start gap-4">
                  {/* Icon Container */}
                  <div className={`p-3.5 rounded-xl border ${
                    isWorking 
                      ? 'bg-white/5 border-white/25 text-white' 
                      : isDone 
                      ? 'bg-[#39FF14]/10 border-[#39FF14]/25 text-[#39FF14]' 
                      : 'bg-white/[0.02] border-white/5 text-white/30'
                  }`}>
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-[#39FF14]" />
                    ) : (
                      <Icon className={`w-5 h-5 ${isWorking ? 'animate-pulse' : ''}`} />
                    )}
                  </div>

                  <div className="space-y-1">
                    <h3 className="font-display font-semibold text-lg tracking-tight text-white">
                      {agent.name}
                    </h3>
                    <p className="text-[11px] uppercase tracking-wider text-brand-muted font-medium">
                      {agent.role}
                    </p>
                  </div>
                </div>

                {/* State Badge */}
                <div className="mt-6 flex items-center justify-between text-xs pt-4 border-t border-white/5">
                  <span className="text-brand-muted">Status</span>
                  <span className={`font-semibold ${
                    isWorking 
                      ? 'text-[#39FF14]' 
                      : isDone 
                      ? 'text-[#39FF14]/70' 
                      : 'text-white/30'
                  }`}>
                    {isWorking ? 'Analyzing...' : isDone ? 'Finished' : 'Queued'}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
        <motion.div 
          className="h-full bg-gradient-to-r from-[#0052FF] via-[#39FF14] to-[#FF007A]"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Real-Time Plain English Build Log Terminal */}
      <div className="border border-white/10 rounded-2xl bg-[#0F0F11]/90 shadow-2xl overflow-hidden flex flex-col h-80">
        {/* Terminal Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-[#141417]">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
              <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
              <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
            </div>
            <span className="text-[10px] uppercase tracking-widest text-brand-muted font-semibold pl-2">
              System Execution Log
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-brand-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-[#39FF14] animate-pulse" />
            Live compiler
          </div>
        </div>

        {/* Terminal logs list */}
        <div className="flex-1 overflow-y-auto p-5 font-mono text-xs md:text-sm space-y-3.5 text-left bg-black/40">
          {logs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.15 }}
              className="flex items-start gap-3.5 leading-relaxed"
            >
              {/* Timestamp */}
              <span className="text-white/20 select-none">
                {log.time}
              </span>
              
              {/* Agent Tag */}
              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getAgentBadgeColor(log.agent)}`}>
                {log.agent}
              </span>
              
              {/* Log Message */}
              <span className="text-white/80">
                {log.message}
              </span>
            </motion.div>
          ))}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
