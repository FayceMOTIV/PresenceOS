"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Check, Plus } from "lucide-react";

interface PublishCelebrationProps {
  onReset: () => void;
}

function Confetti({ canvasRef }: { canvasRef: React.RefObject<HTMLCanvasElement | null> }) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const colors = ["#f59e0b", "#ea580c", "#22c55e", "#3b82f6", "#a855f7", "#ec4899"];
    const particles: {
      x: number;
      y: number;
      vx: number;
      vy: number;
      color: string;
      size: number;
      rotation: number;
      rotationSpeed: number;
      life: number;
    }[] = [];

    // Create particles
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: canvas.width / 2 + (Math.random() - 0.5) * 100,
        y: canvas.height / 2,
        vx: (Math.random() - 0.5) * 12,
        vy: -Math.random() * 12 - 3,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: Math.random() * 6 + 3,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 10,
        life: 1,
      });
    }

    let animFrame: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      let alive = false;
      for (const p of particles) {
        if (p.life <= 0) continue;
        alive = true;

        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.15; // gravity
        p.rotation += p.rotationSpeed;
        p.life -= 0.008;
        p.vx *= 0.99;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = Math.max(0, p.life);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
        ctx.restore();
      }

      if (alive) {
        animFrame = requestAnimationFrame(animate);
      }
    };

    animate();
    return () => cancelAnimationFrame(animFrame);
  }, [canvasRef]);

  return null;
}

export function PublishCelebration({ onReset }: PublishCelebrationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />
      <Confetti canvasRef={canvasRef} />

      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.2 }}
        className="relative z-10 text-center"
      >
        {/* Animated check */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300, delay: 0.4 }}
          className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6 border-2 border-green-500"
        >
          <motion.div
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            <Check className="w-12 h-12 text-green-500" strokeWidth={3} />
          </motion.div>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-3xl font-bold text-white mb-2"
        >
          Publie !
        </motion.h2>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-muted-foreground mb-8"
        >
          Ta publication est en route !
        </motion.p>

        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onReset}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium shadow-lg shadow-amber-500/20 hover:shadow-amber-500/40 transition-shadow"
        >
          <Plus className="w-5 h-5" />
          Creer une autre publication
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
