import React, { useState, useRef } from "react";
import {
  Text, TextInput, TouchableOpacity, View, StyleSheet, ScrollView,
  KeyboardAvoidingView, Platform, ActivityIndicator, Animated
} from "react-native";
import { Eye, EyeOff, Phone, Lock, Shield, Truck, ArrowRight } from 'lucide-react-native';
import { theme } from "../styles";
import { driverLogin, getProfile } from "../api";

export default function LoginScreen({ onAuthenticated, onRegister }) {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [phoneFocused, setPhoneFocused] = useState(false);
  const [pinFocused, setPinFocused] = useState(false);
  const pinRef = useRef(null);

  const isValid = phone.length >= 9 && password.length >= 4;

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
              placeholder="Enter Password"
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
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scrollContent: { flexGrow: 1 },

  hero: { backgroundColor: theme.colors.sky, paddingTop: 60, paddingBottom: 50, borderBottomLeftRadius: 32, borderBottomRightRadius: 32 },
  heroInner: { alignItems: 'center' },
  logoRing: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.15)', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'rgba(255,255,255,0.25)' },
  logoInner: { width: 56, height: 56, borderRadius: 28, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center' },
  brand: { fontSize: 13, fontWeight: '700', color: 'rgba(255,255,255,0.7)', letterSpacing: 3, textTransform: 'uppercase', marginTop: 16 },
  heroTitle: { fontSize: 26, fontWeight: '900', color: '#FFF', marginTop: 4, letterSpacing: 0.5 },
  trustBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 12, backgroundColor: 'rgba(255,255,255,0.15)', paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20 },
  trustText: { fontSize: 11, fontWeight: '700', color: 'rgba(255,255,255,0.9)', letterSpacing: 0.5 },

  formCard: { marginHorizontal: 20, marginTop: -24, backgroundColor: '#FFF', borderRadius: 24, padding: 24, ...theme.shadows.md },
  welcomeText: { fontSize: 22, fontWeight: '800', color: theme.colors.dark },
  welcomeSub: { fontSize: 14, color: '#999', fontWeight: '500', marginTop: 4, marginBottom: 24 },

  inputGroup: { flexDirection: 'row', alignItems: 'center', height: 56, borderRadius: 16, backgroundColor: '#F8F9FA', marginBottom: 14, paddingHorizontal: 4, borderWidth: 2, borderColor: 'transparent' },
  inputGroupFocused: { borderColor: theme.colors.sky, backgroundColor: '#FFF' },
  inputIcon: { width: 40, alignItems: 'center' },
  countryCode: { flexDirection: 'row', alignItems: 'center' },
  codeText: { fontWeight: '700', color: theme.colors.dark, fontSize: 14 },
  inputDivider: { width: 1, height: 24, backgroundColor: '#E0E0E0', marginHorizontal: 10 },
  input: { flex: 1, fontSize: 16, fontWeight: '600', color: theme.colors.dark, paddingVertical: 0 },
  eyeBtn: { paddingHorizontal: 14 },

  forgotRow: { alignSelf: 'flex-end', marginBottom: 20, marginTop: 2 },
  forgotText: { color: theme.colors.sky, fontSize: 13, fontWeight: '700' },

  signInBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: theme.colors.sky, paddingVertical: 16, borderRadius: 16, ...theme.shadows.md },
  signInBtnDisabled: { backgroundColor: '#D0D0D0' },
  signInText: { color: '#FFF', fontSize: 17, fontWeight: '800', letterSpacing: 0.5 },

  registerRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 20 },
  registerText: { fontSize: 14, color: '#999', fontWeight: '500' },
  registerLink: { fontSize: 14, color: theme.colors.sky, fontWeight: '700' },

  errorBox: { backgroundColor: '#FFF5F5', borderWidth: 1, borderColor: '#FFCDD2', borderRadius: 14, padding: 14, marginBottom: 18 },
  errorText: { color: '#D32F2F', fontWeight: '700', textAlign: 'center', fontSize: 14 },

  footer: { paddingHorizontal: 20, paddingTop: 32, paddingBottom: 40, alignItems: 'center' },
  footerDivider: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  dividerLine: { flex: 1, height: 1, backgroundColor: '#E8E8E8' },
  dividerText: { fontSize: 10, fontWeight: '700', color: '#CCC', letterSpacing: 2 },
  statsRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  statItem: { alignItems: 'center' },
  statNum: { fontSize: 16, fontWeight: '900', color: theme.colors.dark },
  statLabel: { fontSize: 10, color: '#999', fontWeight: '600', marginTop: 2 },
  statDot: { width: 4, height: 4, borderRadius: 2, backgroundColor: '#DDD' },
  versionText: { fontSize: 11, color: '#DDD', fontWeight: '600', marginTop: 20 },
});
