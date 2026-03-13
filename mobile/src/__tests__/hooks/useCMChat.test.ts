/**
 * Tests du hook useCMChat
 */

import { renderHook, act } from "@testing-library/react-native";

// Mock the business store
jest.mock("@/stores/businessStore", () => ({
  useBusinessStore: jest.fn((selector: any) =>
    selector({ activeBrand: { id: "brand-test-123", name: "Test" } })
  ),
}));

// Mock cmChatApi
const mockListSessions = jest.fn();
const mockGetMessages = jest.fn();
const mockSend = jest.fn();
const mockDeleteSession = jest.fn();

jest.mock("@/lib/api", () => ({
  cmChatApi: {
    listSessions: (...args: any[]) => mockListSessions(...args),
    getMessages: (...args: any[]) => mockGetMessages(...args),
    send: (...args: any[]) => mockSend(...args),
    deleteSession: (...args: any[]) => mockDeleteSession(...args),
  },
}));

import { useCMChat } from "@/hooks/useCMChat";

beforeEach(() => {
  jest.clearAllMocks();
});

describe("useCMChat — loadSessions", () => {
  test("charge les sessions", async () => {
    const sessions = [
      { id: "s1", title: "Session 1", message_count: 3 },
      { id: "s2", title: "Session 2", message_count: 1 },
    ];
    mockListSessions.mockResolvedValue({ data: { sessions } });

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.loadSessions();
    });

    expect(result.current.sessions).toHaveLength(2);
    expect(result.current.isLoading).toBe(false);
  });

  test("gère l'erreur de chargement", async () => {
    mockListSessions.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.loadSessions();
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.isLoading).toBe(false);
  });
});

describe("useCMChat — selectSession", () => {
  test("charge les messages d'une session", async () => {
    const messages = [
      { id: "m1", role: "user", content: "Bonjour" },
      { id: "m2", role: "assistant", content: "Comment puis-je aider ?" },
    ];
    mockListSessions.mockResolvedValue({
      data: { sessions: [{ id: "s1", title: "Test" }] },
    });
    mockGetMessages.mockResolvedValue({ data: { messages } });

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.loadSessions();
    });

    await act(async () => {
      await result.current.selectSession("s1");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.activeSession?.id).toBe("s1");
  });
});

describe("useCMChat — sendMessage", () => {
  test("envoi optimiste + réponse serveur", async () => {
    const serverResponse = {
      session: { id: "s1", title: "Chat", message_count: 2 },
      message: {
        id: "m-ai",
        role: "assistant",
        content: "Réponse IA",
        session_id: "s1",
        tokens_used: 150,
        created_at: "2026-03-02T10:00:00Z",
      },
    };
    mockSend.mockResolvedValue({ data: serverResponse });

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.sendMessage("Bonjour !");
    });

    // Doit contenir le message user optimiste + la réponse IA
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].content).toBe("Réponse IA");
    expect(result.current.isSending).toBe(false);
  });

  test("supprime le message optimiste en cas d'erreur", async () => {
    mockSend.mockRejectedValue(new Error("Server error"));

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.sendMessage("Test");
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBe("Server error");
  });

  test("ignore les messages vides", async () => {
    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.sendMessage("   ");
    });

    expect(mockSend).not.toHaveBeenCalled();
  });
});

describe("useCMChat — newSession", () => {
  test("réinitialise les messages et la session active", async () => {
    mockSend.mockResolvedValue({
      data: {
        session: { id: "s1" },
        message: { id: "m1", role: "assistant", content: "Hi" },
      },
    });

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.sendMessage("Hello");
    });

    act(() => {
      result.current.newSession();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.activeSession).toBeNull();
    expect(result.current.error).toBeNull();
  });
});

describe("useCMChat — deleteSession", () => {
  test("supprime la session et rafraîchit la liste", async () => {
    mockDeleteSession.mockResolvedValue({ data: { ok: true } });
    mockListSessions.mockResolvedValue({
      data: { sessions: [{ id: "s1" }, { id: "s2" }] },
    });

    const { result } = renderHook(() => useCMChat());

    await act(async () => {
      await result.current.loadSessions();
    });

    await act(async () => {
      await result.current.deleteSession("s1");
    });

    expect(result.current.sessions).toHaveLength(1);
    expect(result.current.sessions[0].id).toBe("s2");
  });
});
