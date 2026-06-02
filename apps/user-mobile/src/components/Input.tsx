import React, {
  forwardRef,
  memo,
  useCallback,
  useMemo,
} from 'react';
import {
  TextInput,
  View,
  Text,
  StyleSheet,
  Pressable,
  ViewStyle,
  TextInputProps,
  StyleProp,
  TextStyle,
} from 'react-native';
import { Eye, EyeOff, AlertCircle } from 'lucide-react-native';
import { theme } from '../styles';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onRightIconPress?: () => void;
  containerStyle?: StyleProp<ViewStyle>;
  showPasswordToggle?: boolean;
  isPasswordVisible?: boolean;
  onPasswordVisibilityToggle?: () => void;
  testID?: string;
}

export const Input = memo(
  forwardRef<TextInput, InputProps>(
    (
      {
        label,
        error,
        icon,
        rightIcon,
        onRightIconPress,
        containerStyle,
        showPasswordToggle = false,
        isPasswordVisible = false,
        onPasswordVisibilityToggle,
        style,
        secureTextEntry,
        testID,
        ...props
      },
      ref
    ) => {
      const isSecure = useMemo(
        () => showPasswordToggle && secureTextEntry && !isPasswordVisible,
        [showPasswordToggle, secureTextEntry, isPasswordVisible]
      );

      const handleRightIconPress = useCallback(() => {
        if (showPasswordToggle && onPasswordVisibilityToggle) {
          onPasswordVisibilityToggle();
        } else if (onRightIconPress) {
          onRightIconPress();
        }
      }, [showPasswordToggle, onPasswordVisibilityToggle, onRightIconPress]);

      const inputContainerStyle = useMemo(
        () => [
          styles.inputContainer,
          error && styles.inputError,
        ],
        [error]
      );

      const inputStyle = useMemo(
        () => [
          styles.input,
          icon && styles.inputWithIcon,
          style,
        ],
        [icon, style]
      );

      const hasRightAction = showPasswordToggle || rightIcon;

      return (
        <View style={[styles.container, containerStyle]}>
          {label && (
            <Text
              style={styles.label}
              numberOfLines={1}
            >
              {label}
            </Text>
          )}
          <View style={inputContainerStyle}>
            {icon && <View style={styles.leftIcon}>{icon}</View>}
            <TextInput
              ref={ref}
              testID={testID}
              style={inputStyle}
              placeholderTextColor={theme.colors.gray[400]}
              secureTextEntry={isSecure}
              accessibilityLabel={label || 'Text input'}
              accessibilityState={{ error: !!error }}
              {...props}
            />
            {hasRightAction && (
              <Pressable
                style={styles.rightIcon}
                onPress={handleRightIconPress}
                disabled={!onPasswordVisibilityToggle && !onRightIconPress}
                accessibilityRole="button"
                accessibilityLabel={
                  showPasswordToggle
                    ? isPasswordVisible
                      ? 'Hide password'
                      : 'Show password'
                    : 'Action'
                }
              >
                {showPasswordToggle ? (
                  isPasswordVisible ? (
                    <EyeOff size={20} color={theme.colors.gray[500]} />
                  ) : (
                    <Eye size={20} color={theme.colors.gray[500]} />
                  )
                ) : (
                  rightIcon
                )}
              </Pressable>
            )}
          </View>
          {error && (
            <View style={styles.errorContainer}>
              <AlertCircle size={14} color={theme.colors.red} />
              <Text
                style={styles.errorText}
                numberOfLines={2}
              >
                {error}
              </Text>
            </View>
          )}
        </View>
      );
    }
  )
);

Input.displayName = 'Input';

const styles = StyleSheet.create({
  container: {
    marginBottom: theme.spacing.md,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.black,
    marginBottom: theme.spacing.sm,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.white,
    borderWidth: 1,
    borderColor: theme.colors.gray[300],
    borderRadius: theme.borderRadius.md,
    paddingHorizontal: theme.spacing.md,
    height: 52,
    ...theme.shadows.xs,
  },
  inputError: {
    borderColor: theme.colors.red,
  },
  input: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: theme.colors.black,
    paddingVertical: 0,
  },
  inputWithIcon: {
    marginLeft: theme.spacing.sm,
  },
  leftIcon: {
    marginRight: theme.spacing.sm,
  },
  rightIcon: {
    marginLeft: theme.spacing.sm,
    padding: theme.spacing.xs,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.xs,
  },
  errorText: {
    fontSize: 12,
    color: theme.colors.red,
    marginLeft: theme.spacing.xs,
  },
});
