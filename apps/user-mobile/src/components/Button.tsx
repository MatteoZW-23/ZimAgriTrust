import React, {
  forwardRef,
  memo,
  useCallback,
  useMemo,
} from 'react';
import {
  Pressable,
  Text,
  StyleSheet,
  ActivityIndicator,
  View,
  ViewStyle,
  TextStyle,
  StyleProp,
} from 'react-native';
import { theme } from '../styles';

type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'danger'
  | 'success'
  | 'warning'
  | 'ghost';

type ButtonSize = 'small' | 'medium' | 'large';

interface ButtonProps {
  title: string;
  onPress: () => void;

  variant?: ButtonVariant;
  size?: ButtonSize;

  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;

  disabled?: boolean;
  loading?: boolean;

  loadingTitle?: string;

  fullWidth?: boolean;

  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;

  testID?: string;
}

const VARIANTS = {
  primary: {
    backgroundColor: theme.colors.green,
    textColor: theme.colors.white,
    borderColor: 'transparent',
  },

  secondary: {
    backgroundColor: theme.colors.sky,
    textColor: theme.colors.white,
    borderColor: 'transparent',
  },

  outline: {
    backgroundColor: 'transparent',
    textColor: theme.colors.green,
    borderColor: theme.colors.green,
  },

  danger: {
    backgroundColor: theme.colors.red,
    textColor: theme.colors.white,
    borderColor: 'transparent',
  },

  success: {
    backgroundColor: theme.colors.green,
    textColor: theme.colors.white,
    borderColor: 'transparent',
  },

  warning: {
    backgroundColor: theme.colors.orange,
    textColor: theme.colors.white,
    borderColor: 'transparent',
  },

  ghost: {
    backgroundColor: 'transparent',
    textColor: theme.colors.green,
    borderColor: 'transparent',
  },
} as const;

const SIZE_CONFIG = {
  small: {
    height: 40,
    paddingHorizontal: 16,
    fontSize: 14,
  },

  medium: {
    height: 48,
    paddingHorizontal: 24,
    fontSize: 16,
  },

  large: {
    height: 56,
    paddingHorizontal: 32,
    fontSize: 18,
  },
} as const;

export const Button = memo(
  forwardRef<View, ButtonProps>(
    (
      {
        title,
        onPress,

        variant = 'primary',
        size = 'medium',

        leftIcon,
        rightIcon,

        disabled = false,
        loading = false,

        loadingTitle,

        fullWidth = false,

        style,
        textStyle,

        testID,
      },
      ref
    ) => {
      const variantConfig = useMemo(() => {
        if (disabled) {
          return {
            backgroundColor: theme.colors.gray[300],
            textColor: theme.colors.gray[500],
            borderColor: theme.colors.gray[300],
          };
        }

        return VARIANTS[variant];
      }, [variant, disabled]);

      const sizeConfig = SIZE_CONFIG[size];

      const handlePress = useCallback(() => {
        if (disabled || loading) return;

        onPress();
      }, [disabled, loading, onPress]);

      const buttonStyle = useMemo(
        () => [
          styles.button,
          {
            backgroundColor: variantConfig.backgroundColor,
            borderColor: variantConfig.borderColor,
            height: sizeConfig.height,
            paddingHorizontal: sizeConfig.paddingHorizontal,
            width: fullWidth ? '100%' : undefined,
          },
          style,
        ],
        [
          variantConfig,
          sizeConfig,
          fullWidth,
          style,
        ]
      );

      return (
        <Pressable
          ref={ref}
          testID={testID}
          accessibilityRole="button"
          accessibilityLabel={title}
          accessibilityHint="Tap to perform action"
          accessibilityState={{
            disabled,
            busy: loading,
          }}
          disabled={disabled || loading}
          onPress={handlePress}
          style={({ pressed }) => [
            buttonStyle,
            pressed &&
              !disabled &&
              !loading &&
              styles.pressed,
          ]}
        >
          {loading ? (
            <View style={styles.content}>
              <ActivityIndicator
                size="small"
                color={variantConfig.textColor}
              />

              {loadingTitle && (
                <Text
                  style={[
                    styles.text,
                    {
                      color: variantConfig.textColor,
                      fontSize: sizeConfig.fontSize,
                    },
                    styles.loadingText,
                    textStyle,
                  ]}
                >
                  {loadingTitle}
                </Text>
              )}
            </View>
          ) : (
            <View style={styles.content}>
              {leftIcon && (
                <View style={styles.leftIcon}>
                  {leftIcon}
                </View>
              )}

              <Text
                style={[
                  styles.text,
                  {
                    color: variantConfig.textColor,
                    fontSize: sizeConfig.fontSize,
                  },
                  textStyle,
                ]}
                numberOfLines={1}
              >
                {title}
              </Text>

              {rightIcon && (
                <View style={styles.rightIcon}>
                  {rightIcon}
                </View>
              )}
            </View>
          )}
        </Pressable>
      );
    }
  )
);

Button.displayName = 'Button';

const styles = StyleSheet.create({
  button: {
    borderRadius: theme.borderRadius.xl,
    borderWidth: 2,

    alignItems: 'center',
    justifyContent: 'center',

    flexDirection: 'row',

    shadowColor: theme.shadows.sm.shadowColor,
    shadowOffset: theme.shadows.sm.shadowOffset,
    shadowOpacity: theme.shadows.sm.shadowOpacity,
    shadowRadius: theme.shadows.sm.shadowRadius,

    elevation: theme.shadows.sm.elevation,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.9,
  },

  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },

  leftIcon: {
    marginRight: 8,
  },

  rightIcon: {
    marginLeft: 8,
  },

  loadingText: {
    marginLeft: 10,
  },

  text: {
    fontWeight: '700',
    letterSpacing: 0.5,
    textAlign: 'center',
  },
});
