import React, { useState, useEffect } from "react";
import logo from "../../assets/logo.png";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet, ActivityIndicator, Platform, KeyboardAvoidingView, Alert, Image } from "react-native";
import { theme } from "../styles";
import { getProfile, login, register, forgotPassword, resetPassword } from "../api";
import * as LocalAuthentication from 'expo-local-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Fingerprint, Eye, EyeOff, Lock, AlertCircle } from 'lucide-react-native';

export function LoginScreen({ role, onAuthenticated, onGuest, onRegister }) {
  const [subStep, setSubStep] = useState('phone');
  const [phone, setPhone] = useState("");
  const [loginPin, setLoginPin] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [profileForm, setProfileForm] = useState({ name: "", location: "", additional: "" });
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(45);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Biometric state
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [showPin, setShowPin] = useState(false);

  // Account lockout state
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [lockoutTime, setLockoutTime] = useState(0);
  const [isLocked, setIsLocked] = useState(false);

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

  // Check biometric availability on mount
  useEffect(() => {
    (async () => {
      try {
        const compatible = await LocalAuthentication.hasHardwareAsync();
        const enrolled = await LocalAuthentication.isEnrolledAsync();
        setBiometricAvailable(compatible && enrolled);
        
        const biometricPref = await AsyncStorage.getItem('biometric_enabled');
        setBiometricEnabled(biometricPref === 'true');
      } catch (err) {
        console.warn('Biometric check failed:', err);
      }
    })();
  }, []);

  // Check account lockout status
  useEffect(() => {
    (async () => {
      try {
        const lockoutData = await AsyncStorage.getItem('account_lockout');
        if (lockoutData) {
          const { timestamp, attempts } = JSON.parse(lockoutData);
          const elapsed = Date.now() - timestamp;
          
          if (elapsed < 15 * 60 * 1000) {
            setFailedAttempts(attempts);
            setLockoutTime(Math.ceil((15 * 60 * 1000 - elapsed) / 1000));
            setIsLocked(true);
          } else {
            await AsyncStorage.removeItem('account_lockout');
            setFailedAttempts(0);
            setIsLocked(false);
          }
        }
      } catch (err) {
        console.warn('Lockout check failed:', err);
      }
    })();
  }, []);

  // Lockout countdown
  useEffect(() => {
    if (isLocked && lockoutTime > 0) {
      const timer = setTimeout(() => setLockoutTime(lockoutTime - 1), 1000);
      return () => clearTimeout(timer);
    } else if (isLocked && lockoutTime === 0) {
      setIsLocked(false);
      setFailedAttempts(0);
      AsyncStorage.removeItem('account_lockout');
    }
  }, [isLocked, lockoutTime]);

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

  const handleSecureLogin = async () => {
    if (phone.length < 9 || loginPin.length < 4) return;
    
    if (isLocked) {
      setError(`Account locked. Try again in ${Math.floor(lockoutTime / 60)}:${(lockoutTime % 60).toString().padStart(2, '0')}`);
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const fullPhone = phone.startsWith('+') ? phone : `+263${phone.replace(/^0/, '')}`;
      const data = await login(fullPhone, loginPin);
      const loadedProfile = await getProfile(data.access_token);
      
      await AsyncStorage.removeItem('account_lockout');
      setFailedAttempts(0);
      setIsLocked(false);
      
      if (biometricAvailable && !biometricEnabled) {
        Alert.alert(
          'Enable Biometric Login?',
          'Use your fingerprint or Face ID for faster, secure access to your account.',
          [
            { text: 'Not Now', style: 'cancel' },
            { 
              text: 'Enable', 
              onPress: async () => {
                try {
                  const result = await LocalAuthentication.authenticateAsync({
                    promptMessage: 'Verify your identity',
                    fallbackLabel: 'Use PIN',
                  });
                  if (result.success) {
                    await AsyncStorage.setItem('biometric_enabled', 'true');
                    await AsyncStorage.setItem('biometric_phone', fullPhone);
                    await AsyncStorage.setItem('biometric_pin', loginPin);
                    setBiometricEnabled(true);
                  }
                } catch (err) {
                  console.warn('Biometric setup failed:', err);
                }
              }
            }
          ]
        );
      }
      
      onAuthenticated({ ...data, profile: loadedProfile });
    } catch (e) {
      const errorMsg = e.message || "Login failed. Check your phone and PIN.";
      setError(errorMsg);
      
      const newAttempts = failedAttempts + 1;
      setFailedAttempts(newAttempts);
      
      if (newAttempts >= 3) {
        setIsLocked(true);
        setLockoutTime(15 * 60);
        await AsyncStorage.setItem('account_lockout', JSON.stringify({
          timestamp: Date.now(),
          attempts: newAttempts
        }));
      } else {
        await AsyncStorage.setItem('account_lockout', JSON.stringify({
          timestamp: Date.now(),
          attempts: newAttempts
        }));
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleBiometricLogin = async () => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Login to ZimAgriTrust',
        fallbackLabel: 'Use PIN',
      });
      
      if (result.success) {
        setLoading(true);
        const savedPhone = await AsyncStorage.getItem('biometric_phone');
        const savedPin = await AsyncStorage.getItem('biometric_pin');
        
        if (savedPhone && savedPin) {
          const data = await login(savedPhone, savedPin);
          const loadedProfile = await getProfile(data.access_token);
          onAuthenticated({ ...data, profile: loadedProfile });
        }
      }
    } catch (err) {
      setError('Biometric authentication failed. Please use your PIN.');
    } finally {
      setLoading(false);
    }
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
            role: role?.toLowerCase() || "farmer",
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

  // --- Login Screen ---
  if (subStep === 'phone') {
    return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.header}>
            <View style={styles.iconContainer}>
              <Image
                source={logo}
                style={styles.logo}
                resizeMode="contain"
              />
            </View>
            <Text style={styles.title}>Welcome Back</Text>
            <Text style={styles.subTitle}>Login to access your ZimAgriTrust account</Text>
          </View>
          
          <View style={styles.form}>
            {error ? (
              <View style={styles.errorBanner}>
                <AlertCircle size={20} color="#ef4444" />
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}
            
            {isLocked && (
              <View style={styles.lockoutBanner}>
                <AlertCircle size={20} color="#f59e0b" />
                <Text style={styles.lockoutText}>
                  Account locked. Try again in {Math.floor(lockoutTime / 60)}:{(lockoutTime % 60).toString().padStart(2, '0')}
                </Text>
              </View>
            )}
            
            {biometricEnabled && (
              <TouchableOpacity 
                style={styles.biometricButton}
                onPress={handleBiometricLogin}
                disabled={loading}
              >
                <Fingerprint size={32} color={theme.colors.green} />
                <Text style={styles.biometricButtonText}>Use Biometric Login</Text>
              </TouchableOpacity>
            )}
            
            <View style={styles.phoneInputRow}>
              <View style={styles.countryCode}><Text style={styles.codeText}>+263</Text></View>
              <TextInput 
                style={styles.phoneInput} 
                placeholder="77 123 4567"
                keyboardType="phone-pad"
                value={phone}
                onChangeText={setPhone}
                maxLength={10}
              />
            </View>
            
            <Text style={styles.label}>Security PIN</Text>
            <View style={styles.pinInputContainer}>
              <TextInput
                style={styles.pinInput}
                placeholder="4-6 digit PIN"
                keyboardType="number-pad"
                maxLength={6}
                secureTextEntry={!showPin}
                value={loginPin}
                onChangeText={v => setLoginPin(v.replace(/[^0-9]/g, ''))}
              />
              <TouchableOpacity onPress={() => setShowPin(!showPin)} style={styles.eyeButton}>
                {showPin ? <EyeOff size={20} color="#999" /> : <Eye size={20} color="#999" />}
              </TouchableOpacity>
            </View>
            
            {!isLocked && failedAttempts > 0 && (
              <Text style={styles.attemptsText}>
                {3 - failedAttempts} attempts remaining
              </Text>
            )}
            
            <TouchableOpacity 
              style={[styles.primaryBtn, (phone.length < 9 || loginPin.length < 4 || isLocked) && styles.disabledBtn]} 
              onPress={handleSecureLogin}
              disabled={phone.length < 9 || loginPin.length < 4 || isLocked || loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.primaryBtnText}>Login</Text>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.registerBtn}
              onPress={onRegister}
            >
              <Text style={styles.registerBtnText}>Create New Account</Text>
            </TouchableOpacity>
            
            {onGuest && (
              <TouchableOpacity style={styles.guestBtn} onPress={onGuest}>
                <Text style={styles.guestBtnText}>Browse as Guest</Text>
              </TouchableOpacity>
            )}
            
            <TouchableOpacity style={styles.forgotBtn} onPress={() => { setSubStep('forgot'); setError(""); }}>
              <Text style={styles.forgotBtnText}>Forgot PIN?</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    );
  }

  // --- OTP Screen ---
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

  // --- Profile Screen ---
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
  scrollContent: { flexGrow: 1 },
  header: { alignItems: 'center', paddingTop: 80, paddingHorizontal: 32, paddingBottom: 20 },
  iconContainer: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(46, 125, 50, 0.1)', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'rgba(46, 125, 50, 0.15)' },
  logo: { width: 50, height: 50 },
  iconText: { fontSize: 18, fontWeight: '800', color: theme.colors.green, letterSpacing: 1 },
  title: { fontSize: 28, fontWeight: '800', color: theme.colors.black, marginTop: 24, textAlign: 'center', letterSpacing: 0.5 },
  subTitle: { fontSize: 16, color: '#666', marginTop: 12, textAlign: 'center', fontWeight: '500', lineHeight: 24 },
  form: { padding: 32, paddingTop: 0 },
  errorBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fee2e2', padding: 12, borderRadius: 8, marginBottom: 20 },
  errorText: { color: '#dc2626', marginLeft: 8, flex: 1, fontSize: 14, fontWeight: '600' },
  lockoutBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fef3c7', padding: 12, borderRadius: 8, marginBottom: 20 },
  lockoutText: { color: '#d97706', marginLeft: 8, flex: 1, fontSize: 14, fontWeight: '600' },
  biometricButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0fdf4', padding: 16, borderRadius: 12, borderWidth: 2, borderColor: theme.colors.green, marginBottom: 24 },
  biometricButtonText: { color: theme.colors.green, fontSize: 16, fontWeight: '700', marginLeft: 12 },
  phoneInputRow: { flexDirection: 'row', height: 56, borderRadius: 12, borderWidth: 1, borderColor: '#E0E0E0', backgroundColor: '#FFF', overflow: 'hidden', marginBottom: 24, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  countryCode: { width: 80, justifyContent: 'center', alignItems: 'center', borderRightWidth: 1, borderRightColor: '#E0E0E0', backgroundColor: '#F9F9F9' },
  codeText: { fontWeight: '700', color: theme.colors.black, fontSize: 16 },
  phoneInput: { flex: 1, paddingHorizontal: 16, fontSize: 16, fontWeight: '500' },
  label: { fontSize: 14, fontWeight: '700', color: theme.colors.black, marginBottom: 8, letterSpacing: 0.5 },
  pinInputContainer: { flexDirection: 'row', alignItems: 'center', height: 56, borderRadius: 12, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E0E0E0', marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  pinInput: { flex: 1, paddingHorizontal: 16, fontSize: 16, fontWeight: '500' },
  eyeButton: { padding: 16 },
  attemptsText: { fontSize: 12, color: '#ef4444', marginBottom: 16, textAlign: 'center', fontWeight: '600' },
  primaryBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 12, alignItems: 'center', shadowColor: theme.colors.green, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 4 },
  disabledBtn: { backgroundColor: '#CCC', shadowOpacity: 0 },
  primaryBtnText: { color: '#FFF', fontSize: 16, fontWeight: '700', letterSpacing: 1 },
  registerBtn: { marginTop: 12, paddingVertical: 16, borderRadius: 12, alignItems: 'center', borderWidth: 2, borderColor: theme.colors.green, backgroundColor: '#FFF' },
  registerBtnText: { color: theme.colors.green, fontSize: 15, fontWeight: '800' },
  guestBtn: { marginTop: 12, paddingVertical: 14, borderRadius: 12, alignItems: 'center', backgroundColor: '#F8FAFC' },
  guestBtnText: { color: '#475569', fontSize: 14, fontWeight: '800' },
  forgotBtn: { marginTop: 16, alignItems: 'center' },
  forgotBtnText: { color: '#64748b', fontSize: 13, fontWeight: '700' },
  otpRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  otpBox: { width: 48, height: 56, borderRadius: 12, borderWidth: 2, borderColor: '#E0E0E0', justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFF' },
  otpInput: { fontSize: 24, fontWeight: '800', textAlign: 'center' },
  timerText: { textAlign: 'center', color: '#999', marginBottom: 32, fontWeight: '500', fontSize: 14 },
  avatarPlaceholder: { width: 110, height: 110, borderRadius: 55, backgroundColor: 'rgba(46, 125, 50, 0.1)', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'rgba(46, 125, 50, 0.15)' },
  input: { height: 56, borderRadius: 12, backgroundColor: '#FFF', paddingHorizontal: 18, fontSize: 16, fontWeight: '500', borderWidth: 1, borderColor: '#E0E0E0', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  chipRow: { flexDirection: 'row', gap: 10, marginTop: 12, marginBottom: 24 },
  chip: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, backgroundColor: '#F0F0F0', borderWidth: 1, borderColor: '#E0E0E0' }
});
