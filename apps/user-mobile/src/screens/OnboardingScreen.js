import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Dimensions, Image } from 'react-native';
import { theme } from '../styles';

const { width } = Dimensions.get('window');

export default function OnboardingScreen({ onComplete }) {
  const [step, setStep] = useState(1); // 1-3: Illustrations, 4: Language, 5: Role
  const [lang, setLang] = useState('en');

  const handleNext = () => setStep(step + 1);
  const handleSkip = () => setStep(4);
  const handleFinish = (role) => onComplete(role);

  // --- Illustration Steps ---
  if (step <= 3) {
    const screens = [
      {
        title: "Maximize Your Agricultural Yield",
        desc: "Direct market access for farmers across Zimbabwe",
        icon: "FARM",
        btn: "Get Started",
        skip: true
      },
      {
        title: "Secure Transaction Platform",
        desc: "Protected payments with escrow verification",
        icon: "LOCK",
        btn: "Next",
        skip: true
      },
      {
        title: "Trusted Agricultural Network",
        desc: "Verified participants across the entire value chain",
        icon: "STAR",
        btn: "Start Selling",
        skip: false
      }
    ];

    const current = screens[step - 1];

    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.illustrationBox}>
           <View style={styles.illusIconContainer}>
             <Text style={styles.illusIcon}>{current.icon}</Text>
           </View>
        </View>
        <View style={styles.onboardContent}>
           <Text style={styles.onboardTitle}>{current.title}</Text>
           <Text style={styles.onboardDesc}>{current.desc}</Text>
           
           <View style={styles.dotContainer}>
              {[1, 2, 3].map(i => (
                <View key={i} style={[styles.dot, step === i && styles.dotActive]} />
              ))}
           </View>

           <TouchableOpacity style={styles.primaryBtn} onPress={handleNext}>
              <Text style={styles.primaryBtnText}>{current.btn}</Text>
           </TouchableOpacity>

           {current.skip && (
             <TouchableOpacity style={styles.skipBtn} onPress={handleSkip}>
                <Text style={styles.skipText}>Skip</Text>
             </TouchableOpacity>
           )}
        </View>
      </SafeAreaView>
    );
  }

  // --- Step 4: Language Selection ---
  if (step === 4) {
    return (
      <View style={styles.container}>
        <View style={styles.languageHeader}>
           <View style={styles.smallLogoContainer}>
             <Text style={styles.smallLogo}>AGRI</Text>
           </View>
           <Text style={styles.langTitle}>Select Your Language</Text>
           <Text style={styles.langSub}>/ Khetha Ulimi Lwakho</Text>
        </View>
        <View style={styles.content}>
           <TouchableOpacity style={[styles.langBtn, lang === 'en' && styles.langBtnActive]} onPress={() => setLang('en')}>
              <Text style={[styles.langText, lang === 'en' && styles.langTextActive]}>English</Text>
           </TouchableOpacity>
           <TouchableOpacity style={[styles.langBtn, lang === 'sn' && styles.langBtnActive]} onPress={() => setLang('sn')}>
              <Text style={[styles.langText, lang === 'sn' && styles.langTextActive]}>ChiShona</Text>
           </TouchableOpacity>
           <TouchableOpacity style={[styles.langBtn, lang === 'nd' && styles.langBtnActive]} onPress={() => setLang('nd')}>
              <Text style={[styles.langText, lang === 'nd' && styles.langTextActive]}>isiNdebele</Text>
           </TouchableOpacity>

           <TouchableOpacity style={styles.primaryBtn} onPress={() => setStep(5)}>
              <Text style={styles.primaryBtnText}>Continue</Text>
           </TouchableOpacity>
        </View>
      </View>
    );
  }

  // --- Step 5: Role Selection ---
  return (
    <View style={styles.container}>
        <View style={styles.heroSmall}>
           <Text style={styles.titleSmall}>I am a...</Text>
        </View>
        <ScrollView style={styles.roleContainer} showsVerticalScrollIndicator={false}>
            <TouchableOpacity style={styles.roleCard} onPress={() => handleFinish('farmer')}>
                <View style={[styles.roleIcon, { backgroundColor: '#E8F5E9' }]}><Text style={{ fontSize: 16, fontWeight: '700' }}>FARM</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Farmer</Text>
                    <Text style={styles.roleDesc}>Sell your produce</Text>
                </View>
                <Text style={styles.roleArrow}>→</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.roleCard} onPress={() => handleFinish('buyer')}>
                <View style={[styles.roleIcon, { backgroundColor: '#E1F5FE' }]}><Text style={{ fontSize: 16, fontWeight: '700' }}>SHOP</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Buyer</Text>
                    <Text style={styles.roleDesc}>Buy produce</Text>
                </View>
                <Text style={styles.roleArrow}>→</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.roleCard} onPress={() => handleFinish('agent')}>
                <View style={[styles.roleIcon, { backgroundColor: '#FFF3E0' }]}><Text style={{ fontSize: 16, fontWeight: '700' }}>AGNT</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Agent</Text>
                    <Text style={styles.roleDesc}>Check deals</Text>
                </View>
                <Text style={styles.roleArrow}>→</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.roleCard} onPress={() => handleFinish('driver')}>
                <View style={[styles.roleIcon, { backgroundColor: '#EDE7F6' }]}><Text style={{ fontSize: 16, fontWeight: '700' }}>TRUCK</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Driver</Text>
                    <Text style={styles.roleDesc}>Deliver goods & earn</Text>
                </View>
                <Text style={styles.roleArrow}>→</Text>
            </TouchableOpacity>
        </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.white },
  illustrationBox: { flex: 1.2, backgroundColor: '#FAFAFA', justifyContent: 'center', alignItems: 'center' },
  illusIconContainer: { width: 160, height: 160, borderRadius: 80, backgroundColor: 'rgba(46, 125, 50, 0.1)', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'rgba(46, 125, 50, 0.15)' },
  illusIcon: { fontSize: 28, fontWeight: '800', color: theme.colors.green, letterSpacing: 1 },
  onboardContent: { flex: 1, padding: 32, alignItems: 'center', justifyContent: 'center' },
  onboardTitle: { fontSize: 28, fontWeight: '800', color: theme.colors.black, textAlign: 'center', letterSpacing: 0.5 },
  onboardDesc: { fontSize: 16, color: '#666', textAlign: 'center', marginTop: 12, marginBottom: 32, lineHeight: 24, fontWeight: '500' },
  dotContainer: { flexDirection: 'row', gap: 8, marginBottom: 40 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#DDD' },
  dotActive: { backgroundColor: theme.colors.green, width: 24 },
  primaryBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 12, width: '100%', alignItems: 'center', shadowColor: theme.colors.green, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 4 },
  primaryBtnText: { color: '#FFF', fontSize: 16, fontWeight: '700', letterSpacing: 1 },
  skipBtn: { marginTop: 20 },
  skipText: { color: theme.colors.green, fontWeight: '600', fontSize: 15, letterSpacing: 0.5 },
  languageHeader: { alignItems: 'center', paddingTop: 100 },
  smallLogoContainer: { width: 90, height: 90, borderRadius: 45, backgroundColor: 'rgba(46, 125, 50, 0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24, borderWidth: 2, borderColor: 'rgba(46, 125, 50, 0.15)' },
  smallLogo: { fontSize: 18, fontWeight: '800', color: theme.colors.green, letterSpacing: 1 },
  langTitle: { fontSize: 24, fontWeight: '800', letterSpacing: 0.5 },
  langSub: { color: '#999', marginTop: 8, fontWeight: '500' },
  content: { padding: 32, flex: 1, justifyContent: 'center' },
  langBtn: { paddingVertical: 20, borderRadius: 12, borderWidth: 2, borderColor: '#F5F5F5', marginBottom: 12, alignItems: 'center', backgroundColor: '#FFF' },
  langBtnActive: { borderColor: theme.colors.green, backgroundColor: '#F1F8E9' },
  langText: { fontSize: 16, fontWeight: '600', color: '#999', letterSpacing: 0.5 },
  langTextActive: { color: theme.colors.green, fontWeight: '700' },
  heroSmall: { paddingTop: 120, paddingHorizontal: 32, paddingBottom: 32 },
  titleSmall: { fontSize: 32, fontWeight: '800', color: theme.colors.black, letterSpacing: 0.5 },
  roleContainer: { paddingHorizontal: 32 },
  roleCard: { flexDirection: 'row', alignItems: 'center', padding: 24, backgroundColor: '#FFF', borderRadius: 16, marginBottom: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 10, elevation: 2, borderWidth: 1, borderColor: '#F0F0F0' },
  roleIcon: { width: 60, height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center', marginRight: 20 },
  roleTitle: { fontSize: 18, fontWeight: '700', color: theme.colors.black, letterSpacing: 0.3 },
  roleDesc: { fontSize: 14, color: '#999', marginTop: 4, fontWeight: '500' },
  roleArrow: { fontSize: 24, color: theme.colors.green, fontWeight: '800' }
});
