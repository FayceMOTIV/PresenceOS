/**
 * Tests du CMChatScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import CMChatScreen from "@/screens/cm/CMChatScreen";

const mockLoadSessions = jest.fn();
const mockSelectSession = jest.fn();
const mockSendMessage = jest.fn();
const mockNewSession = jest.fn();
const mockDeleteSession = jest.fn();

let mockHookReturn: Record<string, any> = {};

jest.mock("@/hooks/useCMChat", () => ({
  useCMChat: () => mockHookReturn,
}));

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: jest.fn(), navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

function setHook(overrides: Record<string, any> = {}) {
  mockHookReturn = {
    sessions: [],
    activeSession: null,
    messages: [],
    isLoading: false,
    isSending: false,
    error: null,
    loadSessions: mockLoadSessions,
    selectSession: mockSelectSession,
    sendMessage: mockSendMessage,
    newSession: mockNewSession,
    deleteSession: mockDeleteSession,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  setHook();
});

describe("CMChatScreen — Header", () => {
  test("affiche le titre par défaut 'CM Chat IA'", () => {
    render(<CMChatScreen />);
    expect(screen.getByText("CM Chat IA")).toBeTruthy();
  });

  test("affiche le titre de la session active", () => {
    setHook({
      activeSession: { id: "s1", title: "Ma conversation", message_count: 5 },
    });
    render(<CMChatScreen />);
    expect(screen.getByText("Ma conversation")).toBeTruthy();
    expect(screen.getByText("5 messages")).toBeTruthy();
  });

  test("appelle loadSessions au montage", () => {
    render(<CMChatScreen />);
    expect(mockLoadSessions).toHaveBeenCalled();
  });
});

describe("CMChatScreen — Empty state", () => {
  test("affiche l'empty state quand pas de messages", () => {
    render(<CMChatScreen />);
    expect(screen.getByText("Votre Community Manager IA")).toBeTruthy();
    expect(screen.getByText(/Demandez-moi de créer des posts/)).toBeTruthy();
  });

  test("affiche les quick prompts", () => {
    render(<CMChatScreen />);
    expect(screen.getByText("Reel pour ce weekend")).toBeTruthy();
    expect(screen.getByText("Post plat du jour")).toBeTruthy();
    expect(screen.getByText("Story promo")).toBeTruthy();
    expect(screen.getByText("Idée de contenu")).toBeTruthy();
  });

  test("quick prompt remplit le champ de texte", () => {
    render(<CMChatScreen />);
    fireEvent.press(screen.getByText("Post plat du jour"));
    const input = screen.getByPlaceholderText("Écrivez votre message...");
    expect(input.props.value).toBe("Post plat du jour");
  });
});

describe("CMChatScreen — Messages", () => {
  test("affiche les messages user et assistant", () => {
    setHook({
      messages: [
        { id: "m1", session_id: "s1", role: "user", content: "Crée un reel", tokens_used: 0, created_at: "2026-01-01T10:00:00Z" },
        { id: "m2", session_id: "s1", role: "assistant", content: "Voici votre Reel", tokens_used: 50, created_at: "2026-01-01T10:00:05Z" },
      ],
    });
    render(<CMChatScreen />);
    expect(screen.getByText("Crée un reel")).toBeTruthy();
    expect(screen.getByText("Voici votre Reel")).toBeTruthy();
  });

  test("affiche ProposalBubble quand message a des proposals", () => {
    setHook({
      messages: [
        {
          id: "m1",
          session_id: "s1",
          role: "assistant",
          content: "Voici ma proposition",
          tokens_used: 50,
          created_at: "2026-01-01T10:00:00Z",
          proposals: [{ caption: "Venez goûter !", hashtags: ["#food"], platform: "instagram" }],
        },
      ],
    });
    render(<CMChatScreen />);
    expect(screen.getByText("Proposition IA")).toBeTruthy();
    expect(screen.getByText("Venez goûter !")).toBeTruthy();
    expect(screen.getByText("instagram")).toBeTruthy();
  });
});

describe("CMChatScreen — Input & Send", () => {
  test("affiche le placeholder du champ de saisie", () => {
    render(<CMChatScreen />);
    expect(screen.getByPlaceholderText("Écrivez votre message...")).toBeTruthy();
  });

  test("envoyer appelle sendMessage", () => {
    render(<CMChatScreen />);
    const input = screen.getByPlaceholderText("Écrivez votre message...");
    fireEvent.changeText(input, "Hello IA");
    fireEvent.press(screen.getByText("send"));
    expect(mockSendMessage).toHaveBeenCalledWith("Hello IA");
  });

  test("bouton send est disabled quand texte vide", () => {
    render(<CMChatScreen />);
    // send button should not trigger sendMessage without text
    fireEvent.press(screen.getByText("send"));
    expect(mockSendMessage).not.toHaveBeenCalled();
  });
});

describe("CMChatScreen — Typing indicator", () => {
  test("affiche l'indicateur de frappe quand isSending", () => {
    setHook({ isSending: true });
    render(<CMChatScreen />);
    expect(screen.getByText("L'IA réfléchit...")).toBeTruthy();
  });

  test("n'affiche pas l'indicateur quand pas en envoi", () => {
    setHook({ isSending: false });
    render(<CMChatScreen />);
    expect(screen.queryByText("L'IA réfléchit...")).toBeNull();
  });
});

describe("CMChatScreen — Error", () => {
  test("affiche la bannière d'erreur", () => {
    setHook({ error: "Connexion perdue" });
    render(<CMChatScreen />);
    expect(screen.getByText("Connexion perdue")).toBeTruthy();
    expect(screen.getByText("Réessayer")).toBeTruthy();
  });

  test("retry appelle loadSessions", () => {
    setHook({ error: "Erreur" });
    render(<CMChatScreen />);
    fireEvent.press(screen.getByText("Réessayer"));
    // loadSessions called on mount + retry
    expect(mockLoadSessions).toHaveBeenCalledTimes(2);
  });
});

describe("CMChatScreen — Drawer", () => {
  test("ouvre le drawer avec le bouton menu", () => {
    render(<CMChatScreen />);
    fireEvent.press(screen.getByText("menu"));
    expect(screen.getByText("Conversations")).toBeTruthy();
    expect(screen.getByText("Nouvelle conversation")).toBeTruthy();
  });

  test("drawer affiche les sessions", () => {
    setHook({
      sessions: [
        { id: "s1", title: "Session 1", message_count: 3 },
        { id: "s2", title: "Session 2", message_count: 7 },
      ],
    });
    render(<CMChatScreen />);
    fireEvent.press(screen.getByText("menu"));
    expect(screen.getByText("Session 1")).toBeTruthy();
    expect(screen.getByText("3 msg")).toBeTruthy();
    expect(screen.getByText("Session 2")).toBeTruthy();
    expect(screen.getByText("7 msg")).toBeTruthy();
  });

  test("drawer vide affiche 'Aucune conversation'", () => {
    setHook({ sessions: [] });
    render(<CMChatScreen />);
    fireEvent.press(screen.getByText("menu"));
    expect(screen.getByText("Aucune conversation")).toBeTruthy();
  });

  test("new session button appelle newSession", () => {
    render(<CMChatScreen />);
    // Both header "create-outline" icon and drawer "Nouvelle conversation"
    fireEvent.press(screen.getByText("create-outline"));
    expect(mockNewSession).toHaveBeenCalled();
  });
});

describe("CMChatScreen — Loading", () => {
  test("affiche le spinner quand isLoading", () => {
    setHook({ isLoading: true });
    render(<CMChatScreen />);
    // ActivityIndicator rendered — no empty state or messages
    expect(screen.queryByText("Votre Community Manager IA")).toBeNull();
  });
});
