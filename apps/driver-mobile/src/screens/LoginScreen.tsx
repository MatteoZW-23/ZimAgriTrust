import React, { useState, useRef, useEffect } from "react";
import {
  Text, TextInput, TouchableOpacity, View, StyleSheet, ScrollView,
  KeyboardAvoidingView, Platform, ActivityIndicator, Animated, Alert
} from "react-native";
import { Eye, EyeOff, Phone, Lock, Shield, Truck, ArrowRight, Fingerprint } from 'lucide-react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import { theme } from "../styles";
import { driverLogin, getProfile } from "../api";
import { getSession } from "../utils/auth";

export default function LoginScreen({ onAuthenticated, onRegister }) {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [phoneFocused, setPhoneFocused] = useState(false);
  const [pinFocused, setPinFocused] = useState(false);
  const pinRef = useRef(null);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricLoading, setBiometricLoading] = useState(false);

  const isValid = phone.length >= 9 && password.length >= 4;

  useEffect(() => {
    let mounted = true;
    async function checkBiometrics() {
      if (Platform.OS === 'web') {
        if (mounted) setBiometricAvailable(false);
        return;
      }
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      if (mounted) setBiometricAvailable(hasHardware && isEnrolled);
    }
    checkBiometrics();
    return () => {
      mounted = false;
    };
  }, []);

  const handleBiometricLogin = async () => {
    setBiometricLoading(true);
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Sign in to ZimAgriTrust Driver',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
      });
      if (!result.success) {
        throw new Error('Biometric authentication was cancelled or failed.');
      }
      const session = await getSession();
      if (!session?.access_token) {
        throw new Error('Sign in with phone and PIN once before using biometrics.');
      }
      const profile = session.profile || await getProfile(session.access_token);
      onAuthenticated({ ...session, profile });
    } catch (err) {
      Alert.alert('Biometric Failed', err.message || 'Could not authenticate with biometrics.');
    } finally {
      setBiometricLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!isValid) return;
    setLoading(true);
    setError("");
    try {
      const fullPhone = phone.startsWith('+') ? phone : `+263${phone.replace(/^0/, '')}`;
      const data = await driverLogin(fullPhone, password);
      const profile = await getProfile(data.access_token);
      onAuthenticated({ ...data, profile });
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        bounces={false}
      >
        {/* Hero Section */}
        <View style={styles.hero}>
          <View style={styles.heroInner}>
            <View style={styles.logoRing}>
              <View style={styles.logoInner}>
                <Truck size={36} color="#FFF" />
              </View>
            </View>
            <Text style={styles.brand}>ZimAgriTrust</Text>
            <Text style={styles.heroTitle}>Driver Portal</Text>
            <View style={styles.trustBadge}>
              <Shield size={12} color="rgba(255,255,255,0.9)" />
              <Text style={styles.trustText}>Secure & Encrypted</Text>
            </View>
          </View>
        </View>

        {/* Form Card */}
        <View style={styles.formCard}>
          <Text style={styles.welcomeText}>Welcome back</Text>
          <Text style={styles.welcomeSub}>Sign in to access your deliveries</Text>

          {error ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          {/* Phone Input */}
          <View style={[styles.inputGroup, phoneFocused && styles.inputGroupFocused]}>
            <View style={styles.inputIcon}>
              <Phone size={18} color={phoneFocused ? theme.colors.sky : '#999'} />
            </View>
            <View style={styles.countryCode}>
              <Text style={styles.codeText}>ZW +263</Text>
            </View>
            <View style={styles.inputDivider} />
            <TextInput
              style={styles.input}
              placeholder="77 123 4567"
              value={phone}
              onChangeText={(t) => { setPhone(t); setError(''); }}
              keyboardType="phone-pad"
              placeholderTextColor="#CCC"
              onFocus={() => setPhoneFocused(true)}
              onBlur={() => setPhoneFocused(false)}
              returnKeyType="next"
              onSubmitEditing={() => pinRef.current?.focus()}
            />
          </View>

          {/* PIN Input */}
          <View style={[styles.inputGroup, pinFocused && styles.inputGroupFocused]}>
            <View style={styles.inputIcon}>
              <Lock size={18} color={pinFocused ? theme.colors.sky : '#999'} />
            </View>
            <TextInput
              ref={pinRef}
              style={[styles.input, { flex: 1 }]}
              placeholder="Enter Pin"
              value={password}
              onChangeText={(t) => { setPassword(t); setError(''); }}
              secureTextEntry={!showPassword}
              placeholderTextColor="#CCC"
              onFocus={() => setPinFocused(true)}
              onBlur={() => setPinFocused(false)}
              onSubmitEditing={handleLogin}
            />
            <TouchableOpacity onPress={() => setShowPassword(v => !v)} style={styles.eyeBtn} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              {showPassword ? <EyeOff size={20} color="#999" /> : <Eye size={20} color="#999" />}
            </TouchableOpacity>
          </View>

          {/* Forgot */}
          <TouchableOpacity style={styles.forgotRow}>
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>

          {/* Biometric Login Button */}
          {biometricAvailable && (
            <TouchableOpacity
              style={styles.biometricBtn}
              onPress={handleBiometricLogin}
              disabled={biometricLoading}
              activeOpacity={0.8}
            >
              {biometricLoading ? (
                <ActivityIndicator color={theme.colors.sky} size="small" />
              ) : (
                <>
                  <Fingerprint size={20} color={theme.colors.sky} />
                  <Text style={styles.biometricText}>Sign in with Biometrics</Text>
                </>
              )}
            </TouchableOpacity>
          )}

          {/* Sign In Button */}
          <TouchableOpacity
            style={[styles.signInBtn, !isValid && styles.signInBtnDisabled]}
            onPress={handleLogin}
            disabled={loading || !isValid}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" size="small" />
            ) : (
              <>
                <Text style={styles.signInText}>Sign In</Text>
                <ArrowRight size={20} color="#FFF" />
              </>
            )}
          </TouchableOpacity>

          {/* Register */}
          <View style={styles.registerRow}>
            <Text style={styles.registerText}>New driver? </Text>
            <TouchableOpacity onPress={onRegister}>
              <Text style={styles.registerLink}>Register your vehicle</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <View style={styles.footerDivider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>TRUSTED PLATFORM</Text>
            <View style={styles.dividerLine} />
          </View>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statNum}>2,400+</Text>
              <Text style={styles.statLabel}>Active Drivers</Text>
            </View>
            <View style={styles.statDot} />
            <View style={styles.statItem}>
              <Text style={styles.statNum}>50K+</Text>
              <Text style={styles.statLabel}>Deliveries</Text>
            </View>
            <View style={styles.statDot} />
            <View style={styles.statItem}>
              <Text style={styles.statNum}>98%</Text>
              <Text style={styles.statLabel}>On-Time</Text>
            </View>
          </View>
          <Text style={styles.versionText}>v1.0.0</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.gray[100] },
  scrollContent: { flexGrow: 1 },

  hero: { backgroundColor: theme.colors.dark, paddingTop: 72, paddingBottom: 56, borderBottomLeftRadius: 36, borderBottomRightRadius: 36 },
  heroInner: { alignItems: 'center' },
  logoRing: { width: 88, height: 88, borderRadius: 30, backgroundColor: 'rgba(255,255,255,0.08)', justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: 'rgba(255,255,255,0.14)' },
  logoInner: { width: 60, height: 60, borderRadius: 22, backgroundColor: theme.colors.sky, justifyContent: 'center', alignItems: 'center', ...theme.shadows.sm },
  brand: { fontSize: 12, fontWeight: '800', color: 'rgba(255,255,255,0.64)', letterSpacing: 3.2, textTransform: 'uppercase', marginTop: 18 },
  heroTitle: { fontSize: 30, fontWeight: '900', color: '#FFF', marginTop: 6, letterSpacing: -0.4 },
  trustBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 14, backgroundColor: 'rgba(255,255,255,0.08)', paddingHorizontal: 14, paddingVertical: 7, borderRadius: 999 },
  trustText: { fontSize: 11, fontWeight: '800', color: 'rgba(255,255,255,0.88)', letterSpacing: 0.4 },

  formCard: { marginHorizontal: 18, marginTop: -26, backgroundColor: '#FFF', borderRadius: 28, padding: 24, borderWidth: 1, borderColor: theme.colors.gray[200], ...theme.shadows.lg },
  welcomeText: { fontSize: 24, fontWeight: '900', color: theme.colors.dark },
  welcomeSub: { fontSize: 14, color: theme.colors.gray[600], fontWeight: '500', marginTop: 4, marginBottom: 24 },

  inputGroup: { flexDirection: 'row', alignItems: 'center', height: 58, borderRadius: 18, backgroundColor: '#F8FAFC', marginBottom: 14, paddingHorizontal: 4, borderWidth: 1, borderColor: theme.colors.gray[200] },
  inputGroupFocused: { borderColor: theme.colors.sky, backgroundColor: '#FFF' },
  inputIcon: { width: 40, alignItems: 'center' },
  countryCode: { flexDirection: 'row', alignItems: 'center' },
  codeText: { fontWeight: '800', color: theme.colors.dark, fontSize: 14 },
  inputDivider: { width: 1, height: 24, backgroundColor: theme.colors.gray[300], marginHorizontal: 10 },
  input: { flex: 1, fontSize: 16, fontWeight: '600', color: theme.colors.dark, paddingVertical: 0 },
  eyeBtn: { paddingHorizontal: 14 },

  forgotRow: { alignSelf: 'flex-end', marginBottom: 20, marginTop: 2 },
  forgotText: { color: theme.colors.sky, fontSize: 13, fontWeight: '800' },

  biometricBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: theme.colors.infoTint, borderWidth: 1, borderColor: '#CFE0FF', paddingVertical: 15, borderRadius: 18, marginBottom: 12 },
  biometricText: { color: theme.colors.sky, fontSize: 15, fontWeight: '800' },

  signInBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: theme.colors.sky, paddingVertical: 17, borderRadius: 20, ...theme.shadows.md },
  signInBtnDisabled: { backgroundColor: theme.colors.gray[400] },
  signInText: { color: '#FFF', fontSize: 17, fontWeight: '900', letterSpacing: 0.3 },

  registerRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 20 },
  registerText: { fontSize: 14, color: theme.colors.gray[500], fontWeight: '500' },
  registerLink: { fontSize: 14, color: theme.colors.sky, fontWeight: '800' },

  errorBox: { backgroundColor: '#FFF5F5', borderWidth: 1, borderColor: '#FFCDD2', borderRadius: 16, padding: 14, marginBottom: 18 },
  errorText: { color: '#D32F2F', fontWeight: '800', textAlign: 'center', fontSize: 14 },

  footer: { paddingHorizontal: 20, paddingTop: 32, paddingBottom: 40, alignItems: 'center' },
  footerDivider: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  dividerLine: { flex: 1, height: 1, backgroundColor: theme.colors.gray[300] },
  dividerText: { fontSize: 10, fontWeight: '800', color: theme.colors.gray[400], letterSpacing: 2 },
  statsRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  statItem: { alignItems: 'center' },
  statNum: { fontSize: 16, fontWeight: '900', color: theme.colors.dark },
  statLabel: { fontSize: 10, color: theme.colors.gray[500], fontWeight: '700', marginTop: 2 },
  statDot: { width: 4, height: 4, borderRadius: 2, backgroundColor: theme.colors.gray[300] },
  versionText: { fontSize: 11, color: theme.colors.gray[400], fontWeight: '700', marginTop: 20 },
});
