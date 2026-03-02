/**
 * Tests du IlyasChatScreen
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import IlyasChatScreen from "@/screens/chat/IlyasChatScreen";
import { BrandContext } from "@/contexts/BrandContext";

const mockLoadSessions = jest.fn();
const mockSelectSession = jest.fn();
const mockSendMessage = jest.fn();
const mockNewSession = jest.fn();
const mockDeleteSession = jest.fn();
const mockSendImage = jest.fn();
const mockSendVoice = jest.fn();

let mockHookReturn: Record<string, any> = {};

jest.mock("@/hooks/useIlyasChat", () => ({
  useIlyasChat: () => mockHookReturn,
}));

jest.mock("@/lib/api", () => ({
  voiceApi: { transcribe: jest.fn() },
}));

jest.mock("@/lib/firebase", () => ({
  auth: {},
  db: {},
  storage: {},
}));

jest.mock("expo-image-picker", () => ({
  requestMediaLibraryPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
  launchImageLibraryAsync: jest.fn().mockResolvedValue({ canceled: true }),
  MediaTypeOptions: { Images: "Images" },
}));

jest.mock("expo-av", () => {
  const React = require("react");
  const { View } = require("react-native");
  return {
    Audio: {
      setAudioModeAsync: jest.fn(),
      Recording: jest.fn().mockImplementation(() => ({
        prepareToRecordAsync: jest.fn(),
        startAsync: jest.fn(),
        stopAndUnloadAsync: jest.fn(),
        getURI: jest.fn(() => "file://audio.m4a"),
      })),
      RecordingOptionsPresets: { HIGH_QUALITY: {} },
    },
    Video: React.forwardRef((props: any, ref: any) =>
      React.createElement(View, { testID: "expo-av-video", ...props })
    ),
    ResizeMode: { CONTAIN: "contain" },
  };
});

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: jest.fn(), navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

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
    sendImage: mockSendImage,
    sendVoice: mockSendVoice,
    newSession: mockNewSession,
    deleteSession: mockDeleteSession,
    ...overrides,
  };
}

function renderIlyas() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <IlyasChatScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  setHook();
});

describe("IlyasChatScreen — Header", () => {
  test("affiche le titre Ilyas", () => {
    renderIlyas();
    expect(screen.getByText("Ilyas, votre CM IA")).toBeTruthy();
  });

  test("appelle loadSessions au montage", () => {
    renderIlyas();
    expect(mockLoadSessions).toHaveBeenCalled();
  });
});

describe("IlyasChatScreen — Empty state", () => {
  test("affiche l'empty state sans messages", () => {
    renderIlyas();
    expect(screen.getByText(/Demandez-moi de creer des posts/)).toBeTruthy();
  });

  test("affiche le placeholder de saisie", () => {
    renderIlyas();
    expect(screen.getByPlaceholderText("Ecrivez a Ilyas...")).toBeTruthy();
  });
});

describe("IlyasChatScreen — Messages", () => {
  test("affiche les messages", () => {
    setHook({
      messages: [
        { id: "m1", session_id: "s1", role: "user", content: "Bonjour Ilyas", tokens_used: 0, created_at: "2026-01-01T10:00:00Z" },
        { id: "m2", session_id: "s1", role: "assistant", content: "Salut ! Comment puis-je vous aider ?", tokens_used: 30, created_at: "2026-01-01T10:00:05Z" },
      ],
    });
    renderIlyas();
    expect(screen.getByText("Bonjour Ilyas")).toBeTruthy();
    expect(screen.getByText("Salut ! Comment puis-je vous aider ?")).toBeTruthy();
  });
});

describe("IlyasChatScreen — Input", () => {
  test("send appelle sendMessage", () => {
    renderIlyas();
    const input = screen.getByPlaceholderText("Ecrivez a Ilyas...");
    fireEvent.changeText(input, "Crée un reel");
    fireEvent.press(screen.getByText("send"));
    expect(mockSendMessage.mock.calls[0][0]).toBe("Crée un reel");
  });
});

describe("IlyasChatScreen — Typing indicator", () => {
  test("affiche 'Ilyas reflechit...' quand isSending", () => {
    setHook({ isSending: true });
    renderIlyas();
    expect(screen.getByText("Ilyas reflechit...")).toBeTruthy();
  });
});

describe("IlyasChatScreen — Drawer", () => {
  test("ouvre le drawer avec le menu", () => {
    renderIlyas();
    fireEvent.press(screen.getByText("menu"));
    expect(screen.getByText("Conversations")).toBeTruthy();
    expect(screen.getByText("Nouvelle conversation")).toBeTruthy();
  });
});
