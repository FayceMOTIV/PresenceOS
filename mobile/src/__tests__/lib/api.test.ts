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
  useAuthStore: { getState: () => mockGetState() },
}));

jest.mock("expo-constants", () => ({
  expoConfig: { version: "2.0.0" },
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
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.brand_id).toBe("b1");
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
  test("facebookPages", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ pages: [] }));
    await socialApi.facebookPages("b1");
    expect(mockFetch.mock.calls[0][0]).toContain("/social-auth/facebook-pages/b1");
  });

  test("selectPage", async () => {
    mockFetch.mockReturnValue(mockJsonResponse({ ok: true }));
    await socialApi.selectPage("b1", "page123");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.page_id).toBe("page123");
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
    expect(mockFetch.mock.calls[0][0]).toContain("/video/history/b1");
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
