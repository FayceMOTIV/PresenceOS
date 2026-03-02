// PresenceOS Mobile — Deep Linking Configuration
// Maps rs3:// URLs to React Navigation screens

import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";

// Build redirect URL for OAuth flows
export function buildRedirectUrl(path: string = "social-callback"): string {
  return Linking.createURL(path);
}

// Open OAuth session using expo-web-browser (NO WebView)
export async function openOAuthSession(
  url: string,
  redirectUrl?: string
): Promise<{ success: boolean; url?: string }> {
  const redirect = redirectUrl || buildRedirectUrl();
  const result = await WebBrowser.openAuthSessionAsync(url, redirect);

  if (result.type === "success") {
    return { success: true, url: result.url };
  }
  // "dismiss" = user closed browser but OAuth may have completed server-side
  if (result.type === "dismiss") {
    return { success: true };
  }
  return { success: false };
}

// React Navigation deep linking configuration
export const deepLinkingConfig: { prefixes: string[]; config: { screens: Record<string, any> } } = {
  prefixes: [Linking.createURL("/"), "rs3://"],
  config: {
    screens: {
      Home: {
        screens: {
          HomeMain: "",
          Brief: "brief",
          SocialAccounts: "social-callback",
          BrainDashboard: "brain",
          Analytics: "analytics",
          ValidationInbox: "validation",
          Settings: "settings",
        },
      },
      Files: {
        screens: {
          FileHub: "files",
          AssetUpload: "upload",
          ScanMenu: "scan",
        },
      },
      Ilyas: {
        screens: {
          IlyasChat: "ilyas",
          ProposalDetail: "proposals/:proposalId",
        },
      },
      Video: {
        screens: {
          VideoStudio: "video",
        },
      },
      Inbox: {
        screens: {
          InboxMain: "inbox",
          CMChat: "cm-chat",
        },
      },
    },
  },
};
