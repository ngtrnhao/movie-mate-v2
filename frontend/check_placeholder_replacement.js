#!/usr/bin/env node
/**
 * Script để kiểm tra việc thay thế placeholder poster
 */
const fs = require('fs');
const path = require('path');

// Tìm tất cả file JS/JSX/TS/TSX
function findFiles(dir, extensions = ['.js', '.jsx', '.ts', '.tsx']) {
  let results = [];
  const list = fs.readdirSync(dir);

  list.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat && stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      results = results.concat(findFiles(filePath, extensions));
    } else if (extensions.some(ext => file.endsWith(ext))) {
      results.push(filePath);
    }
  });

  return results;
}

// Kiểm tra file có chứa placeholder cũ không
function checkFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const oldPlaceholders = [
      '/images/placeholder-poster.jpg',
      '/images/placeholder-movie.jpg',
      '/placeholder-poster.jpg',
      '/placeholder-movie.jpg',
    ];

    const found = oldPlaceholders.filter(placeholder => content.includes(placeholder));

    if (found.length > 0) {
      return {
        file: filePath,
        placeholders: found,
      };
    }

    return null;
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error.message);
    return null;
  }
}

// Kiểm tra file có chứa placeholder mới không
function checkNewPlaceholder(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const newPlaceholder = 'https://placehold.co/600x400';

    if (content.includes(newPlaceholder)) {
      return {
        file: filePath,
        count: (
          content.match(new RegExp(newPlaceholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) ||
          []
        ).length,
      };
    }

    return null;
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error.message);
    return null;
  }
}

console.log('🔍 Checking placeholder replacement...\n');

// Tìm tất cả file frontend
const frontendDir = path.join(__dirname, 'src');
const files = findFiles(frontendDir);

console.log(`📁 Found ${files.length} files to check\n`);

// Kiểm tra placeholder cũ
console.log('❌ Checking for old placeholders:');
const oldPlaceholders = files.map(checkFile).filter(Boolean);

if (oldPlaceholders.length === 0) {
  console.log('   ✅ No old placeholders found!');
} else {
  console.log(`   Found ${oldPlaceholders.length} files with old placeholders:`);
  oldPlaceholders.forEach(item => {
    console.log(`   - ${item.file}`);
    item.placeholders.forEach(placeholder => {
      console.log(`     Contains: ${placeholder}`);
    });
  });
}

console.log('\n✅ Checking for new placeholders:');
const newPlaceholders = files.map(checkNewPlaceholder).filter(Boolean);

if (newPlaceholders.length === 0) {
  console.log('   ❌ No new placeholders found!');
} else {
  console.log(`   Found ${newPlaceholders.length} files with new placeholders:`);
  newPlaceholders.forEach(item => {
    console.log(`   - ${item.file} (${item.count} occurrences)`);
  });
}

console.log('\n📊 Summary:');
console.log(`   Files with old placeholders: ${oldPlaceholders.length}`);
console.log(`   Files with new placeholders: ${newPlaceholders.length}`);

if (oldPlaceholders.length === 0 && newPlaceholders.length > 0) {
  console.log('\n🎉 SUCCESS: All placeholders have been replaced!');
} else if (oldPlaceholders.length > 0) {
  console.log('\n⚠️  WARNING: Some old placeholders still exist!');
} else {
  console.log('\n❌ ERROR: No placeholders found!');
}
