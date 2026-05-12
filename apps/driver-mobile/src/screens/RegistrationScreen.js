import React, { useState, useRef } from "react";
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Alert, Platform, Image,
} from "react-native";
import {
  Phone, Lock, User, Truck, FileText, Camera,
  CheckCircle, ArrowRight, ArrowLeft, Upload,
} from "lucide-react-native";
import { theme } from "../styles";
import { API_BASE_URL } from "../api";

const STEPS = [
  { id: 1, title: "Phone Verification", icon: Phone },
  { id: 2, title: "Create PIN",         icon: Lock },
  { id: 3, title: "Personal Info",      icon: User },
  { id: 4, title: "Vehicle Info",       icon: Truck },
  { id: 5, title: "Documents",          icon: FileText },
  { id: 6, title: "Live Selfie",        icon: Camera },
];

const DOCUMENT_SLOTS = [
  { key: "national_id_front",      label: "National ID – Front" },
  { key: "national_id_back",       label: "National ID – Back" },
  { key: "license_front",          label: "Driver's License – Front" },
  { key: "license_back",           label: "Driver's License – Back" },
  { key: "vehicle_registration",   label: "Vehicle Registration" },
  { key: "vehicle_photo",          label: "Vehicle Photo (plate visible)" },
  { key: "profile_photo",          label: "Profile Photo" },
];

async function post(path, body, token = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST", headers, body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Request failed");
  return data;
}

export default function RegistrationScreen({ onRegistered, onBack }) {
  const [step, setStep]                 = useState(1);
  const [phone, setPhone]               = useState("");
  const [otp, setOtp]                   = useState("");
  const [otpSent, setOtpSent]           = useState(false);
  const [otpVerified, setOtpVerified]   = useState(false);
  const [tempToken, setTempToken]        = useState(null);
  const [pin, setPin]                   = useState("");
  const [confirmPin, setConfirmPin]     = useState("");
  const [firstName, setFirstName]       = useState("");
  const [lastName, setLastName]         = useState("");
  const [dob, setDob]                   = useState("");
  const [address, setAddress]           = useState("");
  const [vehicleType, setVehicleType]   = useState("");
  const [plateNumber, setPlateNumber]   = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [vehicleYear, setVehicleYear]   = useState("");
  const [documents, setDocuments]       = useState({});
  const [selfie, setSelfie]             = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState("");

  const fullPhone = phone.startsWith("+")
    ? phone
    : `+263${phone.replace(/^0/, "")}`;

  // ── Step 1: OTP ──────────────────────────────────────────────────────────
  async function sendOtp() {
    if (phone.length < 9) return setError("Enter a valid phone number");
    setLoading(true); setError("");
    try {
      await post("/auth/driver/request-otp", { phone_number: fullPhone });
      setOtpSent(true);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  async function verifyOtp() {
    if (otp.length < 4) return setError("Enter the OTP code");
    setLoading(true); setError("");
    try {
      const data = await post("/auth/driver/verify-otp", {
        phone_number: fullPhone, otp,
      });
      setTempToken(data.temp_token);
      setOtpVerified(true);
      setStep(2);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  // ── Step 2: PIN ──────────────────────────────────────────────────────────
  function validatePin() {
    if (pin.length < 4 || pin.length > 6) return "PIN must be 4–6 digits";
    if (pin !== confirmPin) return "PINs do not match";
    if (/^(\d)\1+$/.test(pin)) return "PIN cannot be all same digits";
    if (/0123|1234|2345|3456|4567|5678|6789/.test(pin)) return "PIN cannot be sequential";
    return null;
  }

  // ── Step 5: Docs (stub picker – opens alert on non-native) ───────────────
  function pickDocument(key) {
    if (Platform.OS === "web") {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "image/*,application/pdf";
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) setDocuments((d) => ({ ...d, [key]: { name: file.name, uri: URL.createObjectURL(file), file } }));
      };
      input.click();
    } else {
      Alert.alert("Camera / Gallery", "Use expo-image-picker in native build", [{ text: "OK" }]);
    }
  }

  // ── Final submit ─────────────────────────────────────────────────────────
  async function submit() {
    setLoading(true); setError("");
    try {
      const form = new FormData();
      form.append("phone_number", fullPhone);
      form.append("pin", pin);
      form.append("first_name", firstName);
      form.append("last_name", lastName);
      form.append("date_of_birth", dob);
      form.append("address", address);
      form.append("vehicle_type", vehicleType);
      form.append("plate_number", plateNumber);
      form.append("vehicle_model", vehicleModel);
      form.append("vehicle_year", vehicleYear);

      DOCUMENT_SLOTS.forEach(({ key }) => {
        if (documents[key]) {
          if (Platform.OS === "web") {
            form.append(key, documents[key].file, documents[key].name);
          } else {
            form.append(key, { uri: documents[key].uri, name: `${key}.jpg`, type: "image/jpeg" });
          }
        }
      });

      if (selfie) {
        if (Platform.OS === "web") form.append("live_selfie", selfie.file, selfie.name);
        else form.append("live_selfie", { uri: selfie.uri, name: "selfie.jpg", type: "image/jpeg" });
      }

      const res = await fetch(`${API_BASE_URL}/drivers/register`, {
        method: "POST",
        headers: { Authorization: `Bearer ${tempToken}` },
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Registration failed");
      onRegistered(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  // ── Navigation guards ────────────────────────────────────────────────────
  function nextStep() {
    setError("");
    if (step === 1 && !otpVerified) return setError("Verify your phone first");
    if (step === 2) {
      const err = validatePin();
      if (err) return setError(err);
    }
    if (step === 3) {
      if (!firstName || !lastName || !dob) return setError("Fill in all personal details");
    }
    if (step === 4) {
      if (!vehicleType || !plateNumber) return setError("Fill in vehicle details");
    }
    if (step === 5) {
      const missing = DOCUMENT_SLOTS.filter((s) => !documents[s.key]);
      if (missing.length > 0) return setError(`Upload: ${missing.map((s) => s.label).join(", ")}`);
    }
    if (step === 6) {
      if (!selfie) return setError("Take your live selfie");
      submit();
      return;
    }
    setStep((s) => s + 1);
  }

  // ── Render step content ──────────────────────────────────────────────────
  function renderStep() {
    switch (step) {
      case 1: return (
        <View>
          <Text style={s.label}>Phone Number</Text>
          <TextInput
            style={s.input} value={phone} onChangeText={setPhone}
            placeholder="+263 77 xxx xxxx" keyboardType="phone-pad" editable={!otpSent}
          />
          {!otpSent ? (
            <TouchableOpacity style={s.btn} onPress={sendOtp} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Send OTP</Text>}
            </TouchableOpacity>
          ) : (
            <>
              <Text style={s.label}>Enter OTP</Text>
              <TextInput
                style={s.input} value={otp} onChangeText={setOtp}
                placeholder="6-digit code" keyboardType="number-pad" maxLength={6}
              />
              <TouchableOpacity style={s.btn} onPress={verifyOtp} disabled={loading}>
                {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Verify OTP</Text>}
              </TouchableOpacity>
              {otpVerified && <Text style={s.success}>✓ Phone verified</Text>}
            </>
          )}
        </View>
      );

      case 2: return (
        <View>
          <Text style={s.hint}>PIN must be 4–6 digits. No sequential or repeated digits.</Text>
          <Text style={s.label}>Create PIN</Text>
          <TextInput style={s.input} value={pin} onChangeText={setPin}
            placeholder="4–6 digit PIN" keyboardType="number-pad" secureTextEntry maxLength={6} />
          <Text style={s.label}>Confirm PIN</Text>
          <TextInput style={s.input} value={confirmPin} onChangeText={setConfirmPin}
            placeholder="Repeat PIN" keyboardType="number-pad" secureTextEntry maxLength={6} />
        </View>
      );

      case 3: return (
        <View>
          {[
            { label: "First Name",     val: firstName,  set: setFirstName },
            { label: "Last Name",      val: lastName,   set: setLastName },
            { label: "Date of Birth",  val: dob,        set: setDob,        placeholder: "YYYY-MM-DD" },
            { label: "Home Address",   val: address,    set: setAddress },
          ].map(({ label, val, set, placeholder }) => (
            <View key={label}>
              <Text style={s.label}>{label}</Text>
              <TextInput style={s.input} value={val} onChangeText={set}
                placeholder={placeholder || label} />
            </View>
          ))}
        </View>
      );

      case 4: return (
        <View>
          <Text style={s.label}>Vehicle Type</Text>
          <View style={s.chipRow}>
            {["Pickup", "Truck", "Lorry", "Van", "Bakkie"].map((t) => (
              <TouchableOpacity key={t}
                style={[s.chip, vehicleType === t && s.chipActive]}
                onPress={() => setVehicleType(t)}>
                <Text style={[s.chipText, vehicleType === t && s.chipTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>
          {[
            { label: "Plate Number",   val: plateNumber,   set: setPlateNumber },
            { label: "Make & Model",   val: vehicleModel,  set: setVehicleModel, placeholder: "e.g. Toyota Hilux" },
            { label: "Year",           val: vehicleYear,   set: setVehicleYear,  placeholder: "e.g. 2020" },
          ].map(({ label, val, set, placeholder }) => (
            <View key={label}>
              <Text style={s.label}>{label}</Text>
              <TextInput style={s.input} value={val} onChangeText={set} placeholder={placeholder || label} />
            </View>
          ))}
        </View>
      );

      case 5: return (
        <View>
          <Text style={s.hint}>Upload all 7 documents. Clear photos required for approval.</Text>
          {DOCUMENT_SLOTS.map(({ key, label }) => (
            <TouchableOpacity key={key} style={[s.docSlot, documents[key] && s.docSlotDone]}
              onPress={() => pickDocument(key)}>
              <Upload size={18} color={documents[key] ? theme.colors.sky : "#999"} />
              <Text style={[s.docLabel, documents[key] && { color: theme.colors.sky }]}>
                {documents[key] ? `✓ ${label}` : label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      );

      case 6: return (
        <View style={{ alignItems: "center" }}>
          <Text style={s.hint}>
            Take a selfie holding your National ID + Driver's License + a handwritten note with today's date.
          </Text>
          {selfie ? (
            <View style={{ alignItems: "center" }}>
              {Platform.OS === "web" && selfie.uri && (
                <Image source={{ uri: selfie.uri }} style={s.selfiePreview} />
              )}
              <Text style={[s.success, { marginTop: 8 }]}>✓ Selfie uploaded</Text>
            </View>
          ) : null}
          <TouchableOpacity style={[s.btn, { marginTop: 16 }]}
            onPress={() => {
              if (Platform.OS === "web") {
                const input = document.createElement("input");
                input.type = "file"; input.accept = "image/*";
                input.onchange = (e) => {
                  const file = e.target.files[0];
                  if (file) setSelfie({ name: file.name, uri: URL.createObjectURL(file), file });
                };
                input.click();
              } else {
                Alert.alert("Camera", "Use expo-camera in native build");
              }
            }}>
            <Camera size={18} color="#fff" />
            <Text style={s.btnText}> {selfie ? "Retake Selfie" : "Take Selfie"}</Text>
          </TouchableOpacity>
        </View>
      );

      default: return null;
    }
  }

  const currentStep = STEPS[step - 1];
  const StepIcon = currentStep.icon;

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
      {/* Progress bar */}
      <View style={s.progressBar}>
        {STEPS.map((st) => (
          <View key={st.id}
            style={[s.progressDot, step >= st.id && s.progressDotActive,
              step > st.id && s.progressDotDone]} />
        ))}
      </View>

      {/* Header */}
      <View style={s.stepHeader}>
        <View style={s.stepIcon}><StepIcon size={28} color="#fff" /></View>
        <Text style={s.stepTitle}>{currentStep.title}</Text>
        <Text style={s.stepCount}>Step {step} of {STEPS.length}</Text>
      </View>

      {/* Error */}
      {!!error && <View style={s.errorBox}><Text style={s.errorText}>{error}</Text></View>}

      {/* Step content */}
      <View style={s.card}>{renderStep()}</View>

      {/* Navigation */}
      <View style={s.navRow}>
        <TouchableOpacity style={s.backBtn}
          onPress={step === 1 ? onBack : () => { setError(""); setStep((s) => s - 1); }}>
          <ArrowLeft size={16} color={theme.colors.sky} />
          <Text style={s.backBtnText}>{step === 1 ? "Login" : "Back"}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[s.btn, s.nextBtn, loading && { opacity: 0.6 }]}
          onPress={nextStep}
          disabled={loading}>
          {loading
            ? <ActivityIndicator color="#fff" />
            : <>
                <Text style={s.btnText}>{step === 6 ? "Submit" : "Next"}</Text>
                <ArrowRight size={16} color="#fff" />
              </>}
        </TouchableOpacity>
      </View>

      {/* Submission note */}
      {step === 6 && (
        <Text style={s.note}>
          After submission, your account will be reviewed within 24–48 hours.
          You cannot go online until an admin approves your profile.
        </Text>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container:    { flex: 1, backgroundColor: "#f8f9fa" },
  content:      { padding: 20, paddingBottom: 48 },
  progressBar:  { flexDirection: "row", justifyContent: "center", gap: 8, marginBottom: 24 },
  progressDot:  { width: 10, height: 10, borderRadius: 5, backgroundColor: "#ddd" },
  progressDotActive: { backgroundColor: theme.colors.sky },
  progressDotDone:   { backgroundColor: theme.colors.sky, opacity: 0.5 },
  stepHeader:   { alignItems: "center", marginBottom: 24 },
  stepIcon:     {
    width: 64, height: 64, borderRadius: 32,
    backgroundColor: theme.colors.sky, alignItems: "center",
    justifyContent: "center", marginBottom: 12,
  },
  stepTitle:    { fontSize: 20, fontWeight: "700", color: "#1a1a1a", marginBottom: 4 },
  stepCount:    { fontSize: 13, color: "#888" },
  card:         {
    backgroundColor: "#fff", borderRadius: 16, padding: 20,
    shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 }, elevation: 2, marginBottom: 20,
  },
  label:        { fontSize: 13, fontWeight: "600", color: "#444", marginBottom: 6, marginTop: 12 },
  input:        {
    borderWidth: 1.5, borderColor: "#e0e0e0", borderRadius: 10,
    padding: 12, fontSize: 15, color: "#1a1a1a", backgroundColor: "#fafafa",
  },
  btn:          {
    backgroundColor: theme.colors.sky, borderRadius: 10, padding: 14,
    alignItems: "center", flexDirection: "row", justifyContent: "center",
    gap: 8, marginTop: 16,
  },
  btnText:      { color: "#fff", fontWeight: "700", fontSize: 15 },
  nextBtn:      { flex: 1, marginLeft: 12 },
  backBtn:      {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingVertical: 14, paddingHorizontal: 4,
  },
  backBtnText:  { color: theme.colors.sky, fontWeight: "600", fontSize: 15 },
  navRow:       { flexDirection: "row", alignItems: "center" },
  errorBox:     {
    backgroundColor: "#fff0f0", borderRadius: 8, borderLeftWidth: 4,
    borderLeftColor: "#e53e3e", padding: 12, marginBottom: 16,
  },
  errorText:    { color: "#c53030", fontSize: 13 },
  success:      { color: "#38a169", fontWeight: "600", fontSize: 14, textAlign: "center" },
  hint:         {
    fontSize: 13, color: "#666", backgroundColor: "#f0f7ff",
    borderRadius: 8, padding: 10, marginBottom: 12, lineHeight: 18,
  },
  chipRow:      { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 12 },
  chip:         {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
    borderWidth: 1.5, borderColor: "#ddd", backgroundColor: "#fafafa",
  },
  chipActive:   { borderColor: theme.colors.sky, backgroundColor: theme.colors.sky + "15" },
  chipText:     { fontSize: 13, color: "#555" },
  chipTextActive: { color: theme.colors.sky, fontWeight: "600" },
  docSlot:      {
    flexDirection: "row", alignItems: "center", gap: 10,
    borderWidth: 1.5, borderColor: "#e0e0e0", borderStyle: "dashed",
    borderRadius: 10, padding: 14, marginBottom: 10, backgroundColor: "#fafafa",
  },
  docSlotDone:  { borderColor: theme.colors.sky, backgroundColor: theme.colors.sky + "08" },
  docLabel:     { fontSize: 14, color: "#666", flex: 1 },
  selfiePreview: { width: 200, height: 200, borderRadius: 12, marginBottom: 8 },
  note:         {
    fontSize: 12, color: "#888", textAlign: "center",
    lineHeight: 18, marginTop: 8, paddingHorizontal: 12,
  },
});
