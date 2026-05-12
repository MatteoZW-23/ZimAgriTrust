import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  Alert,
  ActivityIndicator,
  Switch,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  UserCheck,
} from 'lucide-react-native';
import { theme } from '../styles';
import { submitAgentApplication } from '../api';

const PROVINCES = [
  'Harare',
  'Bulawayo',
  'Manicaland',
  'Mashonaland Central',
  'Mashonaland East',
  'Mashonaland West',
  'Masvingo',
  'Matabeleland North',
  'Matabeleland South',
  'Midlands',
];

const SPECIALIZATIONS = [
  { value: 'verification', label: 'Crop & Farmer Verification' },
  { value: 'dispute_resolution', label: 'Dispute Resolution' },
  { value: 'field_support', label: 'Field Support' },
  { value: 'grain_inspector', label: 'Grain Inspector' },
  { value: 'livestock_veterinary', label: 'Livestock / Veterinary' },
  { value: 'cold_chain_logistics', label: 'Cold-Chain Logistics' },
];

function formatPhone(p) {
  const trimmed = (p || '').trim();
  if (trimmed.startsWith('+')) return trimmed.replace(/\s/g, '');
  return `+263${trimmed.replace(/^0+/, '').replace(/\s/g, '')}`;
}

export default function AgentApplicationScreen({ navigation, route }) {
  const profile = route?.params?.profile || {};
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(null);

  // Form state
  const [fullName, setFullName] = useState(profile.full_name || '');
  const [phone, setPhone] = useState(profile.phone_number || '');
  const [nationalId, setNationalId] = useState('');
  const [province, setProvince] = useState('');
  const [district, setDistrict] = useState('');
  const [showProvinces, setShowProvinces] = useState(false);
  const [experienceYears, setExperienceYears] = useState('1');
  const [hasSmartphone, setHasSmartphone] = useState(true);
  const [hasTransport, setHasTransport] = useState(false);
  const [transportType, setTransportType] = useState('');
  const [specs, setSpecs] = useState(['verification']);

  function toggleSpec(value) {
    setSpecs((cur) =>
      cur.includes(value) ? cur.filter((s) => s !== value) : [...cur, value],
    );
  }

  function validateStep1() {
    if (!fullName.trim()) return 'Full name is required';
    if (!phone.trim()) return 'Phone number is required';
    if (!nationalId.trim()) return 'National ID is required';
    return null;
  }
  function validateStep2() {
    if (!province) return 'Select your province';
    if (!district.trim()) return 'District is required';
    return null;
  }
  function validateStep3() {
    if (specs.length === 0) return 'Pick at least one specialization';
    return null;
  }

  function next() {
    const err = step === 1 ? validateStep1() : step === 2 ? validateStep2() : null;
    if (err) {
      Alert.alert('Required', err);
      return;
    }
    setStep((s) => s + 1);
  }

  async function handleSubmit() {
    const err = validateStep3();
    if (err) {
      Alert.alert('Required', err);
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitAgentApplication({
        full_name: fullName.trim(),
        phone_number: formatPhone(phone),
        national_id: nationalId.trim(),
        province,
        district: district.trim(),
        has_smartphone: hasSmartphone,
        has_transport: hasTransport,
        transport_type: hasTransport ? transportType || null : null,
        agri_experience_years: parseInt(experienceYears, 10) || 0,
        specializations: specs,
      });
      setSubmitted(res);
    } catch (e) {
      Alert.alert('Submission failed', e.message || 'Try again later.');
    } finally {
      setSubmitting(false);
    }
  }

  // ── Success screen ─────────────────────────────────────────────────────
  if (submitted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.successWrap}>
          <View style={styles.successIconCircle}>
            <CheckCircle2 size={56} color={theme.colors.green} />
          </View>
          <Text style={styles.successTitle}>Application Submitted</Text>
          <Text style={styles.successText}>
            Your application is now pending review. Agent portal login is only
            activated after approval, so keep this application ID and wait for
            SMS instructions from our recruitment team.
          </Text>

          <View style={styles.successCard}>
            <Text style={styles.successCardLabel}>APPLICATION ID</Text>
            <Text style={styles.successCardValue}>{submitted.id}</Text>
          </View>

          <Text style={styles.nextStepsTitle}>What's next?</Text>
          <View style={styles.bulletList}>
            <Bullet>Admin reviews your identity and district suitability within 24-48 hours</Bullet>
            <Bullet>If approved, you receive SMS login instructions for the Agent Portal</Bullet>
            <Bullet>Complete Academy training before practical assessment</Bullet>
            <Bullet>Pass practical assessment and supervised shadowing</Bullet>
            <Bullet>Certification unlocks live field tasks and earnings</Bullet>
          </View>

          <TouchableOpacity
            style={styles.successCta}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.successCtaText}>Back to Profile</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // ── Wizard ─────────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => (step > 1 ? setStep(step - 1) : navigation.goBack())}
            style={styles.backBtn}
          >
            <ArrowLeft size={20} color="#333" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Become an Agent</Text>
          <Text style={styles.headerStep}>Step {step}/3</Text>
        </View>

        {/* Progress bar */}
        <View style={styles.progressOuter}>
          <View style={[styles.progressInner, { width: `${(step / 3) * 100}%` }]} />
        </View>

        <ScrollView
          contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
          keyboardShouldPersistTaps="handled"
        >
          {/* ── Step 1: Personal info ────────────────────────────── */}
          {step === 1 && (
            <>
              <Text style={styles.stepTitle}>Personal Details</Text>
              <Text style={styles.stepSubtitle}>
                We'll use this to verify your identity.
              </Text>

              <Field
                label="Full Name"
                value={fullName}
                onChangeText={setFullName}
                placeholder="Tendai Ncube"
              />
              <Field
                label="Phone Number"
                value={phone}
                onChangeText={setPhone}
                placeholder="771234567"
                keyboardType="phone-pad"
                helperText="+263 prefix added automatically"
              />
              <Field
                label="National ID"
                value={nationalId}
                onChangeText={setNationalId}
                placeholder="63-1234567X12"
              />
              <Field
                label="Years of Agriculture Experience"
                value={experienceYears}
                onChangeText={setExperienceYears}
                keyboardType="numeric"
              />
            </>
          )}

          {/* ── Step 2: Location & equipment ───────────────────── */}
          {step === 2 && (
            <>
              <Text style={styles.stepTitle}>Location & Equipment</Text>
              <Text style={styles.stepSubtitle}>
                We assign agents to their home district.
              </Text>

              {/* Province picker */}
              <Text style={styles.label}>Province</Text>
              <TouchableOpacity
                style={styles.dropdown}
                onPress={() => setShowProvinces((s) => !s)}
              >
                <Text style={[styles.dropdownText, !province && { color: '#999' }]}>
                  {province || 'Select Province'}
                </Text>
                <ChevronDown size={18} color="#666" />
              </TouchableOpacity>
              {showProvinces && (
                <View style={styles.dropdownList}>
                  {PROVINCES.map((p) => (
                    <TouchableOpacity
                      key={p}
                      style={styles.dropdownItem}
                      onPress={() => {
                        setProvince(p);
                        setShowProvinces(false);
                      }}
                    >
                      <Text style={{ fontSize: 14 }}>{p}</Text>
                      {province === p && <Check size={16} color={theme.colors.green} />}
                    </TouchableOpacity>
                  ))}
                </View>
              )}

              <Field
                label="District"
                value={district}
                onChangeText={setDistrict}
                placeholder="e.g. Harare East"
              />

              <View style={styles.toggleRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.toggleLabel}>I have a smartphone</Text>
                  <Text style={styles.toggleHelper}>
                    Required for the agent app
                  </Text>
                </View>
                <Switch
                  value={hasSmartphone}
                  onValueChange={setHasSmartphone}
                  trackColor={{ true: theme.colors.green }}
                />
              </View>

              <View style={styles.toggleRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.toggleLabel}>I have own transport</Text>
                  <Text style={styles.toggleHelper}>
                    Optional but improves task throughput
                  </Text>
                </View>
                <Switch
                  value={hasTransport}
                  onValueChange={setHasTransport}
                  trackColor={{ true: theme.colors.green }}
                />
              </View>

              {hasTransport && (
                <Field
                  label="Transport Type"
                  value={transportType}
                  onChangeText={setTransportType}
                  placeholder="Motorbike, car, bicycle..."
                />
              )}
            </>
          )}

          {/* ── Step 3: Specializations ────────────────────────── */}
          {step === 3 && (
            <>
              <Text style={styles.stepTitle}>Specializations</Text>
              <Text style={styles.stepSubtitle}>
                Pick the areas you want to work in. You can refine later.
              </Text>

              {SPECIALIZATIONS.map((s) => {
                const selected = specs.includes(s.value);
                return (
                  <TouchableOpacity
                    key={s.value}
                    style={[styles.specRow, selected && styles.specRowSelected]}
                    onPress={() => toggleSpec(s.value)}
                  >
                    <View style={[styles.specCheck, selected && styles.specCheckActive]}>
                      {selected && <Check size={14} color="#fff" />}
                    </View>
                    <Text style={styles.specLabel}>{s.label}</Text>
                  </TouchableOpacity>
                );
              })}

              <View style={styles.summaryCard}>
                <Text style={styles.summaryTitle}>Application Summary</Text>
                <SummaryRow label="Name" value={fullName} />
                <SummaryRow label="Phone" value={formatPhone(phone)} />
                <SummaryRow label="National ID" value={nationalId} />
                <SummaryRow label="Location" value={`${district}, ${province}`} />
                <SummaryRow label="Experience" value={`${experienceYears} years`} />
                <SummaryRow label="Smartphone" value={hasSmartphone ? 'Yes' : 'No'} />
                <SummaryRow
                  label="Transport"
                  value={hasTransport ? transportType || 'Yes' : 'No'}
                />
              </View>
            </>
          )}
        </ScrollView>

        {/* Footer CTA */}
        <View style={styles.footer}>
          {step < 3 ? (
            <TouchableOpacity style={styles.cta} onPress={next}>
              <Text style={styles.ctaText}>Continue</Text>
              <ArrowRight size={18} color="#fff" />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.cta, submitting && { opacity: 0.6 }]}
              onPress={handleSubmit}
              disabled={submitting}
            >
              {submitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <UserCheck size={18} color="#fff" />
                  <Text style={styles.ctaText}>Submit Application</Text>
                </>
              )}
            </TouchableOpacity>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────
function Field({ label, value, onChangeText, placeholder, keyboardType, helperText }) {
  return (
    <View style={{ marginBottom: 16 }}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="#bbb"
        keyboardType={keyboardType || 'default'}
      />
      {helperText && <Text style={styles.helper}>{helperText}</Text>}
    </View>
  );
}

function Bullet({ children }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 }}>
      <Text style={{ color: theme.colors.green, fontSize: 16, marginRight: 8 }}>•</Text>
      <Text style={{ flex: 1, color: '#555', fontSize: 14 }}>{children}</Text>
    </View>
  );
}

function SummaryRow({ label, value }) {
  return (
    <View style={styles.summaryRow}>
      <Text style={styles.summaryLabel}>{label}</Text>
      <Text style={styles.summaryValue}>{value || '—'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  backBtn: { padding: 6, marginRight: 8 },
  headerTitle: { flex: 1, fontSize: 18, fontWeight: '700', color: '#222' },
  headerStep: { color: '#888', fontSize: 12, fontWeight: '600' },
  progressOuter: { height: 4, backgroundColor: '#eee' },
  progressInner: {
    height: '100%',
    backgroundColor: theme.colors.green,
  },
  stepTitle: { fontSize: 22, fontWeight: '800', color: '#222', marginBottom: 6 },
  stepSubtitle: { color: '#666', fontSize: 14, marginBottom: 24 },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#444',
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: '#222',
    backgroundColor: '#fafafa',
  },
  helper: { fontSize: 11, color: '#888', marginTop: 4 },
  dropdown: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: '#fafafa',
    marginBottom: 8,
  },
  dropdownText: { fontSize: 15, color: '#222' },
  dropdownList: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    backgroundColor: '#fff',
    marginBottom: 16,
  },
  dropdownItem: {
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  toggleLabel: { fontSize: 15, fontWeight: '600', color: '#222' },
  toggleHelper: { fontSize: 12, color: '#888', marginTop: 2 },
  specRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginBottom: 8,
    backgroundColor: '#fafafa',
  },
  specRowSelected: {
    borderColor: theme.colors.green,
    backgroundColor: '#f0fdf4',
  },
  specCheck: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: '#ccc',
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  specCheckActive: {
    backgroundColor: theme.colors.green,
    borderColor: theme.colors.green,
  },
  specLabel: { fontSize: 14, color: '#222', fontWeight: '500' },
  summaryCard: {
    backgroundColor: '#f7f7f7',
    borderRadius: 12,
    padding: 16,
    marginTop: 20,
  },
  summaryTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  summaryLabel: { color: '#888', fontSize: 13 },
  summaryValue: { color: '#222', fontSize: 13, fontWeight: '600', flex: 1, textAlign: 'right' },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    backgroundColor: '#fff',
  },
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.green,
    paddingVertical: 16,
    borderRadius: 14,
    gap: 8,
  },
  ctaText: { color: '#fff', fontSize: 16, fontWeight: '700' },

  // Success screen
  successWrap: { flex: 1, padding: 24, alignItems: 'center', justifyContent: 'center' },
  successIconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#f0fdf4',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  successTitle: { fontSize: 24, fontWeight: '800', color: '#222', marginBottom: 12 },
  successText: { color: '#555', fontSize: 15, textAlign: 'center', marginBottom: 24, lineHeight: 22 },
  successCard: {
    backgroundColor: '#f7f7f7',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 28,
  },
  successCardLabel: { fontSize: 11, color: '#888', letterSpacing: 1, marginBottom: 4 },
  successCardValue: { fontSize: 12, fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace' }), color: '#222' },
  nextStepsTitle: { alignSelf: 'flex-start', fontSize: 14, fontWeight: '700', color: '#444', marginBottom: 10 },
  bulletList: { alignSelf: 'stretch', marginBottom: 28 },
  successCta: {
    backgroundColor: theme.colors.green,
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 14,
  },
  successCtaText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
