// Safe migration script: rename .js/.jsx to .ts/.tsx, skipping node_modules and dotfolders
const fs = require('fs');
const path = require('path');

function isJSFile(file) {
  return file.endsWith('.js') || file.endsWith('.jsx');
}

function renameFile(oldPath) {
  const newPath = oldPath.replace(/\.jsx?$/,
    match => (match === '.js' ? '.ts' : '.tsx'));
  if (newPath !== oldPath) {
    try {
      fs.renameSync(oldPath, newPath);
      console.log(`Renamed ${oldPath} → ${newPath}`);
    } catch (e) {
      console.error(`Failed to rename ${oldPath}: ${e.message}`);
    }
  }
  return newPath;
}

function walkAndRename(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    console.error(`Cannot read ${dir}: ${e.message}`);
    return;
  }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    // skip node_modules and hidden folders
    if (entry.isDirectory() && (entry.name === 'node_modules' || entry.name.startsWith('.')))
      continue;
    if (entry.isDirectory()) {
      walkAndRename(fullPath);
    } else if (isJSFile(entry.name)) {
      renameFile(fullPath);
    }
  }
}

function updateImports(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    console.error(`Cannot read ${dir}: ${e.message}`);
    return;
  }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory() && (entry.name === 'node_modules' || entry.name.startsWith('.')))
      continue;
    if (entry.isDirectory()) {
      updateImports(fullPath);
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      let content;
      try {
        content = fs.readFileSync(fullPath, 'utf8');
      } catch (e) {
        console.error(`Cannot read ${fullPath}: ${e.message}`);
        continue;
      }
      const updated = content
        .replace(/(import\s+[^'\"]+['\"])([^'\"]+?)\.(js|jsx)(['\"])/g, (_, p1, p2, p3, p4) =>
          `${p1}${p2}.${p3 === 'js' ? 'ts' : 'tsx'}${p4}`)
        .replace(/(require\(['\"])([^'\"]+?)\.(js|jsx)(['\"]\))/g, (_, p1, p2, p3, p4) =>
          `${p1}${p2}.${p3 === 'js' ? 'ts' : 'tsx'}${p4}`);
      if (updated !== content) {
        try {
          fs.writeFileSync(fullPath, updated, 'utf8');
          console.log(`Updated imports in ${fullPath}`);
        } catch (e) {
          console.error(`Failed to write ${fullPath}: ${e.message}`);
        }
      }
    }
  }
}

// Execute migration from the project root
const projectRoot = process.cwd();
walkAndRename(projectRoot);
updateImports(projectRoot);
console.log('Migration complete.');
