#!/bin/bash

echo "Starting RAG Backend Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Copying .env.example to .env"
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your OPENAI_API_KEY"
    echo "Press Enter to continue after editing .env..."
    read
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting server..."
echo "Backend will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo ""
python -m app.main

