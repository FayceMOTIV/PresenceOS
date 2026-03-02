// PresenceOS Mobile — Register Screen

import React, { useState, useContext } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { AuthContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

type Props = {
  navigation: NativeStackNavigationProp<any>;
};

export default function RegisterScreen({ navigation }: Props) {
  const auth = useContext(AuthContext);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!auth) return;
    if (!fullName.trim()) {
      Alert.alert("Erreur", "Veuillez entrer votre nom complet");
      return;
    }
    if (!email.trim()) {
      Alert.alert("Erreur", "Veuillez entrer votre email");
      return;
    }
    if (password.length < 8) {
      Alert.alert("Erreur", "Le mot de passe doit contenir au moins 8 caractères");
      return;
    }
    setLoading(true);
    try {
      await auth.register(
        email.trim(),
        password,
        fullName.trim(),
        workspaceName.trim() || undefined
      );
    } catch (err: any) {
      const code = err?.code as string | undefined;
      let msg = "Impossible de créer le compte. Vérifiez vos informations.";
      if (code === "auth/email-already-in-use") {
        msg = "Un compte existe déjà avec cet email";
      } else if (code === "auth/invalid-email") {
        msg = "Adresse email invalide";
      } else if (code === "auth/weak-password") {
        msg = "Le mot de passe est trop faible (min. 6 caractères)";
      } else if (code === "auth/too-many-requests") {
        msg = "Trop de tentatives, réessayez plus tard";
      } else if (typeof err?.response?.data?.detail === "string") {
        msg = err.response.data.detail;
      }
      Alert.alert("Inscription échouée", msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.inner}>
          <Text style={styles.logo}>RS3</Text>
          <Text style={styles.subtitle}>Créer un compte</Text>

          <TextInput
            style={styles.input}
            placeholder="Nom complet"
            placeholderTextColor={Colors.text.muted}
            autoCapitalize="words"
            autoCorrect={false}
            value={fullName}
            onChangeText={setFullName}
          />

          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={Colors.text.muted}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            value={email}
            onChangeText={setEmail}
          />

          <TextInput
            style={styles.input}
            placeholder="Mot de passe (min. 8 caractères)"
            placeholderTextColor={Colors.text.muted}
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />

          <TextInput
            style={styles.input}
            placeholder="Nom du restaurant (optionnel)"
            placeholderTextColor={Colors.text.muted}
            autoCorrect={false}
            value={workspaceName}
            onChangeText={setWorkspaceName}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleRegister}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.buttonText}>Créer mon compte</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkContainer}
            onPress={() => navigation.navigate("Login")}
          >
            <Text style={styles.linkText}>
              Déjà un compte ?{" "}
              <Text style={styles.linkBold}>Se connecter</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  scroll: {
    flexGrow: 1,
  },
  inner: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 32,
    paddingVertical: 48,
  },
  logo: {
    fontSize: 32,
    fontWeight: "800",
    color: Colors.brand.primary,
    textAlign: "center",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.text.secondary,
    textAlign: "center",
    marginBottom: 32,
  },
  input: {
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Colors.text.primary,
    marginBottom: 12,
  },
  button: {
    backgroundColor: Colors.brand.primary,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "600",
  },
  linkContainer: {
    marginTop: 24,
    alignItems: "center",
  },
  linkText: {
    color: Colors.text.secondary,
    fontSize: 14,
  },
  linkBold: {
    color: Colors.brand.primary,
    fontWeight: "600",
  },
});
