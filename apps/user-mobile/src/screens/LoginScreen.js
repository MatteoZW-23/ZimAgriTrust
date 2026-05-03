import React, { useState, useEffect } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet } from "react-native";
import { theme } from "../styles";
import { getProfile, login, register, forgotPassword, resetPassword } from "../api";

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

  const handleForgotRequest = async () => {
    if (forgotPhone.length < 9) return;
    setLoading(true); setError("");
    try {
      const fullPhone = forgotPhone.startsWith('+') ? forgotPhone : `+263${forgotPhone}`;
      await forgotPassword(fullPhone);
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
      await resetPassword(fullPhone, forgotOtp, newPin);
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
            full_name: profileForm.name,
            phone_number: phone.startsWith('+') ? phone : `+263${phone}`,
            password: otp.join(''),
            role: role?.toUpperCase() || "FARMER",
            location: profileForm.location || undefined,
        };
        await register(payload);
        const data = await login(payload.phone_number, payload.password);
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
          <View style={styles.iconContainer}>
            <Text style={styles.iconText}>KEY</Text>
          </View>
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
          <View style={styles.iconContainer}>
            <Text style={styles.iconText}>LOCK</Text>
          </View>
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
              <Text style={{ fontSize: 16, fontWeight: '700' }}>{showNewPin ? 'HIDE' : 'SHOW'}</Text>
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
            <View style={styles.iconContainer}>
              <Text style={styles.iconText}>PHONE</Text>
            </View>
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
            <View style={styles.iconContainer}>
              <Text style={styles.iconText}>CODE</Text>
            </View>
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
            <View style={styles.avatarPlaceholder}><Text style={{ fontSize: 16, fontWeight: '700' }}>CAM</Text></View>
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
  iconContainer: { width: 90, height: 90, borderRadius: 45, backgroundColor: 'rgba(46, 125, 50, 0.1)', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'rgba(46, 125, 50, 0.15)' },
  iconText: { fontSize: 18, fontWeight: '800', color: theme.colors.green, letterSpacing: 1 },
  title: { fontSize: 28, fontWeight: '800', color: theme.colors.black, marginTop: 28, textAlign: 'center', letterSpacing: 0.5 },
  subTitle: { fontSize: 16, color: '#666', marginTop: 12, textAlign: 'center', fontWeight: '500', lineHeight: 24 },
  form: { padding: 32 },
  phoneInputRow: { flexDirection: 'row', height: 64, borderRadius: 12, borderWeight: 1, borderColor: '#E0E0E0', backgroundColor: '#FFF', overflow: 'hidden', marginBottom: 24, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  countryCode: { width: 90, justifyContent: 'center', alignItems: 'center', borderRightWidth: 1, borderRightColor: '#E0E0E0', backgroundColor: '#F9F9F9' },
  codeText: { fontWeight: '700', color: theme.colors.black, fontSize: 16 },
  phoneInput: { flex: 1, paddingHorizontal: 16, fontSize: 16, fontWeight: '500' },
  primaryBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 12, alignItems: 'center', shadowColor: theme.colors.green, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 4 },
  primaryBtnText: { color: '#FFF', fontSize: 16, fontWeight: '700', letterSpacing: 1 },
  otpRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  otpBox: { width: 48, height: 56, borderRadius: 12, borderWidth: 2, borderColor: '#E0E0E0', justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFF' },
  otpInput: { fontSize: 24, fontWeight: '800', textAlign: 'center' },
  timerText: { textAlign: 'center', color: '#999', marginBottom: 32, fontWeight: '500', fontSize: 14 },
  avatarPlaceholder: { width: 110, height: 110, borderRadius: 55, backgroundColor: 'rgba(46, 125, 50, 0.1)', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'rgba(46, 125, 50, 0.15)' },
  label: { fontSize: 14, fontWeight: '700', color: theme.colors.black, marginBottom: 10, marginTop: 20, letterSpacing: 0.5 },
  input: { height: 56, borderRadius: 12, backgroundColor: '#FFF', paddingHorizontal: 18, fontSize: 16, fontWeight: '500', borderWidth: 1, borderColor: '#E0E0E0', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  chipRow: { flexDirection: 'row', gap: 10, marginTop: 12, marginBottom: 24 },
  chip: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, backgroundColor: '#F0F0F0', borderWidth: 1, borderColor: '#E0E0E0' }
});
