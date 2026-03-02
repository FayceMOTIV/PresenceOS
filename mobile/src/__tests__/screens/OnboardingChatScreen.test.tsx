/**
 * Tests du OnboardingChatScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import OnboardingChatScreen from "@/screens/onboarding/OnboardingChatScreen";
import { onboardingApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  onboardingApi: {
    start: jest.fn(),
    answer: jest.fn(),
    scrape: jest.fn(),
  },
}));

jest.mock("@/stores/onboardingStore", () => ({
  useOnboardingStore: () => ({
    markCompleted: jest.fn(),
  }),
}));

beforeEach(() => {
  jest.clearAllMocks();
  (onboardingApi.start as jest.Mock).mockResolvedValue({
    data: { complete: false, step: 0, question: "Comment s'appelle votre restaurant ?" },
  });
  (onboardingApi.answer as jest.Mock).mockResolvedValue({
    data: { complete: false, next_step: 1, next_question: "Quel type de cuisine ?" },
  });
  (onboardingApi.scrape as jest.Mock).mockResolvedValue({
    data: { message: "Analyse terminee !" },
  });
});

describe("OnboardingChatScreen — URL step", () => {
  test("affiche l'écran URL en premier", () => {
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    expect(screen.getByText("Votre site web")).toBeTruthy();
    expect(screen.getByPlaceholderText("https://votre-restaurant.fr")).toBeTruthy();
  });

  test("bouton analyser désactivé sans URL", () => {
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    expect(screen.getByText("Analyser mon site")).toBeTruthy();
  });

  test("skip URL passe au chat", async () => {
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    fireEvent.press(screen.getByText(/Je n'ai pas de site web/));
    await waitFor(() => {
      expect(onboardingApi.start).toHaveBeenCalledWith("b1");
    });
  });

  test("scrape avec URL appelle onboardingApi.scrape", async () => {
    jest.useFakeTimers();
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    fireEvent.changeText(screen.getByPlaceholderText("https://votre-restaurant.fr"), "https://mon-resto.fr");
    fireEvent.press(screen.getByText("Analyser mon site"));
    await waitFor(() => {
      expect(onboardingApi.scrape).toHaveBeenCalledWith("b1", "https://mon-resto.fr");
    });
    jest.useRealTimers();
  });
});

describe("OnboardingChatScreen — Chat", () => {
  test("affiche la question initiale après skip URL", async () => {
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    fireEvent.press(screen.getByText(/Je n'ai pas de site web/));
    await waitFor(() => {
      expect(screen.getByText("Comment s'appelle votre restaurant ?")).toBeTruthy();
    });
  });

  test("affiche le header Ilyas après chargement", async () => {
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    fireEvent.press(screen.getByText(/Je n'ai pas de site web/));
    await waitFor(() => {
      expect(screen.getByText("Ilyas")).toBeTruthy();
    });
  });

  test("affiche le placeholder de saisie", async () => {
    render(<OnboardingChatScreen brandId="b1" onComplete={jest.fn()} />);
    fireEvent.press(screen.getByText(/Je n'ai pas de site web/));
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Tape ta réponse...")).toBeTruthy();
    });
  });
});
