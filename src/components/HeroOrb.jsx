import React from 'react';
import { motion } from 'framer-motion';

export default function HeroOrb({ status = 'idle' }) {
  // Determine animation speeds and scales based on agent execution state
  const isWorking = status === 'working';
  const isDone = status === 'done';

  return (
    <div className="relative w-72 h-72 md:w-96 md:h-96 flex items-center justify-center select-none">
      {/* Outer Chromatic Glow Layer 1 (Electric Blue) */}
      <motion.div
        className="absolute w-5/6 h-5/6 rounded-full bg-gradient-to-tr from-[#0052FF] to-transparent opacity-30 blur-3xl"
        animate={{
          scale: isWorking ? [1, 1.15, 1] : [1, 1.05, 1],
          opacity: isWorking ? [0.3, 0.5, 0.3] : 0.3,
        }}
        transition={{
          duration: isWorking ? 2 : 6,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Outer Chromatic Glow Layer 2 (Vibrant Magenta) */}
      <motion.div
        className="absolute w-4/5 h-4/5 rounded-full bg-gradient-to-bl from-[#FF007A] to-transparent opacity-25 blur-3xl"
        animate={{
          scale: isWorking ? [1, 1.2, 1] : [1, 1.03, 1],
          opacity: isWorking ? [0.25, 0.45, 0.25] : 0.25,
        }}
        transition={{
          duration: isWorking ? 2.5 : 7,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 0.5
        }}
      />

      {/* Outer Chromatic Glow Layer 3 (Neon Lime Green) */}
      <motion.div
        className="absolute w-3/4 h-3/4 rounded-full bg-gradient-to-br from-[#39FF14] to-transparent opacity-20 blur-3xl"
        animate={{
          scale: isWorking ? [1, 1.1, 1] : [1, 1.06, 1],
          opacity: isWorking ? [0.2, 0.4, 0.2] : 0.2,
        }}
        transition={{
          duration: isWorking ? 1.8 : 5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1
        }}
      />

      {/* The Glassmorphic 3D Orb Structure */}
      <motion.div
        className="relative w-64 h-64 md:w-80 md:h-80 rounded-full chromatic-orb glassmorphism flex items-center justify-center overflow-hidden cursor-pointer"
        whileHover={{ scale: 1.04 }}
        animate={{
          y: isWorking ? [0, -8, 0] : [0, -12, 0],
        }}
        transition={{
          duration: isWorking ? 3 : 6,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        {/* Iridescent Chromatic Edge Flare */}
        <div className="absolute inset-0 rounded-full border border-white/10 pointer-events-none" />

        {/* Dynamic Inner Swirling Orbits */}
        <motion.div
          className="absolute w-[90%] h-[90%] rounded-full opacity-60 mix-blend-screen"
          style={{
            background: 'radial-gradient(ellipse at center, rgba(57, 255, 20, 0.15) 0%, transparent 60%)',
          }}
          animate={{
            rotate: isWorking ? 360 : 180,
            scale: isWorking ? [0.95, 1.05, 0.95] : 1
          }}
          transition={{
            rotate: { duration: isWorking ? 8 : 25, repeat: Infinity, ease: "linear" },
            scale: { duration: 4, repeat: Infinity, ease: "easeInOut" }
          }}
        />

        <motion.div
          className="absolute w-[80%] h-[80%] rounded-full opacity-50 mix-blend-color-dodge"
          style={{
            background: 'radial-gradient(circle at 70% 20%, rgba(0, 82, 255, 0.25) 0%, transparent 50%)',
          }}
          animate={{
            rotate: isWorking ? -360 : -180,
          }}
          transition={{
            duration: isWorking ? 12 : 35,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        {/* Center Core Emblem (Changes based on status) */}
        <div className="relative z-10 flex flex-col items-center justify-center text-center">
          {/* Subtle logo/icon in center */}
          <motion.div
            className="w-12 h-12 rounded-full border border-white/15 bg-white/5 backdrop-blur-md flex items-center justify-center shadow-lg"
            animate={{
              boxShadow: isWorking
                ? ["0 0 10px rgba(57, 255, 20, 0.2)", "0 0 25px rgba(0, 82, 255, 0.4)", "0 0 10px rgba(57, 255, 20, 0.2)"]
                : "0 0 10px rgba(255, 255, 255, 0.05)",
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            {isWorking ? (
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#39FF14] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-[#39FF14]"></span>
              </span>
            ) : isDone ? (
              <svg className="w-6 h-6 text-[#39FF14]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <div className="w-2.5 h-2.5 rounded-full bg-white/70" />
            )}
          </motion.div>
          
          <motion.span
            className="text-[10px] tracking-[0.2em] font-display text-white/50 uppercase mt-4 block"
            animate={{ opacity: isWorking ? [0.4, 1, 0.4] : 0.6 }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            {isWorking ? 'Processing' : isDone ? 'Compiled' : 'Aether Engine'}
          </motion.span>
        </div>

        {/* High Gloss Reflection highlight */}
        <div 
          className="absolute top-2 left-10 w-2/3 h-1/3 rounded-full pointer-events-none opacity-40"
          style={{
            background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0) 100%)',
            transform: 'rotate(-15deg)',
            filter: 'blur(1px)'
          }}
        />
        
        {/* Soft bottom crescent shadow/reflection */}
        <div 
          className="absolute bottom-4 right-10 w-1/2 h-1/4 rounded-full pointer-events-none opacity-20"
          style={{
            background: 'linear-gradient(to top, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0) 100%)',
            transform: 'rotate(15deg)',
            filter: 'blur(2px)'
          }}
        />
      </motion.div>
    </div>
  );
}
