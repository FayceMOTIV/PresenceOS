'use client';

import { useEffect } from 'react';

export default function CrispChat() {
  useEffect(() => {
    const websiteId = process.env.NEXT_PUBLIC_CRISP_WEBSITE_ID;
    if (!websiteId) return;

    try {
      const { Crisp } = require('crisp-sdk-web');
      Crisp.configure(websiteId);

      // Auto-set user info
      const userId = localStorage.getItem('user_id');
      if (userId) {
        Crisp.user.setNickname(`User ${userId.slice(0, 8)}`);
        Crisp.session.setData({
          user_id: userId,
          plan: localStorage.getItem('user_plan') || 'free',
        });
      }

      // Hide on mobile by default
      if (window.innerWidth < 768) {
        Crisp.chat.hide();
      }
    } catch {
      // crisp-sdk-web not available
    }
  }, []);

  return null;
}
