import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white/80 backdrop-blur-sm py-6">
      <div className="container mx-auto px-4 text-center text-gray-400 text-sm">
        <div className="flex justify-center gap-6 mb-4">
          <Link href="/legal/terms" className="hover:text-violet-600 transition-colors">CGU</Link>
          <Link href="/legal/privacy" className="hover:text-violet-600 transition-colors">Confidentialité</Link>
          <Link href="/help" className="hover:text-violet-600 transition-colors">Aide</Link>
        </div>
        <p className="flex items-center justify-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-violet-400" />
          2026 PresenceOS. Tous droits réservés.
        </p>
      </div>
    </footer>
  );
}
