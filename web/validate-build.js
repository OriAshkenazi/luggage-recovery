#!/usr/bin/env node

/**
 * Build validation script
 * Checks that all required assets and modules are properly built
 */

import fs from 'fs';
import path from 'path';

const requiredFiles = [
  'assets/js/qrcode.js',
  'assets/fonts/SF-Pro-Rounded-Bold.otf',
  'js/main.js',
  'js/qr-generator.js',
  'js/layout-engine.js',
  'js/dom-builder.js',
  'js/export-manager.js',
  'css/variables.css',
  'css/layout.css',
  'css/components.css',
  'css/controls.css',
  'index.html'
];

const requiredDirectories = [
  'assets',
  'assets/js',
  'assets/fonts',
  'js',
  'css'
];

function checkFiles() {
  console.log('🔍 Validating build files...');

  let allValid = true;

  // Check directories
  for (const dir of requiredDirectories) {
    if (fs.existsSync(dir)) {
      console.log(`✅ Directory: ${dir}`);
    } else {
      console.log(`❌ Missing directory: ${dir}`);
      allValid = false;
    }
  }

  // Check files
  for (const file of requiredFiles) {
    if (fs.existsSync(file)) {
      const stats = fs.statSync(file);
      const sizeKB = Math.round(stats.size / 1024 * 100) / 100;
      console.log(`✅ File: ${file} (${sizeKB}KB)`);

      // Additional checks for specific files
      if (file === 'assets/js/qrcode.js') {
        const content = fs.readFileSync(file, 'utf8');
        if (content.includes('QRCode') && content.length > 1000) {
          console.log(`   📦 QRCode library appears valid`);
        } else {
          console.log(`   ⚠️  QRCode library may be incomplete`);
        }
      }

      if (file === 'assets/fonts/SF-Pro-Rounded-Bold.otf') {
        if (stats.size > 10000) { // Font should be reasonable size
          console.log(`   🔤 Font file appears valid`);
        } else {
          console.log(`   ⚠️  Font file may be too small`);
        }
      }

    } else {
      console.log(`❌ Missing file: ${file}`);
      allValid = false;
    }
  }

  return allValid;
}

function checkESModules() {
  console.log('\n🧩 Validating ES Module structure...');

  const moduleFiles = [
    'js/main.js',
    'js/qr-generator.js',
    'js/layout-engine.js',
    'js/dom-builder.js',
    'js/export-manager.js'
  ];

  let modulesValid = true;

  for (const moduleFile of moduleFiles) {
    try {
      const content = fs.readFileSync(moduleFile, 'utf8');

      // Check for ES module syntax
      const hasExport = content.includes('export') || content.includes('class');
      const hasImport = content.includes('import') || moduleFile === 'js/main.js';

      if (hasExport || hasImport) {
        console.log(`✅ ES Module: ${moduleFile}`);
      } else {
        console.log(`⚠️  Module may have issues: ${moduleFile}`);
      }

    } catch (error) {
      console.log(`❌ Error reading module: ${moduleFile}`);
      modulesValid = false;
    }
  }

  return modulesValid;
}

function main() {
  console.log('🏗️  Build Validation Starting...\n');

  const filesValid = checkFiles();
  const modulesValid = checkESModules();

  console.log('\n📋 Validation Summary:');
  console.log(`Files: ${filesValid ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Modules: ${modulesValid ? '✅ PASS' : '❌ FAIL'}`);

  if (filesValid && modulesValid) {
    console.log('\n🎉 Build validation passed! Application is ready to run.');
    process.exit(0);
  } else {
    console.log('\n💥 Build validation failed! Please fix issues before running.');
    process.exit(1);
  }
}

main();