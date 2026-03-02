/**
 * Tests du hook useIlyasChat
 */

import { renderHook, act } from "@testing-library/react-native";

jest.mock("@/stores/brandStore", () => ({
  useBrandStore: jest.fn((selector: any) =>
    selector({ activeBrand: { id: "brand-ilyas-123", name: "Test Ilyas" } })
  ),
}));

const mockChat = jest.fn();
const mockListSessions = jest.fn();
const mockGetMessages = jest.fn();
const mockDeleteSession = jest.fn();

jest.mock("@/lib/api", () => ({
  ilyasApi: {
    chat: (...args: any[]) => mockChat(...args),
    listSessions: (...args: any[]) => mockListSessions(...args),
    getMessages: (...args: any[]) => mockGetMessages(...args),
    deleteSession: (...args: any[]) => mockDeleteSession(...args),
    context: jest.fn(),
  },
}));

import { useIlyasChat } from "@/hooks/useIlyasChat";

beforeEach(() => {
  jest.clearAllMocks();
});

describe("useIlyasChat — loadSessions", () => {
  test("charge les sessions Ilyas", async () => {
    mockListSessions.mockResolvedValue({
      data: { sessions: [{ id: "is1", title: "Session Ilyas" }] },
    });

    const { result } = renderHook(() => useIlyasChat());

    await act(async () => {
      await result.current.loadSessions();
    });

    expect(result.current.sessions).toHaveLength(1);
  });
});

describe("useIlyasChat — sendMessage avec image", () => {
  test("envoie un message texte + image", async () => {
    mockChat.mockResolvedValue({
      data: {
        session: { id: "is1", title: "Vision" },
        message: {
          id: "im1",
          role: "assistant",
          content: "Je vois une assiette de tajine",
          session_id: "is1",
          tokens_used: 200,
          created_at: "2026-03-02T10:00:00Z",
        },
      },
    });

    const { result } = renderHook(() => useIlyasChat());

    await act(async () => {
      await result.current.sendMessage(
        "Décris cette photo",
        "https://example.com/photo.jpg"
      );
    });

    expect(mockChat).toHaveBeenCalledWith(
      "brand-ilyas-123",
      "Décris cette photo",
      undefined,
      "https://example.com/photo.jpg"
    );

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].content).toBe(
      "Je vois une assiette de tajine"
    );
  });

  test("envoie un message texte seul (sans image)", async () => {
    mockChat.mockResolvedValue({
      data: {
        session: { id: "is2" },
        message: {
          id: "im2",
          role: "assistant",
          content: "Bonjour !",
          session_id: "is2",
          tokens_used: 50,
          created_at: "2026-03-02T10:00:00Z",
        },
      },
    });

    const { result } = renderHook(() => useIlyasChat());

    await act(async () => {
      await result.current.sendMessage("Salut");
    });

    expect(mockChat).toHaveBeenCalledWith(
      "brand-ilyas-123",
      "Salut",
      undefined,
      undefined
    );
  });
});

describe("useIlyasChat — gestion d'erreur", () => {
  test("rollback optimiste en cas d'erreur", async () => {
    mockChat.mockRejectedValue(new Error("AI service unavailable"));

    const { result } = renderHook(() => useIlyasChat());

    await act(async () => {
      await result.current.sendMessage("Test erreur");
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBe("AI service unavailable");
    expect(result.current.isSending).toBe(false);
  });
});

describe("useIlyasChat — deleteSession", () => {
  test("supprime et réinitialise si session active", async () => {
    mockListSessions.mockResolvedValue({
      data: { sessions: [{ id: "is1" }] },
    });
    mockGetMessages.mockResolvedValue({ data: { messages: [] } });
    mockDeleteSession.mockResolvedValue({ data: { ok: true } });

    const { result } = renderHook(() => useIlyasChat());

    await act(async () => {
      await result.current.loadSessions();
    });
    await act(async () => {
      await result.current.selectSession("is1");
    });
    await act(async () => {
      await result.current.deleteSession("is1");
    });

    expect(result.current.sessions).toHaveLength(0);
    expect(result.current.activeSession).toBeNull();
  });
});
