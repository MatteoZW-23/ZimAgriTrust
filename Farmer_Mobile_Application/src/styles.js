export const theme = {
  colors: {
    green: '#2E7D32',      // Harvest Green
    gold: '#F9A825',       // Tobacco Gold
    brown: '#5D4037',      // Earth Brown
    sky: '#29B6F6',        // Zimbabwe Sky
    orange: '#FF7043',     // Sunset Orange
    red: '#D32F2F',        // Harvest Red
    white: '#FFFFFF',      // Cloud White
    gray: '#F5F5F5',       // Field Gray
    black: '#212121',      // Rich Black
    shadow: 'rgba(0, 0, 0, 0.12)',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 20,
    pill: 40,
  },
  elevation: {
      s1: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.12,
        shadowRadius: 3,
        elevation: 2,
      },
      s2: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 0.16,
        shadowRadius: 6,
        elevation: 4,
      },
      s3: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.19,
        shadowRadius: 20,
        elevation: 8,
      }
  }
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
    fontSize: 28,
    fontWeight: '900',
    color: theme.colors.black,
    fontFamily: 'Poppins-Bold',
  },
  card: {
    backgroundColor: theme.colors.white,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.md,
    ...theme.elevation.s1,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  primaryBtn: {
    backgroundColor: theme.colors.green,
    borderRadius: theme.radius.xl,
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
     borderRadius: theme.radius.pill,
     fontSize: 12,
     fontWeight: '700',
  }
};
