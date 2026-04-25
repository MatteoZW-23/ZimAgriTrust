import React, { useState, useEffect } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet } from "react-native";
import { theme } from "../styles";
import { getProfile, login, register } from "../api";

export function LoginScreen({ role, onAuthenticated }) {
  const [subStep, setSubStep] = useState('phone'); // 'phone', 'otp', 'profile', 'forgot', 'forgot-reset'
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [profileForm, setProfileForm] = useState({ name: "", location: "", additional: "" });
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(45);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Forgot PIN state
  const [forgotPhone, setForgotPhone] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [newPin, setNewPin] = useState("");
  const [showNewPin, setShowNewPin] = useState(false);

  useEffect(() => {
    if (subStep === 'otp' && timer > 0) {
      const t = setTimeout(() => setTimer(timer - 1), 1000);
      return () => clearTimeout(t);
    }
  }, [subStep, timer]);

  const API_BASE = (process.env.EXPO_PUBLIC_API_URL || "http://localhost:8080/api/v1").replace(/\/$/, "");

  const handleForgotRequest = async () => {
    if (forgotPhone.length < 9) return;
    setLoading(true); setError("");
    try {
      const fullPhone = forgotPhone.startsWith('+') ? forgotPhone : `+263${forgotPhone}`;
      await fetch(`${API_BASE}/auth/forgot-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ phone_number: fullPhone }) });
      setSubStep('forgot-reset');
      setSuccessMsg("Reset code sent to your WhatsApp.");
    } catch (e) { setError("Failed to send code. Try again."); }
    finally { setLoading(false); }
  };

  const handleForgotReset = async () => {
    if (!forgotOtp || newPin.length < 4) return;
    setLoading(true); setError("");
    try {
      const fullPhone = forgotPhone.startsWith('+') ? forgotPhone : `+263${forgotPhone}`;
      const res = await fetch(`${API_BASE}/auth/reset-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ phone_number: fullPhone, otp: forgotOtp, new_password: newPin }) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || "Reset failed"); }
      setSuccessMsg("PIN updated! You can now log in.");
      setSubStep('phone'); setForgotPhone(""); setForgotOtp(""); setNewPin("");
    } catch (e) { setError(e.message || "Reset failed."); }
    finally { setLoading(false); }
  };

  const handleSendCode = () => {
    if (phone.length < 9) return;
    setLoading(true);
    setTimeout(() => {
        setLoading(false);
        setSubStep('otp');
    }, 1000);
  };

  const handleVerify = async () => {
    if (otp.join('').length < 6) return;
    setLoading(true);
    setTimeout(() => {
        setLoading(false);
        setSubStep('profile');
    }, 1000);
  };

  const handleCreateAccount = async () => {
    setLoading(true);
    try {
        const payload = {
            name: profileForm.name,
            phone: phone.startsWith('+') ? phone : `+263${phone}`,
            password: otp.join(''),
            role: role?.toUpperCase() || "FARMER"
        };
        await register(payload.name, payload.phone, payload.role, payload.password);
        const data = await login(payload.phone, payload.password);
        const loadedProfile = await getProfile(data.access_token);
        onAuthenticated({ access_token: data.access_token, profile: loadedProfile });
    } catch (e) {
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

  // --- Forgot PIN ---
  if (subStep === 'forgot') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={{ fontSize: 40 }}>🔑</Text>
          <Text style={styles.title}>Reset Your PIN</Text>
          <Text style={styles.subTitle}>Enter your phone number and we'll send a reset code via WhatsApp.</Text>
        </View>
        <View style={styles.form}>
          {error ? <Text style={{ color: '#ef4444', fontWeight: '700', marginBottom: 16, textAlign: 'center' }}>{error}</Text> : null}
          <View style={styles.phoneInputRow}>
            <View style={styles.countryCode}><Text style={styles.codeText}>+263</Text></View>
            <TextInput style={styles.phoneInput} placeholder="77 123 4567" keyboardType="phone-pad" value={forgotPhone} onChangeText={setForgotPhone} />
          </View>
          <TouchableOpacity style={[styles.primaryBtn, forgotPhone.length < 9 && { backgroundColor: '#CCC' }]} onPress={handleForgotRequest} disabled={forgotPhone.length < 9 || loading}>
            <Text style={styles.primaryBtnText}>{loading ? "Sending..." : "Send Reset Code"}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={{ marginTop: 16, alignItems: 'center' }} onPress={() => setSubStep('phone')}>
            <Text style={{ color: '#64748b', fontWeight: '700' }}>← Back to Login</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // --- Forgot PIN Reset ---
  if (subStep === 'forgot-reset') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={{ fontSize: 40 }}>🔐</Text>
          <Text style={styles.title}>Set New PIN</Text>
          <Text style={styles.subTitle}>{successMsg || "Enter the code from WhatsApp and your new PIN."}</Text>
        </View>
        <View style={styles.form}>
          {error ? <Text style={{ color: '#ef4444', fontWeight: '700', marginBottom: 16, textAlign: 'center' }}>{error}</Text> : null}
          <Text style={styles.label}>Verification Code</Text>
          <TextInput style={[styles.input, { textAlign: 'center', fontSize: 22, letterSpacing: 8 }]} placeholder="000000" keyboardType="number-pad" maxLength={6} value={forgotOtp} onChangeText={setForgotOtp} />
          <Text style={styles.label}>New PIN</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#F9F9F9', borderRadius: 16, marginBottom: 8 }}>
            <TextInput style={[styles.input, { flex: 1, marginBottom: 0, backgroundColor: 'transparent' }]} placeholder="4–6 digits" keyboardType="number-pad" maxLength={6} secureTextEntry={!showNewPin} value={newPin} onChangeText={v => setNewPin(v.replace(/[^0-9]/g, ''))} />
            <TouchableOpacity onPress={() => setShowNewPin(v => !v)} style={{ padding: 16 }}>
              <Text style={{ fontSize: 18 }}>{showNewPin ? '🙈' : '👁️'}</Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity style={[styles.primaryBtn, (!forgotOtp || newPin.length < 4) && { backgroundColor: '#CCC' }]} onPress={handleForgotReset} disabled={!forgotOtp || newPin.length < 4 || loading}>
            <Text style={styles.primaryBtnText}>{loading ? "Saving..." : "Set New PIN"}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // --- Step 5: Phone ---
  if (subStep === 'phone') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
            <Text style={{ fontSize: 40 }}>📱</Text>
            <Text style={styles.title}>Enter your mobile number</Text>
            <Text style={styles.subTitle}>We'll send you a verification code</Text>
        </View>
        <View style={styles.form}>
            <View style={styles.phoneInputRow}>
                <View style={styles.countryCode}><Text style={styles.codeText}>+263</Text></View>
                <TextInput 
                    style={styles.phoneInput} 
                    placeholder="77 123 4567"
                    keyboardType="phone-pad"
                    value={phone}
                    onChangeText={setPhone}
                />
            </View>
            <TouchableOpacity 
                style={[styles.primaryBtn, phone.length < 9 && { backgroundColor: '#CCC' }]} 
                onPress={handleSendCode}
                disabled={phone.length < 9 || loading}
            >
                <Text style={styles.primaryBtnText}>{loading ? "Sending..." : "Send Code"}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={{ marginTop: 16, alignItems: 'center' }} onPress={() => { setSubStep('forgot'); setError(""); }}>
              <Text style={{ color: '#64748b', fontSize: 13, fontWeight: '700' }}>Forgot PIN? Reset via WhatsApp</Text>
            </TouchableOpacity>
        </View>
      </View>
    );
  }

  // --- Step 6: OTP ---
  if (subStep === 'otp') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
            <Text style={{ fontSize: 40 }}>🔐</Text>
            <Text style={styles.title}>Verification</Text>
            <Text style={styles.subTitle}>Enter the 6-digit code sent to +263 {phone}</Text>
        </View>
        <View style={styles.form}>
            <View style={styles.otpRow}>
                {otp.map((val, i) => (
                    <View key={i} style={styles.otpBox}>
                        <TextInput 
                            style={styles.otpInput} 
                            maxLength={1} 
                            keyboardType="number-pad"
                            onChangeText={(v) => {
                                const newOtp = [...otp];
                                newOtp[i] = v;
                                setOtp(newOtp);
                            }}
                        />
                    </View>
                ))}
            </View>
            <Text style={styles.timerText}>
                {timer > 0 ? `Resend code in ${timer} seconds` : "Resend Code"}
            </Text>
            <TouchableOpacity style={styles.primaryBtn} onPress={handleVerify} disabled={loading}>
                <Text style={styles.primaryBtnText}>{loading ? "Verifying..." : "Verify"}</Text>
            </TouchableOpacity>
        </View>
      </View>
    );
  }

  // --- Step 7: Profile ---
  return (
    <ScrollView style={styles.container}>
        <View style={[styles.header, { paddingTop: 60 }]}>
            <View style={styles.avatarPlaceholder}><Text style={{ fontSize: 30 }}>📸</Text></View>
            <Text style={styles.title}>Create Profile</Text>
        </View>
        <View style={styles.form}>
            <Text style={styles.label}>Full Name</Text>
            <TextInput 
                style={styles.input} 
                placeholder="Your full name" 
                value={profileForm.name}
                onChangeText={v => setProfileForm({...profileForm, name: v})}
            />
            
            <Text style={styles.label}>Location</Text>
            <TextInput 
                style={styles.input} 
                placeholder="Province / District" 
                value={profileForm.location}
            />

            {role === 'farmer' && (
                <>
                    <Text style={styles.label}>Farm Size</Text>
                    <View style={styles.chipRow}>
                        {['Small', 'Medium', 'Large'].map(s => (
                            <TouchableOpacity key={s} style={styles.chip}><Text>{s}</Text></TouchableOpacity>
                        ))}
                    </View>
                </>
            )}

            <TouchableOpacity style={styles.primaryBtn} onPress={handleCreateAccount} disabled={loading}>
                <Text style={styles.primaryBtnText}>{loading ? "Creating..." : "Create Account"}</Text>
            </TouchableOpacity>
        </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { alignItems: 'center', paddingTop: 100, paddingHorizontal: 32 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.black, marginTop: 24, textAlign: 'center' },
  subTitle: { fontSize: 16, color: '#666', marginTop: 8, textAlign: 'center' },
  form: { padding: 32 },
  phoneInputRow: { flexDirection: 'row', height: 64, borderRadius: 16, borderWeight: 1, borderColor: '#EEE', backgroundColor: '#F9F9F9', overflow: 'hidden', marginBottom: 32 },
  countryCode: { width: 80, justifyContent: 'center', alignItems: 'center', borderRightWidth: 1, borderRightColor: '#EEE' },
  codeText: { fontWeight: '700', color: theme.colors.black },
  phoneInput: { flex: 1, paddingHorizontal: 16, fontSize: 18, fontWeight: '600' },
  primaryBtn: { backgroundColor: theme.colors.green, paddingVertical: 20, borderRadius: 20, alignItems: 'center' },
  primaryBtnText: { color: '#FFF', fontSize: 18, fontWeight: '800' },
  otpRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  otpBox: { width: 45, height: 55, borderRadius: 12, borderWidth: 2, borderColor: '#EEE', justifyContent: 'center', alignItems: 'center' },
  otpInput: { fontSize: 24, fontWeight: '800', textAlign: 'center' },
  timerText: { textAlign: 'center', color: '#999', marginBottom: 32 },
  avatarPlaceholder: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center' },
  label: { fontSize: 14, fontWeight: '800', color: theme.colors.black, marginBottom: 8, marginTop: 20 },
  input: { height: 60, borderRadius: 16, backgroundColor: '#F9F9F9', paddingHorizontal: 20, fontSize: 16 },
  chipRow: { flexDirection: 'row', gap: 10, marginTop: 10, marginBottom: 30 },
  chip: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 12, backgroundColor: '#F0F0F0' }
});
