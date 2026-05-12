const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Force Metro to resolve ESM files and handle extensions correctly
config.resolver.sourceExts.push('mjs');

module.exports = config;
