const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Force Metro to resolve ESM files and handle extensions correctly
config.resolver.sourceExts.push('mjs');

// Fix for 'Unable to resolve "../Utilities/Platform"' error on Web
const originalResolveRequest = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web' && (moduleName.endsWith('/Utilities/Platform') || moduleName === '../Utilities/Platform')) {
    return context.resolveRequest(context, 'react-native-web/dist/exports/Platform', platform);
  }
  if (originalResolveRequest) {
    return originalResolveRequest(context, moduleName, platform);
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
