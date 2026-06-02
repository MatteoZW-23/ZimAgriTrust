import React, { memo } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, Modal } from 'react-native';
import { theme } from '../styles';

interface LoadingOverlayProps {
  visible: boolean;
  message?: string;
  testID?: string;
}

export const LoadingOverlay = memo<LoadingOverlayProps>(({
  visible,
  message = 'Loading...',
  testID,
}) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      testID={testID}
    >
      <View style={styles.container}>
        <View style={styles.content}>
          <ActivityIndicator
            size="large"
            color={theme.colors.green}
            style={styles.spinner}
            accessibilityLabel="Loading"
          />
          {message && (
            <Text
              style={styles.message}
              numberOfLines={2}
            >
              {message}
            </Text>
          )}
        </View>
      </View>
    </Modal>
  );
});

LoadingOverlay.displayName = 'LoadingOverlay';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    backgroundColor: theme.colors.white,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.xl,
    alignItems: 'center',
    minWidth: 200,
    ...theme.shadows.lg,
  },
  spinner: {
    marginBottom: theme.spacing.md,
  },
  message: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.black,
    textAlign: 'center',
  },
});
