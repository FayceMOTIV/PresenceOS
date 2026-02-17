// Analytics module - Mixpanel integration
// Works as no-op when NEXT_PUBLIC_MIXPANEL_TOKEN is not set

let mixpanelLoaded = false;

function getMixpanel() {
  if (typeof window === 'undefined') return null;
  if (!process.env.NEXT_PUBLIC_MIXPANEL_TOKEN) return null;

  if (!mixpanelLoaded) {
    try {
      const mixpanel = require('mixpanel-browser');
      mixpanel.init(process.env.NEXT_PUBLIC_MIXPANEL_TOKEN, {
        debug: process.env.NODE_ENV === 'development',
        track_pageview: true,
        persistence: 'localStorage',
      });
      mixpanelLoaded = true;
      return mixpanel;
    } catch {
      return null;
    }
  }

  try {
    return require('mixpanel-browser');
  } catch {
    return null;
  }
}

export const analytics = {
  identify: (userId: string, properties?: Record<string, unknown>) => {
    const mp = getMixpanel();
    if (!mp) return;
    mp.identify(userId);
    if (properties) mp.people.set(properties);
  },

  track: (eventName: string, properties?: Record<string, unknown>) => {
    const mp = getMixpanel();
    if (!mp) return;
    mp.track(eventName, { ...properties, timestamp: new Date().toISOString() });
  },

  page: (pageName: string) => {
    const mp = getMixpanel();
    if (!mp) return;
    mp.track('Page View', { page: pageName });
  },

  setUserProperties: (properties: Record<string, unknown>) => {
    const mp = getMixpanel();
    if (!mp) return;
    mp.people.set(properties);
  },

  trackRevenue: (amount: number, properties?: Record<string, unknown>) => {
    const mp = getMixpanel();
    if (!mp) return;
    mp.people.track_charge(amount, properties);
  },

  reset: () => {
    const mp = getMixpanel();
    if (!mp) return;
    mp.reset();
  },
};

export const events = {
  SIGNUP: 'User Signed Up',
  LOGIN: 'User Logged In',
  LOGOUT: 'User Logged Out',
  ONBOARDING_STARTED: 'Onboarding Started',
  ONBOARDING_COMPLETED: 'Onboarding Completed',
  ONBOARDING_SKIPPED: 'Onboarding Skipped',
  PHOTO_UPLOADED: 'Photo Uploaded',
  CAPTION_GENERATED: 'Caption Generated',
  POST_PUBLISHED: 'Post Published',
  POST_SCHEDULED: 'Post Scheduled',
  INSTAGRAM_CONNECTED: 'Instagram Connected',
  INSTAGRAM_DISCONNECTED: 'Instagram Disconnected',
  PLAN_UPGRADED: 'Plan Upgraded',
  PLAN_DOWNGRADED: 'Plan Downgraded',
  SUBSCRIPTION_CANCELLED: 'Subscription Cancelled',
  DASHBOARD_VIEWED: 'Dashboard Viewed',
  SETTINGS_OPENED: 'Settings Opened',
  HELP_CLICKED: 'Help Clicked',
};
