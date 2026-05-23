import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  SafeAreaView, TextInput, Alert, ActivityIndicator
} from 'react-native';
import { 
  ArrowLeft as IconArrowLeft, 
  Star as IconStar, 
  Check as IconCheck 
} from 'lucide-react-native';
import { submitReview } from '../api';
import { theme } from '../styles';

const TAGS = [];

export default function RateUserScreen({ navigation, route }) {
  const { orderId, token, role = 'farmer' } = route.params || {};
  const targetLabel = role === 'farmer' ? 'Buyer' : 'Farmer';

  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [comment, setComment] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const toggleTag = (tag) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = async () => {
    if (rating === 0) {
      Alert.alert('Rating required', 'Please select a star rating before submitting.');
      return;
    }
    setSubmitting(true);
    try {
      await submitReview(token, orderId, {
        rating,
        comment: comment.trim() || undefined,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
      });
      Alert.alert('Review submitted!', 'Thank you for your feedback.', [
        { text: 'OK', onPress: () => navigation.navigate('MyOrders', { token, role }) }
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to submit review. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const displayRating = hovered || rating;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtnBox}>
            <IconArrowLeft size={22} color={theme.colors.black} />
          </TouchableOpacity>
          <Text style={styles.title}>Rate {targetLabel}</Text>
          <View style={{ width: 44 }} />
        </View>

        <View style={styles.heroCard}>
          <View style={styles.heroIconBox}>
            <IconStar size={40} color="#f59e0b" fill="#f59e0b" />
          </View>
          <Text style={styles.heroTitle}>How was your experience?</Text>
          <Text style={styles.heroSub}>Your honest feedback helps build trust in the ZimAgritrust community.</Text>
        </View>

        {/* Star Rating */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>YOUR RATING</Text>
          <View style={styles.starsRow}>
            {[1, 2, 3, 4, 5].map(star => (
              <TouchableOpacity
                key={star}
                onPress={() => setRating(star)}
                onPressIn={() => setHovered(star)}
                onPressOut={() => setHovered(0)}
                activeOpacity={0.8}
              >
                <IconStar 
                  size={48} 
                  color={star <= displayRating ? '#f59e0b' : '#e2e8f0'} 
                  fill={star <= displayRating ? '#f59e0b' : 'transparent'} 
                />
              </TouchableOpacity>
            ))}
          </View>
          {rating > 0 && (
            <Text style={styles.ratingLabel}>
              {['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][rating]}
            </Text>
          )}
        </View>

        {/* Quick Tags */}
        {TAGS.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>QUICK TAGS (OPTIONAL)</Text>
            <View style={styles.tagsWrap}>
              {TAGS.map(tag => (
                <TouchableOpacity
                  key={tag}
                  style={[styles.tag, selectedTags.includes(tag) && styles.tagActive]}
                  onPress={() => toggleTag(tag)}
                >
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    {selectedTags.includes(tag) && <IconCheck size={14} color="#FFF" />}
                    <Text style={[styles.tagText, selectedTags.includes(tag) && styles.tagTextActive]}>
                      {tag}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Written Review */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>WRITTEN REVIEW (OPTIONAL)</Text>
          <TextInput
            style={styles.textArea}
            placeholder={`Share your experience with this ${targetLabel.toLowerCase()}...`}
            placeholderTextColor="#94a3b8"
            multiline
            numberOfLines={4}
            value={comment}
            onChangeText={setComment}
            maxLength={500}
          />
          <Text style={styles.charCount}>{comment.length}/500</Text>
        </View>

        {/* Submit */}
        <View style={styles.submitSection}>
          <TouchableOpacity
            style={[styles.submitBtn, (rating === 0 || submitting) && styles.submitBtnDisabled]}
            onPress={handleSubmit}
            disabled={rating === 0 || submitting}
          >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitBtnText}>Submit Review</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity style={styles.skipBtn} onPress={() => navigation.navigate('MyOrders', { token, role })}>
            <Text style={styles.skipText}>Skip for now</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 24, paddingTop: 60 },
  backBtnBox: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#F9FAFB', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#EEE' },
  title: { fontSize: 18, fontWeight: '900', color: theme.colors.black },
  heroCard: { marginHorizontal: 20, marginBottom: 8, backgroundColor: '#f0fdf4', borderRadius: 24, padding: 28, alignItems: 'center', borderWidth: 1, borderColor: '#bbf7d0' },
  heroIconBox: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center', marginBottom: 12, elevation: 2, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
  heroTitle: { fontSize: 22, fontWeight: '900', color: theme.colors.black, textAlign: 'center', marginBottom: 8 },
  heroSub: { fontSize: 14, color: '#475569', textAlign: 'center', lineHeight: 22 },
  section: { marginHorizontal: 20, marginTop: 24 },
  sectionLabel: { fontSize: 11, fontWeight: '900', color: '#94a3b8', letterSpacing: 1.2, marginBottom: 14, textTransform: 'uppercase' },
  starsRow: { flexDirection: 'row', gap: 8, justifyContent: 'center', marginBottom: 8 },
  ratingLabel: { textAlign: 'center', fontSize: 16, fontWeight: '800', color: '#f59e0b', marginTop: 4 },
  tagsWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  tag: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 20, backgroundColor: '#f1f5f9', borderWidth: 1, borderColor: '#e2e8f0' },
  tagActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  tagText: { fontSize: 13, fontWeight: '700', color: '#475569' },
  tagTextActive: { color: '#fff' },
  textArea: { backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 16, padding: 16, fontSize: 15, color: theme.colors.black, minHeight: 120, textAlignVertical: 'top', fontWeight: '500' },
  charCount: { textAlign: 'right', fontSize: 11, color: '#94a3b8', marginTop: 6, fontWeight: '600' },
  submitSection: { marginHorizontal: 20, marginTop: 32 },
  submitBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 20, alignItems: 'center' },
  submitBtnDisabled: { opacity: 0.5 },
  submitBtnText: { color: '#fff', fontSize: 17, fontWeight: '900' },
  skipBtn: { marginTop: 16, alignItems: 'center', paddingVertical: 12 },
  skipText: { color: '#94a3b8', fontWeight: '700', fontSize: 14 },
});
