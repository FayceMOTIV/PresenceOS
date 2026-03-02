// PresenceOS Mobile — Settings Screen

import React, { useContext } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { AuthContext, BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import Constants from "expo-constants";

function SettingsRow({
  icon,
  label,
  value,
  onPress,
  danger,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value?: string;
  onPress?: () => void;
  danger?: boolean;
}) {
  return (
    <TouchableOpacity
      style={styles.row}
      onPress={onPress}
      activeOpacity={onPress ? 0.6 : 1}
      disabled={!onPress}
    >
      <View style={styles.rowLeft}>
        <Ionicons
          name={icon}
          size={20}
          color={danger ? Colors.status.danger : Colors.text.secondary}
        />
        <Text style={[styles.rowLabel, danger && styles.rowLabelDanger]}>
          {label}
        </Text>
      </View>
      {value ? (
        <Text style={styles.rowValue}>{value}</Text>
      ) : onPress ? (
        <Ionicons name="chevron-forward" size={18} color={Colors.text.muted} />
      ) : null}
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const auth = useContext(AuthContext);
  const brand = useContext(BrandContext);
  const nav = useNavigation();
  const appVersion = Constants.expoConfig?.version ?? "1.0.0";
  const brandName = brand?.activeBrand?.name ?? "—";

  const handleLogout = () => {
    Alert.alert("Déconnexion", "Voulez-vous vous déconnecter ?", [
      { text: "Annuler", style: "cancel" },
      {
        text: "Se déconnecter",
        style: "destructive",
        onPress: () => auth?.logout(),
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => nav.goBack()}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <Text style={styles.title}>Paramètres</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Account section */}
        <Text style={styles.sectionTitle}>Compte</Text>
        <View style={styles.card}>
          <SettingsRow icon="business" label="Marque active" value={brandName} />
          <SettingsRow icon="shield-checkmark" label="Sécurité" value="JWT" />
        </View>

        {/* App section */}
        <Text style={styles.sectionTitle}>Application</Text>
        <View style={styles.card}>
          <SettingsRow icon="information-circle" label="Version" value={`v${appVersion}`} />
          <SettingsRow icon="notifications" label="Notifications" value="Activées" />
        </View>

        {/* Danger zone */}
        <View style={[styles.card, { marginTop: 32 }]}>
          <SettingsRow
            icon="log-out"
            label="Se déconnecter"
            onPress={handleLogout}
            danger
          />
        </View>

        <Text style={styles.footer}>
          PresenceOS v{appVersion}
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  title: {
    fontSize: 17,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  scroll: {
    flex: 1,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.text.muted,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginTop: 24,
    marginBottom: 8,
    marginLeft: 4,
  },
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border.default,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border.default,
  },
  rowLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  rowLabel: {
    fontSize: 15,
    color: Colors.text.primary,
    fontWeight: "500",
  },
  rowLabelDanger: {
    color: Colors.status.danger,
  },
  rowValue: {
    fontSize: 14,
    color: Colors.text.secondary,
  },
  footer: {
    textAlign: "center",
    color: Colors.text.muted,
    fontSize: 12,
    marginTop: 32,
    marginBottom: 48,
  },
});
