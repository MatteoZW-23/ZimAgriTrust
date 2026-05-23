const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

config.resolver.sourceExts.push('mjs');

// Fix for 'Unable to resolve "../Utilities/Platform"' error on Web
const originalResolveRequest = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web' && (moduleName.endsWith('/Utilities/Platform') || moduleName === '../Utilities/Platform')) {
    return {
      type: 'sourceFile',
      filePath: path.join(__dirname, 'src', 'shims', 'ReactNativePlatform.web.js'),
    };
  }
  if (originalResolveRequest) {
    return originalResolveRequest(context, moduleName, platform);
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
