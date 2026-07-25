import React from 'react';
import { Calendar, ArrowRight, ShieldCheck, Trash2, LayoutGrid } from 'lucide-react';

export default function HistoryView({ historyList, onViewReport, onClearHistory, onBackToInput }) {
  const isEmpty = historyList.length === 0;

  return (
    <div className="max-w-5xl mx-auto w-full px-6 py-10 space-y-8 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/5">
        <div>
          <span className="text-[10px] font-semibold tracking-widest text-[#0052FF] uppercase block">
            Archived Runs
          </span>
          <h2 className="font-display font-extrabold text-2xl md:text-3xl tracking-tight text-white mt-1">
            Engine Archives
          </h2>
        </div>
        
        {!isEmpty && (
          <button
            onClick={onClearHistory}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-500/10 hover:border-red-500/35 bg-red-500/[0.02] hover:bg-red-500/[0.08] text-xs font-semibold transition-all cursor-pointer text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Wipe Archives
          </button>
        )}
      </div>

      {isEmpty ? (
        /* Empty State */
        <div className="border border-white/5 bg-brand-card/30 rounded-3xl p-16 text-center space-y-6 flex flex-col items-center justify-center">
          <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 text-white/20">
            <LayoutGrid className="w-10 h-10" />
          </div>
          <div className="space-y-2">
            <h3 className="font-display font-bold text-xl text-white">No compiled goals yet</h3>
            <p className="text-sm text-brand-muted max-w-sm mx-auto font-light leading-relaxed">
              Initialize your first multi-agent research sprint from the main console to archive insights here.
            </p>
          </div>
          <button
            onClick={onBackToInput}
            className="bg-white hover:bg-white/90 text-black px-6 py-3 rounded-xl text-xs font-semibold flex items-center gap-2 hover:scale-[1.02] transition-all cursor-pointer"
          >
            Launch Command Bar
            <ArrowRight className="w-4 h-4 text-black" />
          </button>
        </div>
      ) : (
        /* Grid list of history cards */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {historyList.map((item, idx) => {
            const dateStr = new Date(item.timestamp).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });

            return (
              <div
                key={item.id || idx}
                className="group relative p-6 rounded-2xl border border-white/5 bg-brand-card/75 hover:bg-brand-card transition-all duration-300 flex flex-col justify-between space-y-6 hover:border-white/10"
              >
                {/* Info */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between gap-2">
                    {/* Timestamp */}
                    <div className="flex items-center gap-1.5 text-xs text-brand-muted">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{dateStr}</span>
                    </div>

                    {/* Trust Rating Badge */}
                    <div className="flex items-center gap-1 px-2 py-0.5 rounded border border-[#FF007A]/20 bg-[#FF007A]/5 text-[10px] font-semibold text-[#FF007A]">
                      <ShieldCheck className="w-3 h-3" />
                      <span>{item.trustScore}% Score</span>
                    </div>
                  </div>

                  {/* Goal title */}
                  <h3 className="font-display font-bold text-lg text-white leading-snug line-clamp-2">
                    "{item.goal}"
                  </h3>

                  {/* Vertical Tag */}
                  <span className="inline-block text-[10px] font-semibold tracking-wider text-[#39FF14] bg-[#39FF14]/10 border border-[#39FF14]/15 px-2 py-0.5 rounded uppercase">
                    {item.industry}
                  </span>
                </div>

                {/* Footer action */}
                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-[10px] uppercase text-brand-muted tracking-wider">
                    Execution Archived
                  </span>
                  
                  <button
                    onClick={() => onViewReport(item)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-white group-hover:text-[#39FF14] transition-all cursor-pointer"
                  >
                    Recall Report
                    <ArrowRight className="w-3.5 h-3.5 transform group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
