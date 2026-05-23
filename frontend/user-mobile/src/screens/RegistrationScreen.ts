import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet,
  ActivityIndicator, Alert, Platform, Image, KeyboardAvoidingView,
  Modal, Animated
} from 'react-native';
import {
  Phone as IconPhone, Lock as IconLock, User as IconUser,
  CheckCircle as IconCheckCircle, ArrowRight as IconArrowRight,
  ArrowLeft as IconArrowLeft, Camera as IconCamera, Upload as IconUpload,
  Shield as IconShield, Wheat as IconWheat, ShoppingBag as IconShoppingBag,
  AlertCircle as IconAlertCircle
} from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import * as LocalAuthentication from 'expo-local-authentication';
import { theme } from '../styles';
import { register, requestOtp, verifyOtp } from '../api';

const PROVINCES = ['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Masvingo', 'Marondera', 'Chinhoyi'];
const DISTRICTS = {
  'Harare': ['Harare Central', 'Budiriro', 'Mbare', 'Highfield', 'Mabelreign'],
  'Bulawayo': ['Bulawayo Central', 'Nkulumane', 'Makokoba', 'Luveve', 'Pumula'],
  'Mutare': ['Mutare Central', 'Sakubva', 'Dangamvura', 'Chikanga'],
  'Gweru': ['Gweru Central', 'Mkoba', 'Senga', 'Ascot'],
  'Masvingo': ['Masvingo Central', 'Mucheke', 'Rujeko', 'Zimre Park'],
  'Marondera': ['Marondera Central', 'Ruzawi', 'Watershed'],
  'Chinhoyi': ['Chinhoyi Central', 'Mhangura', 'Karoi']
};

const CROPS = [
  'Maize', 'Sorghum', 'Millet', 'Wheat', 'Rice', 'Beans', 'Cowpeas',
  'Groundnuts', 'Soybeans', 'Sunflower', 'Cotton', 'Tobacco',
  'Tomatoes', 'Onions', 'Potatoes', 'Cabbage', 'Spinach', 'Carrots',
  'Butternut', 'Pumpkin', 'Sugarcane', 'Bananas', 'Citrus', 'Mangoes',
  'Avocados', 'Papayas', 'Guavas', 'Apples', 'Peaches', 'Pears'
];

export default function RegistrationScreen({ onRegistered, onBack }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  
  // Step 1: Phone Verification
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [otpSent, setOtpSent] = useState(false);
  const [otpCooldown, setOtpCooldown] = useState(0);
  const otpRefs = useRef([]);
  
  // Step 2: PIN
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  
  // Step 3: Role Selection
  const [role, setRole] = useState('');
  
  // Step 4: Personal Information
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [province, setProvince] = useState('');
  const [district, setDistrict] = useState('');
  const [address, setAddress] = useState('');
  
  // Step 5: ID Verification
  const [idFront, setIdFront] = useState(null);
  const [idBack, setIdBack] = useState(null);
  const [selfieWithId, setSelfieWithId] = useState(null);
  const [skipVerification, setSkipVerification] = useState(false);
  
  // Biometric prompt
  const [showBiometricPrompt, setShowBiometricPrompt] = useState(false);

  useEffect(() => {
    if (otpCooldown > 0) {
      const timer = setTimeout(() => setOtpCooldown(otpCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [otpCooldown]);

  const validatePhone = () => {
    const digits = phone.replace(/\D/g, '');
    return digits.length === 10;
  };

  const handleSendOtp = async () => {
    if (!validatePhone()) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const fullPhone = phone.startsWith('+') ? phone : `+263${phone.replace(/^0/, '')}`;
      await requestOtp(fullPhone);
      setOtpSent(true);
      setOtpCooldown(60);
      setSuccessMsg('OTP sent to your phone');
    } catch (err) {
      setError(err.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      setError('Please enter the complete 6-digit OTP');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const fullPhone = phone.startsWith('+') ? phone : `+263${phone.replace(/^0/, '')}`;
      await verifyOtp(fullPhone, otpCode);
      setSuccessMsg('Phone verified successfully');
      setTimeout(() => {
        setStep(2);
        setSuccessMsg('');
      }, 1000);
    } catch (err) {
      setError(err.message || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (value.length > 1) value = value[0];
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const validatePin = (pinValue) => {
    if (pinValue.length < 4 || pinValue.length > 6) return false;
    // No sequential digits
    for (let i = 0; i < pinValue.length - 1; i++) {
      if (parseInt(pinValue[i + 1]) === parseInt(pinValue[i]) + 1) return false;
    }
    // No repeated digits
    if (/^(\d)\1+$/.test(pinValue)) return false;
    return true;
  };

  const handlePinSubmit = () => {
    if (!validatePin(pin)) {
      setError('PIN must be 4-6 digits with no sequential or repeated digits');
      return;
    }
    if (pin !== confirmPin) {
      setError('PINs do not match');
      return;
    }
    setStep(3);
    setError('');
  };

  const handleRoleSelect = (selectedRole) => {
    setRole(selectedRole);
    setTimeout(() => setStep(4), 300);
  };

  const handlePersonalInfoSubmit = () => {
    if (!fullName || fullName.length < 2) {
      setError('Please enter your full name');
      return;
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }
    if (!province || !district || !address) {
      setError('Please complete all location fields');
      return;
    }
    setStep(5);
    setError('');
  };

  const pickImage = async (setImage) => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please grant camera roll permissions');
      return;
    }
    
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });
    
    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  const takePhoto = async (setImage) => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please grant camera permissions');
      return;
    }
    
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });
    
    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  const handleIdVerificationSubmit = async () => {
    if (skipVerification) {
      await completeRegistration();
      return;
    }
    
    if (!idFront || !idBack || !selfieWithId) {
      setError('Please upload all required documents');
      return;
    }
    
    await completeRegistration();
  };

  const completeRegistration = async () => {
    setLoading(true);
    setError('');
    try {
      const fullPhone = phone.startsWith('+') ? phone : `+263${phone.replace(/^0/, '')}`;
      
      const userData = {
        phone: fullPhone,
        pin,
        role,
        full_name: fullName,
        email: email || null,
        province,
        district,
        address,
        id_verified: !skipVerification,
        id_front: idFront,
        id_back: idBack,
        selfie_with_id: selfieWithId
      };
      
      const result = await register(userData);
      setSuccessMsg('Registration successful!');
      
      // Check for biometric support
      const compatible = await LocalAuthentication.hasHardwareAsync();
      if (compatible) {
        setShowBiometricPrompt(true);
      } else {
        setTimeout(() => onRegistered(result), 1500);
      }
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricSetup = async () => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Enable biometric login for faster access',
        fallbackLabel: 'Use PIN',
      });
      
      if (result.success) {
        // Store biometric preference
        setShowBiometricPrompt(false);
        Alert.alert('Success', 'Biometric login enabled!', [
          { text: 'OK', onPress: () => onRegistered({ success: true }) }
        ]);
      } else {
        setShowBiometricPrompt(false);
        onRegistered({ success: true });
      }
    } catch (err) {
      setShowBiometricPrompt(false);
      onRegistered({ success: true });
    }
  };

  const renderStep1 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <IconPhone size={48} color={theme.colors.sky} />
        <Text style={styles.stepTitle}>Phone Verification</Text>
        <Text style={styles.stepSubtitle}>Step 1 of 6</Text>
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Phone Number</Text>
        <View style={styles.phoneInputContainer}>
          <Text style={styles.countryCode}>+263</Text>
          <TextInput
            style={styles.phoneInput}
            placeholder="7XX XXX XXX"
            placeholderTextColor="#999"
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            maxLength={10}
          />
        </View>
      </View>
      
      {otpSent ? (
        <View style={styles.otpContainer}>
          <Text style={styles.otpLabel}>Enter 6-digit OTP</Text>
          <View style={styles.otpInputs}>
            {otp.map((digit, index) => (
              <TextInput
                key={index}
                ref={ref => otpRefs.current[index] = ref}
                style={styles.otpInput}
                value={digit}
                onChangeText={(value) => handleOtpChange(index, value)}
                keyboardType="number-pad"
                maxLength={1}
                textAlign="center"
                secureTextEntry
              />
            ))}
          </View>
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={handleSendOtp}
            disabled={otpCooldown > 0}
          >
            <Text style={styles.secondaryButtonText}>
              {otpCooldown > 0 ? `Resend in ${otpCooldown}s` : 'Resend OTP'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={handleVerifyOtp}
          >
            <Text style={styles.primaryButtonText}>Verify OTP</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleSendOtp}
          disabled={loading || !validatePhone()}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.primaryButtonText}>Send OTP</Text>
          )}
        </TouchableOpacity>
      )}
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <IconLock size={48} color={theme.colors.sky} />
        <Text style={styles.stepTitle}>Create PIN</Text>
        <Text style={styles.stepSubtitle}>Step 2 of 6</Text>
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={styles.label}>PIN (4-6 digits)</Text>
        <View style={styles.pinInputContainer}>
          <TextInput
            style={styles.pinInput}
            value={pin}
            onChangeText={setPin}
            keyboardType="number-pad"
            maxLength={6}
            secureTextEntry={!showPin}
            placeholder="••••"
          />
          <TouchableOpacity onPress={() => setShowPin(!showPin)}>
            <IconLock size={20} color="#999" />
          </TouchableOpacity>
        </View>
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Confirm PIN</Text>
        <TextInput
          style={styles.input}
          value={confirmPin}
          onChangeText={setConfirmPin}
          keyboardType="number-pad"
          maxLength={6}
          secureTextEntry
          placeholder="••••"
        />
      </View>
      
      <View style={styles.pinRules}>
        <Text style={styles.pinRulesTitle}>PIN Requirements:</Text>
        <Text style={styles.pinRule}>• 4-6 digits</Text>
        <Text style={styles.pinRule}>• No sequential digits (1234)</Text>
        <Text style={styles.pinRule}>• No repeated digits (1111)</Text>
      </View>
      
      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={handlePinSubmit}
        disabled={!pin || !confirmPin}
      >
        <Text style={styles.primaryButtonText}>Confirm PIN</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <IconUser size={48} color={theme.colors.sky} />
        <Text style={styles.stepTitle}>Select Your Role</Text>
        <Text style={styles.stepSubtitle}>Step 3 of 6</Text>
      </View>
      
      <TouchableOpacity
        style={[styles.roleCard, role === 'farmer' && styles.roleCardSelected]}
        onPress={() => handleRoleSelect('farmer')}
      >
        <IconWheat size={64} color={role === 'farmer' ? theme.colors.green : '#999'} />
        <Text style={styles.roleTitle}>👨‍🌾 Farmer</Text>
        <Text style={styles.roleDescription}>
          Sell your crops directly to buyers. Get better prices and faster payments.
        </Text>
        {role === 'farmer' && <IconCheckCircle size={24} color={theme.colors.green} />}
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.roleCard, role === 'buyer' && styles.roleCardSelected]}
        onPress={() => handleRoleSelect('buyer')}
      >
        <IconShoppingBag size={64} color={role === 'buyer' ? theme.colors.sky : '#999'} />
        <Text style={styles.roleTitle}>🛒 Buyer</Text>
        <Text style={styles.roleDescription}>
          Browse and purchase quality produce directly from farmers. Fresh and affordable.
        </Text>
        {role === 'buyer' && <IconCheckCircle size={24} color={theme.colors.sky} />}
      </TouchableOpacity>
    </View>
  );

  const renderStep4 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <IconUser size={48} color={theme.colors.sky} />
        <Text style={styles.stepTitle}>Personal Information</Text>
        <Text style={styles.stepSubtitle}>Step 4 of 6</Text>
      </View>
      
      <ScrollView style={styles.formScroll}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Full Name *</Text>
          <TextInput
            style={styles.input}
            value={fullName}
            onChangeText={setFullName}
            placeholder="Enter your full name"
          />
        </View>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Email (Optional)</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            placeholder="your@email.com"
            autoCapitalize="none"
          />
        </View>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Province *</Text>
          <View style={styles.pickerContainer}>
            {PROVINCES.map((prov) => (
              <TouchableOpacity
                key={prov}
                style={[styles.pickerItem, province === prov && styles.pickerItemSelected]}
                onPress={() => { setProvince(prov); setDistrict(''); }}
              >
                <Text style={[styles.pickerItemText, province === prov && styles.pickerItemTextSelected]}>
                  {prov}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        
        {province && (
          <View style={styles.inputGroup}>
            <Text style={styles.label}>District *</Text>
            <View style={styles.pickerContainer}>
              {DISTRICTS[province]?.map((dist) => (
                <TouchableOpacity
                  key={dist}
                  style={[styles.pickerItem, district === dist && styles.pickerItemSelected]}
                  onPress={() => setDistrict(dist)}
                >
                  <Text style={[styles.pickerItemText, district === dist && styles.pickerItemTextSelected]}>
                    {dist}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Address *</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={address}
            onChangeText={setAddress}
            placeholder="Enter your full address"
            multiline
            numberOfLines={3}
            maxLength={200}
          />
          <Text style={styles.charCount}>{address.length}/200</Text>
        </View>
      </ScrollView>
      
      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={handlePersonalInfoSubmit}
      >
        <Text style={styles.primaryButtonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep5 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <IconShield size={48} color={theme.colors.sky} />
        <Text style={styles.stepTitle}>ID Verification</Text>
        <Text style={styles.stepSubtitle}>Step 5 of 6 - Optional</Text>
      </View>
      
      <View style={styles.verificationInfo}>
        <IconAlertCircle size={24} color={theme.colors.gold} />
        <Text style={styles.verificationInfoText}>
          Verify your ID to increase your trust score by +15 points and unlock higher listing limits.
        </Text>
      </View>
      
      <ScrollView style={styles.formScroll}>
        <View style={styles.uploadSection}>
          <Text style={styles.uploadLabel}>National ID - Front</Text>
          {idFront ? (
            <Image source={{ uri: idFront }} style={styles.uploadedImage} />
          ) : (
            <View style={styles.uploadPlaceholder}>
              <IconUpload size={40} color="#999" />
              <Text style={styles.uploadPlaceholderText}>Tap to upload</Text>
            </View>
          )}
          <View style={styles.uploadButtons}>
            <TouchableOpacity
              style={styles.uploadButton}
              onPress={() => pickImage(setIdFront)}
            >
              <Text style={styles.uploadButtonText}>Gallery</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.uploadButton, styles.uploadButtonCamera]}
              onPress={() => takePhoto(setIdFront)}
            >
              <IconCamera size={16} color="#fff" />
              <Text style={styles.uploadButtonText}>Camera</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        <View style={styles.uploadSection}>
          <Text style={styles.uploadLabel}>National ID - Back</Text>
          {idBack ? (
            <Image source={{ uri: idBack }} style={styles.uploadedImage} />
          ) : (
            <View style={styles.uploadPlaceholder}>
              <IconUpload size={40} color="#999" />
              <Text style={styles.uploadPlaceholderText}>Tap to upload</Text>
            </View>
          )}
          <View style={styles.uploadButtons}>
            <TouchableOpacity
              style={styles.uploadButton}
              onPress={() => pickImage(setIdBack)}
            >
              <Text style={styles.uploadButtonText}>Gallery</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.uploadButton, styles.uploadButtonCamera]}
              onPress={() => takePhoto(setIdBack)}
            >
              <IconCamera size={16} color="#fff" />
              <Text style={styles.uploadButtonText}>Camera</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        <View style={styles.uploadSection}>
          <Text style={styles.uploadLabel}>Selfie with ID</Text>
          <Text style={styles.uploadHint}>Hold your ID clearly visible next to your face</Text>
          {selfieWithId ? (
            <Image source={{ uri: selfieWithId }} style={styles.uploadedImage} />
          ) : (
            <View style={styles.uploadPlaceholder}>
              <IconCamera size={40} color="#999" />
              <Text style={styles.uploadPlaceholderText}>Take selfie with ID</Text>
            </View>
          )}
          <TouchableOpacity
            style={[styles.uploadButton, styles.uploadButtonFull]}
            onPress={() => takePhoto(setSelfieWithId)}
          >
            <IconCamera size={16} color="#fff" />
            <Text style={styles.uploadButtonText}>Take Photo</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
      
      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={handleIdVerificationSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.primaryButtonText}>
            {skipVerification ? 'Skip Verification' : 'Submit Verification'}
          </Text>
        )}
      </TouchableOpacity>
      
      {!skipVerification && (
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={() => setSkipVerification(true)}
        >
          <Text style={styles.secondaryButtonText}>Skip for Now</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const renderStep6 = () => (
    <View style={styles.stepContainer}>
      <View style={styles.stepHeader}>
        <IconCheckCircle size={64} color={theme.colors.green} />
        <Text style={styles.stepTitle}>Registration Complete!</Text>
      </View>
      
      <View style={styles.successCard}>
        <Text style={styles.successMessage}>
          Your account has been created successfully!
        </Text>
        
        <View style={styles.trustScoreCard}>
          <Text style={styles.trustScoreLabel}>Trust Score</Text>
          <Text style={styles.trustScoreValue}>
            {skipVerification ? '50/100' : '65/100'}
          </Text>
          {!skipVerification && (
            <Text style={styles.trustScoreBonus}>+15 ID Verification Bonus</Text>
          )}
        </View>
        
        <Text style={styles.nextSteps}>
          You can now log in and start using ZimAgriTrust.
        </Text>
      </View>
      
      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={() => onBack()}
      >
        <Text style={styles.primaryButtonText}>Go to Login</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <IconArrowLeft size={24} color="#333" />
        </TouchableOpacity>
        
        {error && (
          <View style={styles.errorBanner}>
            <IconAlertCircle size={20} color="#fff" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
        
        {successMsg && (
          <View style={styles.successBanner}>
            <IconCheckCircle size={20} color="#fff" />
            <Text style={styles.successText}>{successMsg}</Text>
          </View>
        )}
        
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
        {step === 4 && renderStep4()}
        {step === 5 && renderStep5()}
        {step === 6 && renderStep6()}
        
        {/* Biometric Prompt Modal */}
        <Modal
          visible={showBiometricPrompt}
          transparent
          animationType="fade"
          onRequestClose={() => setShowBiometricPrompt(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <IconShield size={64} color={theme.colors.sky} />
              <Text style={styles.modalTitle}>Enable Biometric Login?</Text>
              <Text style={styles.modalText}>
                Use your fingerprint or Face ID for faster, secure access to your account.
              </Text>
              <TouchableOpacity
                style={[styles.button, styles.primaryButton]}
                onPress={handleBiometricSetup}
              >
                <Text style={styles.primaryButtonText}>Enable</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.secondaryButton]}
                onPress={() => {
                  setShowBiometricPrompt(false);
                  onRegistered({ success: true });
                }}
              >
                <Text style={styles.secondaryButtonText}>Skip</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  backButton: {
    alignSelf: 'flex-start',
    marginBottom: 20,
    padding: 8,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fee2e2',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#dc2626',
    marginLeft: 8,
    flex: 1,
  },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#dcfce7',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  successText: {
    color: '#16a34a',
    marginLeft: 8,
    flex: 1,
  },
  stepContainer: {
    flex: 1,
  },
  stepHeader: {
    alignItems: 'center',
    marginBottom: 32,
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
    marginTop: 16,
    textAlign: 'center',
  },
  stepSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  phoneInputContainer: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f9f9f9',
  },
  countryCode: {
    padding: 12,
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
    borderRightWidth: 1,
    borderRightColor: '#ddd',
  },
  phoneInput: {
    flex: 1,
    padding: 12,
    fontSize: 16,
  },
  otpContainer: {
    alignItems: 'center',
  },
  otpLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  otpInputs: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  otpInput: {
    width: 48,
    height: 56,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
    backgroundColor: '#f9f9f9',
  },
  pinInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f9f9f9',
  },
  pinInput: {
    flex: 1,
    padding: 12,
    fontSize: 16,
  },
  pinRules: {
    backgroundColor: '#f0f9ff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  pinRulesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0369a1',
    marginBottom: 8,
  },
  pinRule: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
  },
  roleCard: {
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 16,
    position: 'relative',
  },
  roleCardSelected: {
    borderColor: theme.colors.sky,
    backgroundColor: '#f0f9ff',
  },
  roleTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginTop: 12,
  },
  roleDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  formScroll: {
    maxHeight: 400,
    marginBottom: 16,
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: 12,
    color: '#999',
    textAlign: 'right',
    marginTop: 4,
  },
  pickerContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pickerItem: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    backgroundColor: '#f9f9f9',
  },
  pickerItemSelected: {
    borderColor: theme.colors.sky,
    backgroundColor: theme.colors.sky,
  },
  pickerItemText: {
    fontSize: 14,
    color: '#333',
  },
  pickerItemTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  verificationInfo: {
    flexDirection: 'row',
    backgroundColor: '#fef9c3',
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  verificationInfoText: {
    flex: 1,
    fontSize: 13,
    color: '#854d0e',
    marginLeft: 8,
  },
  uploadSection: {
    marginBottom: 24,
  },
  uploadLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  uploadHint: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  uploadPlaceholder: {
    height: 150,
    borderWidth: 2,
    borderColor: '#ddd',
    borderStyle: 'dashed',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
  },
  uploadPlaceholderText: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
  },
  uploadedImage: {
    width: '100%',
    height: 150,
    borderRadius: 8,
  },
  uploadButtons: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  uploadButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    gap: 6,
  },
  uploadButtonCamera: {
    backgroundColor: theme.colors.sky,
  },
  uploadButtonFull: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    backgroundColor: theme.colors.sky,
    borderRadius: 8,
    gap: 8,
  },
  uploadButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  button: {
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  primaryButton: {
    backgroundColor: theme.colors.sky,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  secondaryButtonText: {
    color: '#666',
    fontSize: 14,
    fontWeight: '600',
  },
  successCard: {
    backgroundColor: '#f0fdf4',
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 24,
  },
  successMessage: {
    fontSize: 16,
    color: '#16a34a',
    textAlign: 'center',
    marginBottom: 20,
  },
  trustScoreCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    marginBottom: 16,
  },
  trustScoreLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  trustScoreValue: {
    fontSize: 36,
    fontWeight: '800',
    color: theme.colors.green,
  },
  trustScoreBonus: {
    fontSize: 12,
    color: '#16a34a',
    marginTop: 4,
  },
  nextSteps: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    width: '100%',
    maxWidth: 320,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
});
