/**
 * Tests du composant ProposalCard
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import ProposalCard from "@/components/ProposalCard";
import type { AIProposal } from "@/types";

const makeProposal = (overrides: Partial<AIProposal> = {}): AIProposal => ({
  id: "prop-1",
  brand_id: "b1",
  proposal_type: "post",
  platform: "instagram",
  caption: "Découvrez notre nouveau plat signature ! 🍽️",
  hashtags: ["#restaurant", "#food"],
  image_url: "https://example.com/image.jpg",
  source: "ai",
  status: "pending",
  confidence_score: 0.87,
  created_at: "2026-03-01T10:00:00Z",
  ...overrides,
});

describe("ProposalCard", () => {
  test("affiche le caption tronqué", () => {
    const proposal = makeProposal();
    const onPress = jest.fn();
    render(<ProposalCard proposal={proposal} onPress={onPress} />);
    expect(screen.getByText(/Découvrez notre nouveau plat/)).toBeTruthy();
  });

  test("affiche le score de confiance en %", () => {
    const proposal = makeProposal({ confidence_score: 0.87 });
    render(<ProposalCard proposal={proposal} onPress={jest.fn()} />);
    expect(screen.getByText("87%")).toBeTruthy();
  });

  test("gère le onPress", () => {
    const onPress = jest.fn();
    render(<ProposalCard proposal={makeProposal()} onPress={onPress} />);
    fireEvent.press(screen.getByText(/Découvrez/));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  test("affiche le type de proposition", () => {
    render(
      <ProposalCard
        proposal={makeProposal({ proposal_type: "reel" })}
        onPress={jest.fn()}
      />
    );
    expect(screen.getByText("reel")).toBeTruthy();
  });

  test("utilise improved_image_url si disponible", () => {
    const proposal = makeProposal({
      image_url: "https://orig.com/img.jpg",
      improved_image_url: "https://improved.com/img.jpg",
    });
    const { toJSON } = render(
      <ProposalCard proposal={proposal} onPress={jest.fn()} />
    );
    const json = JSON.stringify(toJSON());
    expect(json).toContain("improved.com");
  });

  test("gère un statut published", () => {
    const proposal = makeProposal({ status: "published" });
    const { toJSON } = render(
      <ProposalCard proposal={proposal} onPress={jest.fn()} />
    );
    expect(toJSON()).toBeTruthy();
  });

  test("gère une image absente (gradient placeholder)", () => {
    const proposal = makeProposal({
      image_url: undefined,
      improved_image_url: undefined,
    });
    const { toJSON } = render(
      <ProposalCard proposal={proposal} onPress={jest.fn()} />
    );
    expect(toJSON()).toBeTruthy();
  });
});
