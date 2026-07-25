import React, { useState } from 'react';
import HeroOrb from './HeroOrb';
import { ArrowRight, Sparkles, Terminal } from 'lucide-react';

const EXAMPLES = [
  "Launch a subscription box for premium organic Matcha tea targeted at Gen-Z remote workers",
  "Build a local micro-brewery with craft cider delivery and real-time taproom availability app in Austin",
  "Create a B2B SaaS platform for automated medical billing compliance using AI agents"
];

export default function GoalInput({ onSubmit }) {
  const [goal, setGoal] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (goal.trim()) {
      onSubmit(goal);
    }
  };

  const handleChipClick = (example) => {
    setGoal(example);
  };

  return (
    <div className="relative min-h-[85vh] flex flex-col justify-center items-center px-6 py-12 md:py-20 max-w-7xl mx-auto w-full overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center w-full">
        {/* Left Side: Copy and Input */}
        <div className="lg:col-span-7 flex flex-col justify-center text-left space-y-8 z-10">
          <div className="space-y-4">
            {/* Micro-copy badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/5 bg-white/5 backdrop-blur-md text-[11px] font-medium tracking-[0.2em] text-[#39FF14] uppercase">
              <Sparkles className="w-3.5 h-3.5 text-[#39FF14]" />
              Autonomous Business Engine
            </div>
            
            {/* Bold Oversized Display Typography */}
            <h1 className="font-display font-extrabold text-5xl md:text-7xl leading-[1.05] tracking-[-0.04em] text-white">
              Tell it your goal.<br/>
              Watch it build the <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#0052FF] via-[#39FF14] to-[#FF007A]">business.</span>
            </h1>
            
            {/* Micro-copy under bold headline */}
            <p className="text-[#8A8A8E] text-base md:text-lg max-w-xl font-light leading-relaxed">
              Submit a natural language objective. Our autonomous team of virtual executives will research market dynamics, project financials, and run QA risk matrices in real-time.
            </p>
          </div>

          {/* Form Input (Command Bar Style) */}
          <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl w-full">
            <div 
              className={`relative flex items-center p-2 rounded-2xl border transition-all duration-300 ${
                isFocused 
                  ? 'border-[#0052FF]/60 shadow-[0_0_20px_rgba(0,82,255,0.15)] bg-[#111113]' 
                  : 'border-white/10 bg-[#161618]/60'
              }`}
            >
              <div className="pl-4 pr-2 text-white/40 flex items-center justify-center">
                <Terminal className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder="What startup goal are you planning today?"
                className="w-full py-4 px-2 bg-transparent text-white placeholder-white/30 border-none outline-none font-body text-base md:text-lg"
                required
              />
              <button
                type="submit"
                className="bg-white hover:bg-white/90 text-black px-6 py-4 rounded-xl font-semibold flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer shadow-lg shadow-white/5"
              >
                Launch
                <ArrowRight className="w-4 h-4 text-black" />
              </button>
            </div>

            {/* Example Goal Chips */}
            <div className="space-y-2.5">
              <span className="text-[10px] font-semibold tracking-widest text-[#8A8A8E] uppercase block">
                Quick-Start Suggestions
              </span>
              <div className="flex flex-col gap-2">
                {EXAMPLES.map((example, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleChipClick(example)}
                    className="text-left w-full text-xs md:text-sm text-[#8A8A8E] hover:text-white px-4 py-2.5 rounded-xl border border-white/5 hover:border-white/15 bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-200 truncate cursor-pointer font-body"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </form>
        </div>

        {/* Right Side: Signature Hero Object */}
        <div className="lg:col-span-5 flex justify-center items-center z-0 lg:pl-8">
          <div className="relative animate-float">
            <HeroOrb status="idle" />
          </div>
        </div>
      </div>
    </div>
  );
}
