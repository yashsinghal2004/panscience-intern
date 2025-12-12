#!/bin/bash

echo "Starting RAG Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "Copying .env.local.example to .env.local"
    cp .env.local.example .env.local
fi

echo ""
echo "Starting Next.js development server..."
echo "Frontend will be available at http://localhost:3000"
echo ""
npm run dev

