'use client';

import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function MobileMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        className="md:hidden fixed top-4 right-4 z-50 p-3 bg-white rounded-full shadow-lg"
        aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'}
      >
        {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
              className="md:hidden fixed inset-0 bg-black/50 z-40"
            />

            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="md:hidden fixed top-0 right-0 bottom-0 w-80 bg-white z-40 shadow-2xl overflow-y-auto"
            >
              <div className="p-6 pt-20">{children}</div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
