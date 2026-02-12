const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const archiver = require('archiver');

console.log('🚀 Starting Lambda deployment package creation...\n');

const deployDir = path.join(__dirname, 'lambda-package');
const zipPath = path.join(__dirname, 'lambda-deployment.zip');

// Clean up previous builds
if (fs.existsSync(deployDir)) {
    console.log('🧹 Cleaning up previous build...');
    fs.rmSync(deployDir, { recursive: true, force: true });
}

if (fs.existsSync(zipPath)) {
    fs.unlinkSync(zipPath);
}

// Create deployment directory
console.log('📁 Creating deployment directory...');
fs.mkdirSync(deployDir, { recursive: true });

// Install production dependencies
console.log('📦 Installing production dependencies...');
try {
    execSync('npm install --production --prefix lambda-package', {
        stdio: 'inherit',
        cwd: __dirname
    });
} catch (error) {
    console.error('❌ Error installing dependencies');
    process.exit(1);
}

// Copy necessary files
console.log('📋 Copying application files...');
const filesToCopy = [
    'index.js',
    'database.js',
    'package.json'
];

filesToCopy.forEach(file => {
    fs.copyFileSync(
        path.join(__dirname, file),
        path.join(deployDir, file)
    );
    console.log(`  ✓ ${file}`);
});

// Copy public directory
console.log('📋 Copying public directory...');
const publicDir = path.join(deployDir, 'public');
fs.mkdirSync(publicDir, { recursive: true });
fs.copyFileSync(
    path.join(__dirname, 'public', 'index.html'),
    path.join(publicDir, 'index.html')
);
console.log('  ✓ public/index.html');

// Create ZIP file
console.log('\n📦 Creating ZIP package...');
const output = fs.createWriteStream(zipPath);
const archive = archiver('zip', {
    zlib: { level: 9 } // Maximum compression
});

output.on('close', () => {
    const sizeMB = (archive.pointer() / 1024 / 1024).toFixed(2);
    console.log(`\n✅ Deployment package created successfully!`);
    console.log(`📦 Package: lambda-deployment.zip`);
    console.log(`📊 Size: ${sizeMB} MB`);
    console.log(`\n🎯 Next steps:`);
    console.log(`  1. Upload lambda-deployment.zip to AWS Lambda`);
    console.log(`  2. Set handler to: index.handler`);
    console.log(`  3. Set environment variable: MYSQL_URI`);
    console.log(`  4. Configure API Gateway or Lambda Function URL`);
    console.log(`  5. Ensure Lambda has network access to your RDS instance\n`);

    // Clean up temp directory
    fs.rmSync(deployDir, { recursive: true, force: true });
});

archive.on('error', (err) => {
    throw err;
});

archive.pipe(output);
archive.directory(deployDir, false);
archive.finalize();
