'use client';

import { motion } from 'framer-motion';

export function AIThinking({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="relative w-16 h-16">
        <motion.div
          className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 opacity-50"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 0.8, 0.5],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute inset-2 rounded-full bg-gradient-to-r from-purple-600 to-pink-600"
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      </div>
      <div className="text-center space-y-2">
        <p className="text-sm font-medium text-gray-900">{message}</p>
        <div className="flex items-center justify-center gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-purple-600"
              animate={{
                y: [0, -8, 0],
              }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
