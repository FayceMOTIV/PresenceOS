/**
 * Tests du BrandSwitcher
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import BrandSwitcher from "@/components/BrandSwitcher";
import { useBusinessStore } from "@/stores/businessStore";

jest.mock("@/stores/businessStore", () => ({
  useBusinessStore: jest.fn(),
}));

jest.mock("@/services/businessService", () => ({
  subscribeToMyBusinesses: jest.fn(),
}));

jest.mock("@/lib/firebase", () => ({
  db: {},
  storage: {},
}));

const mockDismiss = jest.fn();
const mockBottomSheetRef = { current: { dismiss: mockDismiss } } as any;

const mockSwitchBusiness = jest.fn();

function setupStore(overrides: Record<string, any> = {}) {
  (useBusinessStore as unknown as jest.Mock).mockReturnValue({
    brands: [
      { id: "b1", name: "Le Family's", brand_type: "restaurant" },
      { id: "b2", name: "Pizza Roma", brand_type: "restaurant" },
    ],
    activeBrand: { id: "b1", name: "Le Family's", brand_type: "restaurant" },
    switchBusiness: mockSwitchBusiness,
    ...overrides,
  });
}

beforeEach(() => {
  jest.clearAllMocks();
  setupStore();
});

describe("BrandSwitcher — Rendu", () => {
  test("affiche le titre 'Changer de marque'", () => {
    render(<BrandSwitcher bottomSheetRef={mockBottomSheetRef} />);
    expect(screen.getByText("Changer de marque")).toBeTruthy();
  });

  test("affiche les marques", () => {
    render(<BrandSwitcher bottomSheetRef={mockBottomSheetRef} />);
    expect(screen.getByText("Le Family's")).toBeTruthy();
    expect(screen.getByText("Pizza Roma")).toBeTruthy();
  });

  test("affiche les initiales", () => {
    render(<BrandSwitcher bottomSheetRef={mockBottomSheetRef} />);
    expect(screen.getByText("LF")).toBeTruthy();
    expect(screen.getByText("PR")).toBeTruthy();
  });

  test("affiche le type de marque", () => {
    render(<BrandSwitcher bottomSheetRef={mockBottomSheetRef} />);
    const types = screen.getAllByText("restaurant");
    expect(types.length).toBe(2);
  });
});

describe("BrandSwitcher — Sélection", () => {
  test("press sur une marque appelle switchBusiness et dismiss", () => {
    render(<BrandSwitcher bottomSheetRef={mockBottomSheetRef} />);
    // After render, useImperativeHandle overwrites ref.current with mock methods
    const dismiss = mockBottomSheetRef.current.dismiss;
    fireEvent.press(screen.getByText("Pizza Roma"));
    expect(mockSwitchBusiness).toHaveBeenCalledWith("b2");
    expect(dismiss).toHaveBeenCalled();
  });
});
