// Migration script: rename .js/.jsx files to .ts/.tsx and update import statements (source only)
const fs = require('fs');
const path = require('path');

// Directories to exclude from traversal
const EXCLUDE_DIRS = new Set(['node_modules', '.git', 'dist', 'build', 'out', 'coverage', '.next', '.cache']);

function isJSFile(fileName) {
  return fileName.endsWith('.js') || fileName.endsWith('.jsx');
}

function renameFile(oldPath) {
  const newPath = oldPath.replace(/\.jsx?$/ , match => (match === '.js' ? '.ts' : '.tsx'));
  if (newPath !== oldPath) {
    fs.renameSync(oldPath, newPath);
    console.log(`Renamed ${oldPath} → ${newPath}`);
  }
  return newPath;
}

function walkAndRename(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (EXCLUDE_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkAndRename(fullPath);
    } else if (isJSFile(entry.name)) {
      renameFile(fullPath);
    }
  }
}

function updateImports(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (EXCLUDE_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      updateImports(fullPath);
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      const content = fs.readFileSync(fullPath, 'utf8');
      const updated = content
        // import ... from './module.js' → './module.ts'
        .replace(/(import\s+[^'";]+['"])([^'";]+?)\.(js|jsx)(['"];)/g, (m, p1, p2, p3, p4) => `${p1}${p2}.${p3 === 'js' ? 'ts' : 'tsx'}${p4}`)
        // require('./module.ts') → require('./module.ts')
        .replace(/(require\(['"])([^'";]+?)\.(js|jsx)(['"]\))/g, (m, p1, p2, p3, p4) => `${p1}${p2}.${p3 === 'js' ? 'ts' : 'tsx'}${p4}`);
      if (updated !== content) {
        fs.writeFileSync(fullPath, updated, 'utf8');
        console.log(`Updated imports in ${fullPath}`);
      }
    }
  }
}

const projectRoot = process.cwd();
walkAndRename(projectRoot);
updateImports(projectRoot);
console.log('Migration complete (source directories only).');
