const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

// Backend URL - use environment variable or default to Railway backend
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://backend-production-ceb1.up.railway.app';

// Proxy /api requests to the backend
app.use('/api', createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/api': '/api' // Keep /api prefix
    },
    onError: (err, req, res) => {
        console.error('Proxy error:', err.message);
        res.status(502).json({ error: 'Backend unavailable' });
    }
}));

// Serve static files from the React build directory
app.use(express.static(path.join(__dirname, 'build')));

// Handle React routing - return index.html for all non-api routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Frontend server running on port ${PORT}`);
    console.log(`Proxying /api requests to: ${BACKEND_URL}`);
});
