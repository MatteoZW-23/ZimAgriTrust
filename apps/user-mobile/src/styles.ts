export const theme = {
  colors: {
    green: '#2E7D32',      // Harvest Green
    gold: '#FFC107',       // Tobacco Gold
    brown: '#5D4037',      // Earth Brown
    sky: '#29B6F6',        // Zimbabwe Sky
    orange: '#FF7043',     // Sunset Orange
    red: '#D32F2F',        // Harvest Red
    white: '#FFFFFF',      // Cloud White
    gray: {
      100: '#F5F5F5',
      200: '#EEEEEE',
      300: '#E0E0E0',
      400: '#BDBDBD',
      500: '#9E9E9E',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
    black: '#212121',      // Rich Black
    light: '#F6F0DE',
  },
  typography: {
    h1: { fontSize: 32, fontWeight: '800', letterSpacing: 0.5, lineHeight: 40 },
    h2: { fontSize: 28, fontWeight: '800', letterSpacing: 0.5, lineHeight: 36 },
    h3: { fontSize: 24, fontWeight: '700', letterSpacing: 0.3, lineHeight: 32 },
    h4: { fontSize: 20, fontWeight: '700', letterSpacing: 0.2, lineHeight: 28 },
    body: { fontSize: 16, fontWeight: '500', lineHeight: 24 },
    bodyLarge: { fontSize: 18, fontWeight: '500', lineHeight: 28 },
    caption: { fontSize: 14, fontWeight: '500', lineHeight: 20 },
    small: { fontSize: 12, fontWeight: '500', lineHeight: 16 },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 24,
    round: 9999,
  },
  shadows: {
    xs: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1,
    },
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.08,
      shadowRadius: 4,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.12,
      shadowRadius: 8,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.16,
      shadowRadius: 12,
      elevation: 8,
    },
    xl: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 10 },
      shadowOpacity: 0.2,
      shadowRadius: 20,
      elevation: 12,
    },
  },
};

export const globalStyles = {
  container: {
    flex: 1,
    backgroundColor: theme.colors.white,
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
  },
  title: {
    fontSize: theme.typography.h1.fontSize,
    fontWeight: theme.typography.h1.fontWeight,
    color: theme.colors.black,
    fontFamily: 'Poppins-Bold',
  },
  card: {
    backgroundColor: theme.colors.white,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.md,
    ...theme.shadows.sm,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  primaryBtn: {
    backgroundColor: theme.colors.green,
    borderRadius: theme.borderRadius.xl,
    paddingVertical: theme.spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryBtnText: {
    color: theme.colors.white,
    fontSize: 16,
    fontWeight: '800',
  },
  badge: {
     paddingHorizontal: 12,
     paddingVertical: 4,
     borderRadius: theme.borderRadius.round,
     fontSize: 12,
     fontWeight: '700',
  }
};
