import React, { useState, useEffect } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet } from "react-native";
import { theme } from "../styles";
import { getProfile, login, register } from "../api";

export function LoginScreen({ role, onAuthenticated }) {
  const [subStep, setSubStep] = useState('phone'); // 'phone', 'otp', 'profile'
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [profileForm, setProfileForm] = useState({ name: "", location: "Harare", additional: "" });
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(45);

  useEffect(() => {
    if (subStep === 'otp' && timer > 0) {
      const t = setTimeout(() => setTimer(timer - 1), 1000);
      return () => clearTimeout(t);
    }
  }, [subStep, timer]);

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
            name: profileForm.name || "Tendai Moyo",
            phone: phone.startsWith('+') ? phone : `+263${phone}`,
            password: "password123",
            role: role?.toUpperCase() || "FARMER"
        };
        await register(payload);
        const data = await login(payload.phone, payload.password);
        const loadedProfile = await getProfile(data.access_token);
        onAuthenticated({ access_token: data.access_token, profile: loadedProfile });
    } catch (e) {
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

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
                placeholder="Tendai Moyo" 
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
