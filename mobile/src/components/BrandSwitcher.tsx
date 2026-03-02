// PresenceOS Mobile — Brand Switcher (Bottom Sheet)
// Shows a list of user's brands with ability to switch

import React, { useCallback, useMemo } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { BottomSheetModal, BottomSheetView } from "@gorhom/bottom-sheet";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { useBusinessStore } from "@/stores/businessStore";

interface BrandSwitcherProps {
  bottomSheetRef: React.RefObject<BottomSheetModal | null>;
}

export default function BrandSwitcher({ bottomSheetRef }: BrandSwitcherProps) {
  const { brands, activeBrand, switchBusiness } = useBusinessStore();

  // Alias for compatibility
  const switchBrand = switchBusiness;

  // Dynamic snap points: 120px per brand + 80px header
  const snapPoints = useMemo(() => {
    const height = Math.min(brands.length * 72 + 80, 400);
    return [height];
  }, [brands.length]);

  const handleSelect = useCallback(
    (brandId: string) => {
      switchBrand(brandId);
      bottomSheetRef.current?.dismiss();
    },
    [switchBrand, bottomSheetRef]
  );

  return (
    <BottomSheetModal
      ref={bottomSheetRef}
      snapPoints={snapPoints}
      backgroundStyle={styles.sheetBg}
      handleIndicatorStyle={styles.indicator}
      enableDynamicSizing={false}
    >
      <BottomSheetView style={styles.content}>
        <Text style={styles.title}>Changer de marque</Text>

        {brands.map((brand) => {
          const isActive = brand.id === activeBrand?.id;
          const initials = brand.name
            .split(" ")
            .map((w) => w[0])
            .join("")
            .slice(0, 2)
            .toUpperCase();

          return (
            <TouchableOpacity
              key={brand.id}
              style={[styles.brandRow, isActive && styles.brandRowActive]}
              onPress={() => handleSelect(brand.id)}
              activeOpacity={0.7}
            >
              <View
                style={[
                  styles.avatar,
                  isActive && styles.avatarActive,
                ]}
              >
                <Text
                  style={[
                    styles.avatarText,
                    isActive && styles.avatarTextActive,
                  ]}
                >
                  {initials}
                </Text>
              </View>

              <View style={styles.brandInfo}>
                <Text style={styles.brandName}>{brand.name}</Text>
                <Text style={styles.brandType}>
                  {brand.brand_type || "Marque"}
                </Text>
              </View>

              {isActive && (
                <Ionicons
                  name="checkmark-circle"
                  size={22}
                  color={Colors.brand.primary}
                />
              )}
            </TouchableOpacity>
          );
        })}
      </BottomSheetView>
    </BottomSheetModal>
  );
}

const styles = StyleSheet.create({
  sheetBg: {
    backgroundColor: Colors.bg.secondary,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  indicator: {
    backgroundColor: Colors.text.muted,
    width: 40,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary,
    marginBottom: 16,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginBottom: 4,
  },
  brandRowActive: {
    backgroundColor: Colors.brand.glow,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: Colors.bg.elevated,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarActive: {
    backgroundColor: Colors.brand.primary,
  },
  avatarText: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text.secondary,
  },
  avatarTextActive: {
    color: Colors.text.inverted,
  },
  brandInfo: {
    flex: 1,
    marginLeft: 12,
  },
  brandName: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text.primary,
  },
  brandType: {
    fontSize: 12,
    color: Colors.text.muted,
    marginTop: 1,
  },
});
