const { spawnSync } = require('child_process');
const path = require('path');

const expoBin = path.join(
  __dirname,
  '..',
  'node_modules',
  '.bin',
  process.platform === 'win32' ? 'expo.cmd' : 'expo'
);

const result = spawnSync(expoBin, process.argv.slice(2), {
  cwd: path.join(__dirname, '..'),
  env: {
    ...process.env,
    EXPO_NO_METRO_WORKSPACE_ROOT: '1',
  },
  stdio: 'inherit',
  shell: process.platform === 'win32',
});

process.exit(result.status ?? 1);
