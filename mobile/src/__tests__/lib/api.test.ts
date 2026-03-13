/**
 * Tests du client API (src/lib/api.ts)
 * Couvre: request wrapper, auth headers, 401 interception, timeout, modules API
 */

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock AbortController
const mockAbort = jest.fn();
global.AbortController = jest.fn().mockImplementation(() => ({
  signal: "mock-signal",
  abort: mockAbort,
})) as any;

// Mock auth store
const mockGetState = jest.fn(() => ({
  token: "test-token-123",
  user: null,
  refreshToken: jest.fn(),
}));

jest.mock("@/stores/authStore", () => ({
  useAuthStore: {
    getState: () => mockGetState(),
    setState: jest.fn(), // used by requestV2 to store refreshed token
  },
}));

jest.mock("expo-constants", () => ({
  expoConfig: { version: "2.0.0" },
}));

// Mock Firebase auth — currentUser is mutable so tests can override it
const mockFirebaseAuth = { currentUser: null as any };
jest.mock("@/lib/firebase", () => ({
  get auth() { return mockFirebaseAuth; },
}));

import api, {
  authApi,
  contentApi,
  menuApi,
  proposalsApi,
  briefApi,
  kbApi,
  assetsApi,
  videoApi,
  cmApi,
  cmChatApi,
  brainApi,
  socialApi,
  brandsApi,
  ilyasApi,
  onboardingApi,
  voiceApi,
  abTestApi,
  engageApi,
  socialV2Api,
  breakoutApi,
  dishApi,
  imageApi,
  aiVideoApi,
  postizApi,
  videoTemplatesApi,
} from "@/lib/api";

function mockJsonResponse(data: any, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get: (h: string) =>
        h === "content-type" ? "application/json" : null,
    },
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  });
}

beforeEach(() => {
  jest.clearAllMocks();
  mockFetch.mockReset();
  mockGetState.mockReturnValue({
    token: "test-token-123",
    user: null,
    refreshToken: jest.fn(),
  });
});

describe("API Client — Core", () => {
  test("ajoute le header Authorization avec le token", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.listDishes("brand-1");
    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders["Authorization"]).toBe("Bearer test-token-123");
  });

  test("ajoute le header X-App-Version", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.listDishes("brand-1");
    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders["X-App-Version"]).toBe("2.0.0");
  });

  test("lance une erreur sur HTTP 500", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ detail: "Internal Server Error" }, 500)
    );
    await expect(contentApi.listDishes("brand-1")).rejects.toThrow(
      "Internal Server Error"
    );
  });

  test("throws on 401 without forcing logout", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ detail: "Not authenticated" }, 401)
    );

    await expect(contentApi.listDishes("brand-1")).rejects.toThrow();
  });

  test("gère le timeout (AbortError)", async () => {
    mockFetch.mockImplementation(() => {
      const error: any = new Error("Aborted");
      error.name = "AbortError";
      return Promise.reject(error);
    });

    await expect(contentApi.listDishes("brand-1")).rejects.toThrow(
      "Request timeout"
    );
  });

  test("construit l'URL avec query params", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ proposals: [] }));
    await proposalsApi.list("brand-1", { status: "pending", limit: 10 });
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("status=pending");
    expect(url).toContain("limit=10");
  });

  test("ne met pas Content-Type pour FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ result: "ok" }));
    const formData = new FormData();
    await assetsApi.upload("brand-1", formData);
    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders["Content-Type"]).toBeUndefined();
  });
});

describe("API Client — Auth Module", () => {
  test("login envoie form-urlencoded", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ access_token: "jwt-123" })
    );
    await authApi.login("test@test.com", "password123");
    const body = mockFetch.mock.calls[0][1].body;
    expect(body).toContain("username=test%40test.com");
    expect(body).toContain("password=password123");
  });

  test("register envoie JSON", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ id: "user-1" }));
    await authApi.register("a@b.com", "pass", "John", "Workspace");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.email).toBe("a@b.com");
    expect(body.full_name).toBe("John");
    expect(body.workspace_name).toBe("Workspace");
  });

  test("forgotPassword envoie l'email", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await authApi.forgotPassword("a@b.com");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.email).toBe("a@b.com");
  });
});

describe("API Client — Proposals Module", () => {
  test("list avec brandId", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ proposals: [] }));
    await proposalsApi.list("brand-abc");
    expect(mockFetch.mock.calls[0][0]).toContain("/proposals/brand-abc");
  });

  test("approve envoie scheduled_at", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await proposalsApi.approve("b1", "p1", "2026-03-15T10:00:00Z");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.scheduled_at).toBe("2026-03-15T10:00:00Z");
  });

  test("reject envoie reason", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await proposalsApi.reject("b1", "p1", "Pas pertinent");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.reason).toBe("Pas pertinent");
  });

  test("editCaption envoie caption + hashtags", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await proposalsApi.editCaption("b1", "p1", "New caption", ["#food"]);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.caption).toBe("New caption");
    expect(body.hashtags).toEqual(["#food"]);
  });

  test("regenerate appelle POST", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await proposalsApi.regenerate("b1", "p1");
    expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    expect(mockFetch.mock.calls[0][0]).toContain("/proposals/b1/p1/regenerate");
  });
});

describe("API Client — Brief Module", () => {
  test("getToday récupère le brief", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ id: "brief-1", status: "pending" })
    );
    const res = await briefApi.getToday("brand-1");
    expect(res.data.status).toBe("pending");
  });

  test("respond envoie la réponse", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await briefApi.respond("brand-1", "Plat du jour: tajine");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.response).toBe("Plat du jour: tajine");
  });
});

describe("API Client — KB Module", () => {
  test("completeness retourne le score", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ completeness_score: 72 })
    );
    const res = await kbApi.completeness("brand-1");
    expect(res.data.completeness_score).toBe(72);
  });

  test("rebuild appelle POST", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await kbApi.rebuild("brand-1");
    expect(mockFetch.mock.calls[0][1].method).toBe("POST");
  });
});

describe("API Client — Video Module", () => {
  test("generate envoie les bons paramètres", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ video_url: "https://example.com/video.mp4" })
    );
    await videoApi.generate("b1", "Un restaurant au coucher de soleil", 10, "cinematic", "9:16");
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("/ai-video/brands/b1/generate");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.prompt).toBe("Un restaurant au coucher de soleil");
    expect(body.duration).toBe(10);
    expect(body.style).toBe("cinematic");
    expect(body.aspect_ratio).toBe("9:16");
  });

  test("credits récupère le solde", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ credits_remaining: 5, plan: "starter" })
    );
    const res = await videoApi.credits("b1");
    expect(res.data.credits_remaining).toBe(5);
  });
});

describe("API Client — CM Chat Module", () => {
  test("send envoie message + session_id", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ session: { id: "s1" }, message: { content: "AI reply" } })
    );
    await cmChatApi.send("b1", "Bonjour", "session-abc");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.message).toBe("Bonjour");
    expect(body.session_id).toBe("session-abc");
  });

  test("send sans session_id envoie null", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ session: { id: "new-s" }, message: {} })
    );
    await cmChatApi.send("b1", "Hello");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.session_id).toBeNull();
  });

  test("listSessions avec pagination", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ sessions: [] }));
    await cmChatApi.listSessions("b1", 10, 5);
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("limit=10");
    expect(url).toContain("offset=5");
  });

  test("deleteSession appelle DELETE", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await cmChatApi.deleteSession("b1", "s1");
    expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
  });
});

describe("API Client — Brain Module", () => {
  test("recall envoie query + memory_type", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ memories: [] }));
    await brainApi.recall("b1", "menu items", "dish");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.query).toBe("menu items");
    expect(body.memory_type).toBe("dish");
  });

  test("registerPushToken envoie le token expo", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await brainApi.registerPushToken("b1", "ExponentPushToken[xxx]");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.expo_push_token).toBe("ExponentPushToken[xxx]");
  });
});

describe("API Client — Social Module", () => {
  test("accounts récupère les comptes", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ accounts: [{ platform: "instagram", connected: true }] })
    );
    const res = await socialApi.accounts("b1");
    expect(res.data.accounts[0].platform).toBe("instagram");
  });

  test("linkUrl passe platform en param", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ url: "https://upload-post.com/oauth" })
    );
    await socialApi.linkUrl("b1", "instagram", "rs3://social-callback");
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("platform=instagram");
    expect(url).toContain("redirect_url=rs3");
  });
});

describe("API Client — CM Inbox Module", () => {
  test("listInteractions passe brand_id", async () => {
    mockFetch.mockReturnValue(
      mockJsonResponse({ interactions: [] })
    );
    await cmApi.listInteractions("b1", { sentiment: "positive" });
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("brand_id=b1");
    expect(url).toContain("sentiment=positive");
  });

  test("approve envoie final_response", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await cmApi.approve("int-1", "Merci pour votre avis !");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.final_response).toBe("Merci pour votre avis !");
  });

  test("reject appelle POST", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await cmApi.reject("int-1");
    expect(mockFetch.mock.calls[0][0]).toContain("/cm/interactions/int-1/reject");
  });

  test("getStats avec days", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ stats: {} }));
    await cmApi.getStats("b1", 30);
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("days=30");
  });
});

// ── Modules non couverts dans la première version ──

describe("API Client — Content Module", () => {
  test("updateDish appelle PUT", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.updateDish("b1", "d1", { name: "Updated" });
    expect(mockFetch.mock.calls[0][0]).toContain("/content/b1/dishes/d1");
    expect(mockFetch.mock.calls[0][1].method).toBe("PUT");
  });

  test("deleteDish appelle DELETE", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.deleteDish("b1", "d1");
    expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
  });

  test("createRequest appelle POST", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.createRequest("b1", { request_text: "Reel" });
    expect(mockFetch.mock.calls[0][0]).toContain("/content/b1/request");
  });
});

describe("API Client — Menu Module", () => {
  test("scan envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ dishes: [] }));
    const fd = new FormData();
    await menuApi.scan("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/menu/b1/scan");
  });

  test("importDishes envoie les plats", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await menuApi.importDishes("b1", [{ name: "Test" }]);
    expect(mockFetch.mock.calls[0][0]).toContain("/menu/b1/scan/import");
  });
});

describe("API Client — Assets Module (complet)", () => {
  test("list récupère les assets", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ assets: [] }));
    await assetsApi.list("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/media-library/brands/b1/assets");
  });

  test("improve appelle POST", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await assetsApi.improve("b1", "a1");
    expect(mockFetch.mock.calls[0][0]).toContain("/media-library/brands/b1/assets/a1/improve");
  });

  test("generatePost envoie asset_id", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await assetsApi.generatePost("b1", "a1");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.asset_id).toBe("a1");
  });
});

describe("API Client — Social Module (complet)", () => {
  test("connectUrl", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ url: "https://oauth.test" }));
    await socialApi.connectUrl("b1", "instagram", "rs3://callback");
    expect(mockFetch.mock.calls[0][0]).toContain("/social/connect-url/b1");
    expect(mockFetch.mock.calls[0][0]).toContain("platform=instagram");
  });

  test("disconnect", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ success: true }));
    await socialApi.disconnect("b1", "acc123");
    expect(mockFetch.mock.calls[0][0]).toContain("/social/disconnect/b1/acc123");
  });

  test("linkUrl sans params", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ url: "https://test" }));
    await socialApi.linkUrl("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/social/link-url/b1");
    expect(mockFetch.mock.calls[0][0]).not.toContain("?");
  });
});

describe("API Client — Brands Module", () => {
  test("mine récupère les marques", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ brands: [] }));
    await brandsApi.mine();
    expect(mockFetch.mock.calls[0][0]).toContain("/brands/mine");
  });
});

describe("API Client — Video history", () => {
  test("history récupère l'historique", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ videos: [] }));
    await videoApi.history("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/video/brands/b1/videos");
  });
});

describe("API Client — CM Chat (complet)", () => {
  test("getMessages", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ messages: [] }));
    await cmChatApi.getMessages("b1", "s1");
    expect(mockFetch.mock.calls[0][0]).toContain("/cm-chat/b1/sessions/s1/messages");
  });
});

describe("API Client — Brain Module (complet)", () => {
  test("status", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ active: true }));
    await brainApi.status("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/brain/b1/status");
  });

  test("visualStatus", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ style: "warm" }));
    await brainApi.visualStatus("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/brain/b1/visual/status");
  });

  test("remember", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await brainApi.remember("b1", "Couscous is best", "brand_facts", "owner");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.content).toBe("Couscous is best");
    expect(body.memory_type).toBe("brand_facts");
  });

  test("extractDna", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ dna: {} }));
    await brainApi.extractDna("b1", ["https://img.jpg"]);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.image_urls).toEqual(["https://img.jpg"]);
  });

  test("analytics", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ data: {} }));
    await brainApi.analytics("b1", 30);
    expect(mockFetch.mock.calls[0][0]).toContain("/brain/b1/analytics");
  });

  test("calendarEvents", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ events: [] }));
    await brainApi.calendarEvents("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/brain/b1/calendar/upcoming");
  });

  test("ugcList", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ items: [] }));
    await brainApi.ugcList("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/brain/b1/ugc");
  });

  test("ugcAdd", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await brainApi.ugcAdd("b1", { url: "https://test" });
    expect(mockFetch.mock.calls[0][1].method).toBe("POST");
  });
});

describe("API Client — Auth token refresh", () => {
  test("refresh token quand user sans token", async () => {
    const mockRefresh = jest.fn().mockResolvedValue("refreshed-jwt");
    mockGetState.mockReturnValue({ token: null, user: { id: "u1" }, refreshToken: mockRefresh } as any);
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.listDishes("b1");
    expect(mockRefresh).toHaveBeenCalled();
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["Authorization"]).toBe("Bearer refreshed-jwt");
  });

  test("resetPassword", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await authApi.resetPassword("tok123", "newpass");
    expect(mockFetch.mock.calls[0][0]).toContain("/auth/reset-password");
  });
});

describe("API Client — Réponse texte", () => {
  test("retourne du texte quand pas JSON", async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: () => "text/plain" },
        text: () => Promise.resolve("OK"),
        json: () => Promise.reject(new Error("not json")),
      })
    );
    const res = await contentApi.listDishes("b1");
    expect(res.data).toBe("OK");
  });
});

// ── V2 Endpoints (requestV2) ──

describe("API Client — Ilyas v2", () => {
  test("chat envoie message + session_id", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ reply: "Bonjour" }));
    await ilyasApi.chat("b1", "Salut", "s1", "https://img.jpg");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.message).toBe("Salut");
    expect(body.session_id).toBe("s1");
    expect(body.image_url).toBe("https://img.jpg");
  });

  test("listSessions", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ sessions: [] }));
    await ilyasApi.listSessions("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/ilyas/b1/sessions");
  });

  test("getMessages", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ messages: [] }));
    await ilyasApi.getMessages("b1", "s1");
    expect(mockFetch.mock.calls[0][0]).toContain("/ilyas/b1/sessions/s1/messages");
  });

  test("deleteSession", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await ilyasApi.deleteSession("b1", "s1");
    expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
  });

  test("context", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ context: {} }));
    await ilyasApi.context("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/ilyas/b1/context");
  });
});

describe("API Client — Onboarding v2", () => {
  test("start", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ step: 0 }));
    await onboardingApi.start("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/onboarding/brands/b1/onboarding/start");
  });

  test("answer", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ next_step: 2 }));
    await onboardingApi.answer("b1", 1, "Italian");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.step).toBe(1);
    expect(body.answer).toBe("Italian");
  });

  test("getDna", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ dna: {} }));
    await onboardingApi.getDna("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/onboarding/brands/b1/onboarding/dna");
  });

  test("scrape", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ result: {} }));
    await onboardingApi.scrape("b1", "https://restaurant.com");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.url).toBe("https://restaurant.com");
  });
});

describe("API Client — Voice v2", () => {
  test("transcribe envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ text: "transcription" }));
    const fd = new FormData();
    await voiceApi.transcribe("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/voice/b1/transcribe");
  });
});

describe("API Client — A/B Testing v2", () => {
  test("create", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ test_id: "t1" }));
    await abTestApi.create("b1", "instagram", "Original caption", "food");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.platform).toBe("instagram");
    expect(body.original_caption).toBe("Original caption");
  });

  test("list", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ tests: [] }));
    await abTestApi.list("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/ab/b1/tests");
  });
});

describe("API Client — Engage v2", () => {
  test("scan", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await engageApi.scan("b1", 48);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.since_hours).toBe(48);
  });

  test("inbox", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ comments: [] }));
    await engageApi.inbox("b1", "pending", 20);
    expect(mockFetch.mock.calls[0][0]).toContain("/engage/b1/inbox");
  });

  test("approve", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await engageApi.approve("b1", "c1", "Thanks!");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.final_reply).toBe("Thanks!");
  });

  test("reject", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await engageApi.reject("b1", "c1");
    expect(mockFetch.mock.calls[0][0]).toContain("/engage/b1/inbox/c1/reject");
  });

  test("stats", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ stats: {} }));
    await engageApi.stats("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/engage/b1/stats");
  });
});

describe("API Client — Social v2", () => {
  test("accounts sans filtre", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ accounts: [] }));
    await socialV2Api.accounts();
    expect(mockFetch.mock.calls[0][0]).toContain("/social/accounts");
  });

  test("accounts avec filtre platform", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ accounts: [] }));
    await socialV2Api.accounts("instagram");
    expect(mockFetch.mock.calls[0][0]).toContain("/social/accounts");
  });

  test("subaccounts", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ subaccounts: [] }));
    await socialV2Api.subaccounts("acc1");
    expect(mockFetch.mock.calls[0][0]).toContain("/social/accounts/acc1/subaccounts");
  });

  test("publish", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await socialV2Api.publish("acc1", "instagram", "Hello!", ["https://img.jpg"], "page1");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.account_id).toBe("acc1");
    expect(body.platform).toBe("instagram");
    expect(body.text).toBe("Hello!");
  });
});

// ── Coverage: uncovered branches and paths ──

describe("API Client — Core: __DEV__ bypass (no token, no user)", () => {
  test("envoie dev-token quand pas de token et pas d'utilisateur en mode DEV", async () => {
    // Simulate __DEV__ = true (already set in test env), no token, no user
    mockGetState.mockReturnValue({ token: null, user: null, refreshToken: jest.fn() } as any);
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await contentApi.listDishes("b1");
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["Authorization"]).toBe("Bearer dev-token-presenceos");
  });
});

describe("API Client — Core: 401 retry success path", () => {
  test("retire la requête avec le nouveau token après un 401", async () => {
    const freshToken = "refreshed-token-xyz";
    const mockRefresh = jest.fn().mockResolvedValue(freshToken);
    mockGetState.mockReturnValue({ token: "old-token", user: null, refreshToken: mockRefresh });

    // First call returns 401, second (retry) returns 200
    mockFetch
      .mockReturnValueOnce(mockJsonResponse({ detail: "Unauthorized" }, 401))
      .mockReturnValueOnce(mockJsonResponse({ data: "ok" }, 200));

    const res = await contentApi.listDishes("b1");
    expect(res.data).toEqual({ data: "ok" });
    expect(mockFetch).toHaveBeenCalledTimes(2);
    const retryHeaders = mockFetch.mock.calls[1][1].headers;
    expect(retryHeaders["Authorization"]).toBe(`Bearer ${freshToken}`);
  });

  test("propage l'erreur quand le token refresh échoue sur 401", async () => {
    const mockRefresh = jest.fn().mockResolvedValue(null);
    mockGetState.mockReturnValue({ token: "old-token", user: null, refreshToken: mockRefresh });

    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Unauthorized" }, 401));

    await expect(contentApi.listDishes("b1")).rejects.toThrow();
  });

  test("propage l'erreur quand refreshToken lance une exception sur 401", async () => {
    const mockRefresh = jest.fn().mockRejectedValue(new Error("Firebase session dead"));
    mockGetState.mockReturnValue({ token: "bad-token", user: null, refreshToken: mockRefresh });

    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Unauthorized" }, 401));

    await expect(contentApi.listDishes("b1")).rejects.toThrow();
  });

  test("ne force pas la déconnexion après un 401", async () => {
    const mockRefresh = jest.fn().mockResolvedValue(null);
    mockGetState.mockReturnValue({ token: "t", user: null, refreshToken: mockRefresh });
    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Unauthorized" }, 401));

    // Should reject but NOT call logout
    await expect(contentApi.listDishes("b1")).rejects.toThrow();
    // No logout call means no store setState with isAuthenticated: false from here
    expect(mockRefresh).toHaveBeenCalledTimes(1);
  });
});

describe("API Client — Core: réponse non-JSON (request)", () => {
  test("retourne du texte brut quand content-type est text/plain", async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: () => "text/plain" },
        text: () => Promise.resolve("plain text response"),
        json: () => Promise.reject(new Error("not json")),
      })
    );
    const res = await contentApi.listDishes("b1");
    expect(res.data).toBe("plain text response");
  });
});

describe("API Client — Core: erreur 403", () => {
  test("lance une erreur avec le message detail sur 403", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Access forbidden" }, 403));
    await expect(contentApi.listDishes("b1")).rejects.toThrow("Access forbidden");
  });
});

describe("API Client — requestV2: timeout (AbortError)", () => {
  test("gère le timeout sur requestV2 (AbortError)", async () => {
    mockFetch.mockImplementation(() => {
      const error: any = new Error("Aborted");
      error.name = "AbortError";
      return Promise.reject(error);
    });
    await expect(videoApi.credits("b1")).rejects.toThrow("Request timeout");
  });
});

describe("API Client — requestV2: réponse non-JSON", () => {
  test("retourne du texte brut dans requestV2 quand content-type est text/plain", async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: () => "text/plain" },
        text: () => Promise.resolve("v2 text response"),
        json: () => Promise.reject(new Error("not json")),
      })
    );
    const res = await videoApi.credits("b1");
    expect(res.data).toBe("v2 text response");
  });
});

describe("API Client — requestV2: 401 retry success", () => {
  afterEach(() => {
    mockFirebaseAuth.currentUser = null;
  });

  test("retire avec le nouveau token Firebase après 401 sur requestV2", async () => {
    const freshToken = "firebase-refreshed-token";
    mockFirebaseAuth.currentUser = {
      getIdToken: jest.fn().mockResolvedValue(freshToken),
    };

    mockFetch
      .mockReturnValueOnce(mockJsonResponse({ detail: "Unauthorized" }, 401))
      .mockReturnValueOnce(mockJsonResponse({ credits_remaining: 10 }, 200));

    const res = await videoApi.credits("b1");
    expect(res.data.credits_remaining).toBe(10);
    // Original request + retry
    expect(mockFetch).toHaveBeenCalledTimes(2);
    // Retry must use the fresh token
    const retryHeaders = mockFetch.mock.calls[1][1].headers;
    expect(retryHeaders["Authorization"]).toBe(`Bearer ${freshToken}`);
  });

  test("requestV2 401: retourne l'erreur quand le retry échoue aussi", async () => {
    const freshToken = "firebase-fresh-but-retry-fails";
    mockFirebaseAuth.currentUser = {
      getIdToken: jest.fn().mockResolvedValue(freshToken),
    };

    // Both calls fail
    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Unauthorized" }, 401));
    await expect(videoApi.credits("b1")).rejects.toThrow();
  });

  test("requestV2 401: pas de currentUser — ne peut pas rafraichir le token", async () => {
    mockFirebaseAuth.currentUser = null;
    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Unauthorized" }, 401));
    await expect(videoApi.credits("b1")).rejects.toThrow();
    // Should only call fetch once (no retry without currentUser)
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  test("requestV2 401 retry avec corps FormData (branche isFormData)", async () => {
    const freshToken = "firebase-fresh-formdata";
    mockFirebaseAuth.currentUser = {
      getIdToken: jest.fn().mockResolvedValue(freshToken),
    };

    mockFetch
      .mockReturnValueOnce(mockJsonResponse({ detail: "Unauthorized" }, 401))
      .mockReturnValueOnce(mockJsonResponse({ text: "transcription" }, 200));

    const fd = new FormData();
    fd.append("audio", "mock-audio-data");
    // voiceApi.transcribe uses requestV2 with isFormData: true + body
    const res = await voiceApi.transcribe("b1", fd);
    expect(res.data.text).toBe("transcription");
    expect(mockFetch).toHaveBeenCalledTimes(2);
    // Retry must have the fresh token
    const retryHeaders = mockFetch.mock.calls[1][1].headers;
    expect(retryHeaders["Authorization"]).toBe(`Bearer ${freshToken}`);
  });

  test("requestV2: propage l'erreur quand le retry échoue aussi sur 401", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ detail: "Unauthorized" }, 401));
    await expect(videoApi.credits("b1")).rejects.toThrow();
  });
});

describe("API Client — requestV2: params avec valeurs null/undefined filtrées", () => {
  test("filtre les params null et undefined dans l'URL v2", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ tests: [] }));
    await engageApi.inbox("b1", undefined, 50);
    const url = mockFetch.mock.calls[0][0];
    // undefined status_filter should not appear in URL
    expect(url).not.toContain("status_filter=undefined");
    expect(url).toContain("limit=50");
  });
});

describe("API Client — buildUrl: filtre null/undefined", () => {
  test("ne met pas les params null dans l'URL", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ proposals: [] }));
    await proposalsApi.list("b1", { status: "pending", page: null, limit: undefined });
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("status=pending");
    expect(url).not.toContain("page=null");
    expect(url).not.toContain("limit=undefined");
  });
});

describe("API Client — Content createDish", () => {
  test("createDish appelle POST avec les données du plat", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ id: "dish-1", name: "Couscous" }));
    const res = await contentApi.createDish("b1", { name: "Couscous", price: 12.5 });
    expect(mockFetch.mock.calls[0][0]).toContain("/content/b1/dishes");
    expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.name).toBe("Couscous");
    expect(body.price).toBe(12.5);
    expect(res.data.id).toBe("dish-1");
  });
});

describe("API Client — KB Module (complet)", () => {
  test("kbApi.get", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ kb: {} }));
    await kbApi.get("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/kb/b1");
    expect(mockFetch.mock.calls[0][1].method).toBe("GET");
  });
});

describe("API Client — Social publish et schedule", () => {
  test("socialApi.publish envoie content + platforms + media_urls", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await socialApi.publish("b1", "Hello!", [{ platform: "instagram", accountId: "acc1" }], ["https://img.jpg"]);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.content).toBe("Hello!");
    expect(body.platforms).toEqual([{ platform: "instagram", accountId: "acc1" }]);
    expect(body.media_urls).toEqual(["https://img.jpg"]);
  });

  test("socialApi.publish sans mediaUrls envoie tableau vide", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await socialApi.publish("b1", "Post", [{ platform: "facebook", accountId: "acc2" }]);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.media_urls).toEqual([]);
  });

  test("socialApi.schedule envoie scheduled_for + timezone", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await socialApi.schedule("b1", "Scheduled post", [{ platform: "instagram", accountId: "acc1" }], "2026-04-01T10:00:00Z");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.content).toBe("Scheduled post");
    expect(body.scheduled_for).toBe("2026-04-01T10:00:00Z");
    expect(body.timezone).toBe("Europe/Paris");
    expect(body.media_urls).toEqual([]);
  });
});

describe("API Client — Video Module (complet)", () => {
  test("videoApi.setCredits envoie credits + plan", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await videoApi.setCredits("b1", 10, "pro");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.credits).toBe(10);
    expect(body.plan).toBe("pro");
  });

  test("videoApi.setCredits utilise plan 'studio' par défaut", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await videoApi.setCredits("b1", 5);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.plan).toBe("studio");
  });

  test("videoApi.save envoie les métadonnées vidéo", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ asset_id: "v1" }));
    await videoApi.save("b1", "https://fal.ai/video.mp4", "Restaurant sunset", 10, "9:16", "cinematic");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.fal_url).toBe("https://fal.ai/video.mp4");
    expect(body.prompt).toBe("Restaurant sunset");
    expect(body.duration_seconds).toBe(10);
    expect(body.aspect_ratio).toBe("9:16");
    expect(body.style).toBe("cinematic");
  });

  test("videoApi.publish envoie asset_id + platform + caption", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await videoApi.publish("b1", "asset-123", "instagram", "Check this out!", "@restaurant");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.asset_id).toBe("asset-123");
    expect(body.platform).toBe("instagram");
    expect(body.caption).toBe("Check this out!");
    expect(body.account_username).toBe("@restaurant");
  });

  test("videoApi.listSaved appelle GET sur /video/brands/:id/videos", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ videos: [] }));
    await videoApi.listSaved("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/video/brands/b1/videos");
    expect(mockFetch.mock.calls[0][1].method).toBe("GET");
  });
});

describe("API Client — Onboarding v2 (complet)", () => {
  test("onboardingApi.getState", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ state: {} }));
    await onboardingApi.getState("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/onboarding/brands/b1/onboarding/state");
  });

  test("onboardingApi.reset appelle POST", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await onboardingApi.reset("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/onboarding/brands/b1/onboarding/reset");
    expect(mockFetch.mock.calls[0][1].method).toBe("POST");
  });
});

describe("API Client — Breakout v2", () => {
  test("generate envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/breakout.mp4" }));
    const fd = new FormData();
    fd.append("file", "mock-file");
    await breakoutApi.generate("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/breakout/b1/generate");
    // FormData — Content-Type doit être absent
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["Content-Type"]).toBeUndefined();
  });
});

describe("API Client — Dish Recognition v2", () => {
  test("recognize envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ dish: { name: "Pizza" } }));
    const fd = new FormData();
    fd.append("image", "mock-image");
    await dishApi.recognize(fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/dish/recognize");
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["Content-Type"]).toBeUndefined();
  });
});

describe("API Client — Image Generation v2", () => {
  test("imageApi.generate avec valeurs par défaut", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ image_url: "https://example.com/img.jpg" }));
    await imageApi.generate("b1", "Assiette gastronomique");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.prompt).toBe("Assiette gastronomique");
    expect(body.niche).toBe("restaurant");
    expect(body.style).toBe("natural");
    expect(body.quality).toBe("fast");
  });

  test("imageApi.generate avec paramètres personnalisés", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ image_url: "https://example.com/img2.jpg" }));
    await imageApi.generate("b1", "Plat du jour", "bakery", "artistic", "hd");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.niche).toBe("bakery");
    expect(body.style).toBe("artistic");
    expect(body.quality).toBe("hd");
  });

  test("imageApi.enhance envoie source_url + style", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ enhanced_url: "https://example.com/enhanced.jpg" }));
    await imageApi.enhance("b1", "https://example.com/orig.jpg", "fine-dining");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.source_url).toBe("https://example.com/orig.jpg");
    expect(body.style).toBe("fine-dining");
  });

  test("imageApi.enhance utilise 'restaurant' comme style par défaut", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ enhanced_url: "https://example.com/enhanced2.jpg" }));
    await imageApi.enhance("b1", "https://example.com/orig.jpg");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.style).toBe("restaurant");
  });

  test("imageApi.niches retourne la liste des niches", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ niches: ["restaurant", "bakery", "cafe"] }));
    const res = await imageApi.niches();
    expect(mockFetch.mock.calls[0][0]).toContain("/images/niches");
    expect(res.data.niches).toContain("restaurant");
  });
});

describe("API Client — AI Video v2 (Kling/Wan)", () => {
  test("aiVideoApi.textToVideo avec valeurs par défaut", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/vid.mp4" }));
    await aiVideoApi.textToVideo("b1", "Un restaurant animé");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.prompt).toBe("Un restaurant animé");
    expect(body.duration).toBe(5);
    expect(body.aspect_ratio).toBe("9:16");
    expect(body.model).toBe("kling");
  });

  test("aiVideoApi.textToVideo avec paramètres personnalisés", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/vid2.mp4" }));
    await aiVideoApi.textToVideo("b1", "Sunset terrace", 10, "16:9", "wan");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.duration).toBe(10);
    expect(body.aspect_ratio).toBe("16:9");
    expect(body.model).toBe("wan");
  });

  test("aiVideoApi.imageToVideo envoie image_url + prompt", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/i2v.mp4" }));
    await aiVideoApi.imageToVideo("b1", "https://example.com/dish.jpg", "Add motion effects", 10, "9:16");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.image_url).toBe("https://example.com/dish.jpg");
    expect(body.prompt).toBe("Add motion effects");
    expect(body.duration).toBe(10);
    expect(body.aspect_ratio).toBe("9:16");
  });

  test("aiVideoApi.imageToVideo avec valeurs par défaut", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/i2v2.mp4" }));
    await aiVideoApi.imageToVideo("b1", "https://example.com/food.jpg");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.prompt).toBe("");
    expect(body.duration).toBe(5);
    expect(body.aspect_ratio).toBe("9:16");
  });
});

describe("API Client — Postiz v2", () => {
  test("getConnectUrl", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ url: "https://oauth.postiz.com/instagram" }));
    await postizApi.getConnectUrl("b1", "instagram");
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/brands/b1/connect/instagram");
  });

  test("integrations", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ integrations: [] }));
    await postizApi.integrations("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/brands/b1/integrations");
  });

  test("disconnect", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await postizApi.disconnect("b1", "int-123");
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/brands/b1/integrations/int-123");
    expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
  });

  test("publishNow envoie integration_ids + content + media_urls", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ post_id: "p1" }));
    await postizApi.publishNow("b1", ["int-1", "int-2"], "Beau post!", ["https://img.jpg"]);
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.integration_ids).toEqual(["int-1", "int-2"]);
    expect(body.content).toBe("Beau post!");
    expect(body.media_urls).toEqual(["https://img.jpg"]);
  });

  test("publishNow sans media envoie tableau vide", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ post_id: "p2" }));
    await postizApi.publishNow("b1", ["int-1"], "Post sans media");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.media_urls).toEqual([]);
  });

  test("schedule envoie publish_at", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ post_id: "p3" }));
    await postizApi.schedule("b1", ["int-1"], "Post planifié", "2026-04-01T09:00:00Z");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.publish_at).toBe("2026-04-01T09:00:00Z");
    expect(body.media_urls).toEqual([]);
  });

  test("listPosts", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ posts: [] }));
    await postizApi.listPosts("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/brands/b1/posts");
  });

  test("deletePost", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await postizApi.deletePost("b1", "post-999");
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/brands/b1/posts/post-999");
    expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
  });

  test("analytics avec days", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ analytics: {} }));
    await postizApi.analytics("b1", "int-1", 30);
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/brands/b1/analytics/int-1");
    expect(mockFetch.mock.calls[0][0]).toContain("days=30");
  });

  test("analytics sans days", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ analytics: {} }));
    await postizApi.analytics("b1", "int-1");
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("/publish/brands/b1/analytics/int-1");
    expect(url).not.toContain("days=");
  });

  test("health", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ status: "ok" }));
    await postizApi.health();
    expect(mockFetch.mock.calls[0][0]).toContain("/publish/health");
  });
});

describe("API Client — Video Templates v2", () => {
  test("prepareBreakoutV4 envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ cutout_url: "https://example.com/cutout.png" }));
    const fd = new FormData();
    fd.append("image", "mock-image");
    await videoTemplatesApi.prepareBreakoutV4("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/breakout-v4/brands/b1/prepare");
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["Content-Type"]).toBeUndefined();
  });

  test("renderBreakoutV4 envoie les données de rendu", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/breakout-v4.mp4" }));
    await videoTemplatesApi.renderBreakoutV4("b1", {
      original_url: "https://example.com/original.jpg",
      cutout_url: "https://example.com/cutout.png",
      business_name: "Le Restaurant",
      instagram_handle: "@lerestaurant",
      caption: "Découvrez notre spécialité",
      accent_color: "#7C5CBF",
    });
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/breakout-v4/brands/b1/render");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.business_name).toBe("Le Restaurant");
    expect(body.accent_color).toBe("#7C5CBF");
  });

  test("generateBreakoutV4 envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/gen-breakout.mp4" }));
    const fd = new FormData();
    await videoTemplatesApi.generateBreakoutV4("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/breakout-v4/brands/b1/generate");
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["Content-Type"]).toBeUndefined();
  });

  test("generateCinematic envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/cinematic.mp4" }));
    const fd = new FormData();
    await videoTemplatesApi.generateCinematic("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/cinematic/brands/b1/generate");
  });

  test("generateCinematicFromUrl envoie image_url + food_type + duration + aspect_ratio", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/cin-url.mp4" }));
    await videoTemplatesApi.generateCinematicFromUrl("b1", "https://example.com/dish.jpg", "pizza", 10, "16:9");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.image_url).toBe("https://example.com/dish.jpg");
    expect(body.food_type).toBe("pizza");
    expect(body.duration).toBe("10");
    expect(body.aspect_ratio).toBe("16:9");
  });

  test("generateCinematicFromUrl avec valeurs par défaut", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/cin-default.mp4" }));
    await videoTemplatesApi.generateCinematicFromUrl("b1", "https://example.com/food.jpg");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.food_type).toBe("default");
    expect(body.duration).toBe("5");
    expect(body.aspect_ratio).toBe("9:16");
  });

  test("cinematicPricing", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ plans: [] }));
    await videoTemplatesApi.cinematicPricing();
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/cinematic/pricing");
  });

  test("generatePromoFlash envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/promo.mp4" }));
    const fd = new FormData();
    await videoTemplatesApi.generatePromoFlash("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/promo-flash/brands/b1/generate");
  });

  test("generateShowcase envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/showcase.mp4" }));
    const fd = new FormData();
    await videoTemplatesApi.generateShowcase("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/showcase/brands/b1/generate");
  });

  test("generateStory envoie FormData", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ video_url: "https://example.com/story.mp4" }));
    const fd = new FormData();
    await videoTemplatesApi.generateStory("b1", fd);
    expect(mockFetch.mock.calls[0][0]).toContain("/templates/story/brands/b1/generate");
  });
});
