#!/bin/bash
set -e

# Build frontend
cd frontend
npm ci --legacy-peer-deps
npm run build

# Install backend dependencies
cd ../backend
pip install -r requirements.txt --user
