#!/bin/bash

set -e

echo "Building Board Optimizer..."

# Build frontend
echo "Building Svelte frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete!"
echo ""
echo "To run the application:"
echo "  uv run app.py"
echo ""
echo "Then open http://localhost:5000 in your browser"
echo ""
echo "Note: uv will automatically install Python dependencies (Flask, PuLP) on first run"
