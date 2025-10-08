// Entry point for browserify to bundle QRCode for browser use
const QRCode = require('qrcode');

// Make QRCode available globally
window.QRCode = QRCode;