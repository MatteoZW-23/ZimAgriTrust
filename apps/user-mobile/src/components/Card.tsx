import React, {
  forwardRef,
  memo,
  useCallback,
  useMemo,
} from 'react';
import {
  View,
  StyleSheet,
  Pressable,
  ViewStyle,
  StyleProp,
} from 'react-native';
import { theme } from '../styles';

type CardPadding = 'none' | 'small' | 'medium' | 'large';
type CardVariant = 'default' | 'outlined' | 'elevated';

interface CardProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
  padding?: CardPadding;
  variant?: CardVariant;
  disabled?: boolean;
  testID?: string;
}

const PADDING_CONFIG = {
  none: 0,
  small: theme.spacing.sm,
  medium: theme.spacing.md,
  large: theme.spacing.lg,
} as const;

const VARIANT_CONFIG = {
  outlined: {
    borderWidth: 1,
    borderColor: theme.colors.gray[300],
    backgroundColor: theme.colors.white,
  },
  elevated: {
    backgroundColor: theme.colors.white,
    shadowColor: theme.shadows.md.shadowColor,
    shadowOffset: theme.shadows.md.shadowOffset,
    shadowOpacity: theme.shadows.md.shadowOpacity,
    shadowRadius: theme.shadows.md.shadowRadius,
    elevation: theme.shadows.md.elevation,
  },
  default: {
    backgroundColor: theme.colors.white,
    shadowColor: theme.shadows.sm.shadowColor,
    shadowOffset: theme.shadows.sm.shadowOffset,
    shadowOpacity: theme.shadows.sm.shadowOpacity,
    shadowRadius: theme.shadows.sm.shadowRadius,
    elevation: theme.shadows.sm.elevation,
  },
} as const;

export const Card = memo(
  forwardRef<View, CardProps>(
    (
      {
        children,
        style,
        onPress,
        padding = 'medium',
        variant = 'default',
        disabled = false,
        testID,
      },
      ref
    ) => {
      const handlePress = useCallback(() => {
        if (disabled || !onPress) return;
        onPress();
      }, [disabled, onPress]);

      const cardStyle = useMemo(
        () => [
          styles.card,
          { padding: PADDING_CONFIG[padding] },
          VARIANT_CONFIG[variant],
          disabled && styles.disabled,
          style,
        ],
        [padding, variant, disabled, style]
      );

      if (onPress) {
        return (
          <Pressable
            ref={ref}
            testID={testID}
            accessibilityRole="button"
            accessibilityLabel="Card"
            accessibilityHint={disabled ? 'Disabled' : 'Tap to interact'}
            accessibilityState={{ disabled }}
            disabled={disabled}
            onPress={handlePress}
            style={({ pressed }) => [
              cardStyle,
              pressed && !disabled && styles.pressed,
            ]}
          >
            {children}
          </Pressable>
        );
      }

      return <View ref={ref} style={cardStyle}>{children}</View>;
    }
  )
);

Card.displayName = 'Card';

const styles = StyleSheet.create({
  card: {
    borderRadius: theme.borderRadius.lg,
    backgroundColor: theme.colors.white,
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.9,
  },
});
