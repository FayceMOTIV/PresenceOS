// PresenceOS Mobile — Login Screen

import React, { useState, useContext, useEffect } from "react";
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
} from "react-native";
import * as Google from "expo-auth-session/providers/google";
import * as WebBrowser from "expo-web-browser";
import { AuthContext } from "@/contexts/BrandContext";
import { useAuthStore } from "@/stores/authStore";
import { Colors } from "@/constants/colors";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

WebBrowser.maybeCompleteAuthSession();

const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID ?? "";

type Props = {
  navigation?: NativeStackNavigationProp<any>;
};

export default function LoginScreen({ navigation }: Props) {
  const auth = useContext(AuthContext);
  const loginWithGoogle = useAuthStore((s) => s.loginWithGoogle);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const [, googleResponse, promptGoogleAsync] = Google.useAuthRequest({
    webClientId: GOOGLE_WEB_CLIENT_ID,
    iosClientId: GOOGLE_WEB_CLIENT_ID,
  });

  useEffect(() => {
    if (googleResponse?.type === "success") {
      const idToken = googleResponse.authentication?.idToken;
      if (idToken) {
        setGoogleLoading(true);
        loginWithGoogle(idToken)
          .catch((err: any) => {
            Alert.alert("Erreur Google", err?.message ?? "Connexion Google echouee");
          })
          .finally(() => setGoogleLoading(false));
      }
    }
  }, [googleResponse]);

  const handleLogin = async () => {
    if (!auth) return;
    if (!email.trim() || !password.trim()) {
      Alert.alert("Erreur", "Veuillez entrer votre email et mot de passe");
      return;
    }
    setLoading(true);
    try {
      await auth.login(email.trim(), password);
    } catch (err: any) {
      const code = err?.code as string | undefined;
      let msg = "Identifiants invalides";
      if (code === "auth/invalid-credential" || code === "auth/wrong-password" || code === "auth/user-not-found") {
        msg = "Email ou mot de passe incorrect";
      } else if (code === "auth/user-disabled") {
        msg = "Ce compte a ete desactive";
      } else if (code === "auth/too-many-requests") {
        msg = "Trop de tentatives, reessayez plus tard";
      } else if (code === "auth/invalid-email") {
        msg = "Adresse email invalide";
      } else if (err?.response?.data?.detail) {
        msg = err.response.data.detail;
      }
      Alert.alert("Connexion echouee", msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    if (!GOOGLE_WEB_CLIENT_ID) {
      Alert.alert("Erreur", "Google Sign-In non configure");
      return;
    }
    setGoogleLoading(true);
    try {
      await promptGoogleAsync();
    } catch {
      Alert.alert("Erreur", "Impossible de lancer Google Sign-In");
    } finally {
      setGoogleLoading(false);
    }
  };

  if (!auth) {
    return (
      <View style={styles.container}>
        <View style={styles.inner}>
          <Text style={styles.subtitle}>Chargement...</Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.inner}>
        <Text style={styles.logo}>RS3</Text>
        <Text style={styles.subtitle}>Connectez-vous a votre compte</Text>

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
          placeholder="Mot de passe"
          placeholderTextColor={Colors.text.muted}
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={loading || googleLoading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.buttonText}>Se connecter</Text>
          )}
        </TouchableOpacity>

        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>ou</Text>
          <View style={styles.dividerLine} />
        </View>

        <TouchableOpacity
          style={[styles.googleButton, googleLoading && styles.buttonDisabled]}
          onPress={handleGoogleLogin}
          disabled={loading || googleLoading}
        >
          {googleLoading ? (
            <ActivityIndicator color={Colors.text.primary} />
          ) : (
            <Text style={styles.googleButtonText}>Continuer avec Google</Text>
          )}
        </TouchableOpacity>

        {navigation && (
          <>
            <TouchableOpacity
              style={styles.forgotContainer}
              onPress={() => navigation.navigate("ForgotPassword")}
            >
              <Text style={styles.forgotText}>Mot de passe oublie ?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.linkContainer}
              onPress={() => navigation.navigate("Register")}
            >
              <Text style={styles.linkText}>
                Pas de compte ?{" "}
                <Text style={styles.linkBold}>Creer un compte</Text>
              </Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  inner: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 32,
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
  forgotContainer: {
    marginTop: 16,
    alignItems: "center",
  },
  forgotText: {
    color: Colors.brand.primary,
    fontSize: 14,
    fontWeight: "500",
  },
  linkContainer: {
    marginTop: 16,
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
  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border.default,
  },
  dividerText: {
    color: Colors.text.muted,
    fontSize: 13,
    marginHorizontal: 12,
  },
  googleButton: {
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
  },
  googleButtonText: {
    color: Colors.text.primary,
    fontSize: 16,
    fontWeight: "600",
  },
});
