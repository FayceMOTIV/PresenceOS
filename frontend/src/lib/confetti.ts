import confetti from "canvas-confetti";

export function fireConfetti() {
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 },
    colors: ["#8B5CF6", "#A855F7", "#D946EF", "#F59E0B", "#10B981"],
  });
}

export function fireSuccessConfetti() {
  const end = Date.now() + 300;
  const frame = () => {
    confetti({
      particleCount: 3,
      angle: 60,
      spread: 55,
      origin: { x: 0 },
      colors: ["#8B5CF6", "#A855F7", "#10B981"],
    });
    confetti({
      particleCount: 3,
      angle: 120,
      spread: 55,
      origin: { x: 1 },
      colors: ["#8B5CF6", "#A855F7", "#10B981"],
    });
    if (Date.now() < end) requestAnimationFrame(frame);
  };
  frame();
}
