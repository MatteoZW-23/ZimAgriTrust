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
        title: "Sell Everything You Grow",
        desc: "Connect directly with buyers across Zimbabwe",
        icon: "🌾",
        btn: "Get Started",
        skip: true
      },
      {
        title: "Safe & Secure Payments",
        desc: "Escrow protection for every transaction",
        icon: "🛡️",
        btn: "Next",
        skip: true
      },
      {
        title: "Trusted by Thousands",
        desc: "Verified farmers and buyers across all sectors",
        icon: "⭐",
        btn: "Start Selling",
        skip: false
      }
    ];

    const current = screens[step - 1];

    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.illustrationBox}>
           <Text style={styles.illusIcon}>{current.icon}</Text>
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
           <Text style={styles.smallLogo}>🚜</Text>
           <Text style={styles.langTitle}>Select Your Language</Text>
           <Text style={styles.langSub}>/ Khetha Ulimi Lwakho</Text>
        </View>
        <View style={styles.content}>
           <TouchableOpacity style={[styles.langBtn, lang === 'en' && styles.langBtnActive]} onPress={() => setLang('en')}>
              <Text style={[styles.langText, lang === 'en' && styles.langTextActive]}>🇬🇧 English</Text>
           </TouchableOpacity>
           <TouchableOpacity style={[styles.langBtn, lang === 'sn' && styles.langBtnActive]} onPress={() => setLang('sn')}>
              <Text style={[styles.langText, lang === 'sn' && styles.langTextActive]}>🇿🇼 ChiShona</Text>
           </TouchableOpacity>
           <TouchableOpacity style={[styles.langBtn, lang === 'nd' && styles.langBtnActive]} onPress={() => setLang('nd')}>
              <Text style={[styles.langText, lang === 'nd' && styles.langTextActive]}>🇿🇼 isiNdebele</Text>
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
                <View style={[styles.roleIcon, { backgroundColor: '#E8F5E9' }]}><Text style={{ fontSize: 32 }}>🌾</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Farmer</Text>
                    <Text style={styles.roleDesc}>Sell your produce</Text>
                </View>
                <Text style={styles.roleArrow}>→</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.roleCard} onPress={() => handleFinish('buyer')}>
                <View style={[styles.roleIcon, { backgroundColor: '#E1F5FE' }]}><Text style={{ fontSize: 32 }}>🛒</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Buyer</Text>
                    <Text style={styles.roleDesc}>Buy produce</Text>
                </View>
                <Text style={styles.roleArrow}>→</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.roleCard} onPress={() => handleFinish('agent')}>
                <View style={[styles.roleIcon, { backgroundColor: '#FFF3E0' }]}><Text style={{ fontSize: 32 }}>⚖️</Text></View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.roleTitle}>Agent</Text>
                    <Text style={styles.roleDesc}>Check deals</Text>
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
  illusIcon: { fontSize: 120 },
  onboardContent: { flex: 1, padding: 32, alignItems: 'center', justifyContent: 'center' },
  onboardTitle: { fontSize: 26, fontWeight: '900', color: theme.colors.black, textAlign: 'center' },
  onboardDesc: { fontSize: 16, color: '#666', textAlign: 'center', marginTop: 12, marginBottom: 32, lineHeight: 24 },
  dotContainer: { flexDirection: 'row', gap: 8, marginBottom: 40 },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#DDD' },
  dotActive: { backgroundColor: theme.colors.green, width: 20 },
  primaryBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 20, width: '100%', alignItems: 'center' },
  primaryBtnText: { color: '#FFF', fontSize: 18, fontWeight: '800' },
  skipBtn: { marginTop: 20 },
  skipText: { color: theme.colors.green, fontWeight: '700', fontSize: 15 },
  languageHeader: { alignItems: 'center', paddingTop: 80 },
  smallLogo: { fontSize: 60, marginBottom: 20 },
  langTitle: { fontSize: 22, fontWeight: '800' },
  langSub: { color: '#999', marginTop: 4 },
  content: { padding: 32, flex: 1, justifyContent: 'center' },
  langBtn: { paddingVertical: 18, borderRadius: 16, borderWidth: 2, borderColor: '#F5F5F5', marginBottom: 12, alignItems: 'center' },
  langBtnActive: { borderColor: theme.colors.green, backgroundColor: '#F1F8E9' },
  langText: { fontSize: 16, fontWeight: '700', color: '#999' },
  langTextActive: { color: theme.colors.green },
  heroSmall: { paddingTop: 100, paddingHorizontal: 32, paddingBottom: 32 },
  titleSmall: { fontSize: 32, fontWeight: '900', color: theme.colors.black },
  roleContainer: { paddingHorizontal: 32 },
  roleCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', borderRadius: 24, padding: 24, marginBottom: 20, borderWidth: 1, borderColor: '#F0F0F0' },
  roleIcon: { width: 64, height: 64, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginRight: 20 },
  roleTitle: { fontSize: 20, fontWeight: '800', color: theme.colors.black },
  roleDesc: { fontSize: 13, color: '#666', marginTop: 4 },
  roleArrow: { fontSize: 24, fontWeight: '700', color: '#DDD', marginLeft: 10 }
});

