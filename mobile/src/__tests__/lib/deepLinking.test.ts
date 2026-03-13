/**
 * Tests du deepLinking
 */

jest.mock("expo-linking", () => ({
  createURL: jest.fn().mockReturnValue("rs3:///"),
}));

jest.mock("expo-web-browser", () => ({
  openAuthSessionAsync: jest.fn(),
}));

import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { buildRedirectUrl, openOAuthSession, deepLinkingConfig } from "@/lib/deepLinking";

beforeEach(() => {
  jest.clearAllMocks();
  (Linking.createURL as jest.Mock).mockReturnValue("rs3://social-callback");
});

describe("buildRedirectUrl", () => {
  test("appelle Linking.createURL avec le path", () => {
    buildRedirectUrl("social-callback");
    expect(Linking.createURL).toHaveBeenCalledWith("social-callback");
  });

  test("path par défaut est social-callback", () => {
    buildRedirectUrl();
    expect(Linking.createURL).toHaveBeenCalledWith("social-callback");
  });
});

describe("openOAuthSession", () => {
  test("retourne success true si type success", async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValue({ type: "success", url: "rs3://callback?code=abc" });
    const result = await openOAuthSession("https://auth.example.com");
    expect(result.success).toBe(true);
    expect(result.url).toBe("rs3://callback?code=abc");
  });

  test("retourne success true si type dismiss", async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValue({ type: "dismiss" });
    const result = await openOAuthSession("https://auth.example.com");
    expect(result.success).toBe(true);
    expect(result.url).toBeUndefined();
  });

  test("retourne success false si type cancel", async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValue({ type: "cancel" });
    const result = await openOAuthSession("https://auth.example.com");
    expect(result.success).toBe(false);
  });

  test("utilise le redirect custom si fourni", async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValue({ type: "success", url: "custom://cb" });
    await openOAuthSession("https://auth.example.com", "custom://cb");
    expect(WebBrowser.openAuthSessionAsync).toHaveBeenCalledWith("https://auth.example.com", "custom://cb");
  });
});

describe("deepLinkingConfig", () => {
  test("contient les prefixes rs3://", () => {
    expect(deepLinkingConfig.prefixes).toContain("rs3://");
  });

  test("contient les 5 tabs", () => {
    const screens = deepLinkingConfig.config.screens;
    expect(screens.Home).toBeDefined();
    expect(screens.Files).toBeDefined();
    expect(screens.Ilyas).toBeDefined();
    expect(screens.Video).toBeDefined();
    expect(screens.Inbox).toBeDefined();
  });

  test("Home contient les sous-écrans", () => {
    const home = deepLinkingConfig.config.screens.Home.screens;
    expect(home.HomeMain).toBe("");
    expect(home.Brief).toBe("brief");
    expect(home.SocialAccounts).toBe("social-accounts");
  });

  test("Inbox contient CMChat", () => {
    const inbox = deepLinkingConfig.config.screens.Inbox.screens;
    expect(inbox.CMChat).toBe("cm-chat");
  });
});
