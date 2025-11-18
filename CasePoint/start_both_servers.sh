#!/bin/bash

echo "🚀 Starting KanoonPK - Full Stack Application"
echo "=============================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $FLASK_PID 2>/dev/null
    kill $REACT_PID 2>/dev/null
    exit 0
}

# Set up trap to call cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start Flask backend
echo "📦 Starting Flask Backend (Port 5000)..."
python run_flask_backend.py &
FLASK_PID=$!
sleep 3

# Start React frontend
echo "⚛️  Starting React Frontend (Port 3000)..."
cd frontend
npm run dev &
REACT_PID=$!
cd ..

echo ""
echo "✅ Both servers are running!"
echo "   - Flask Backend:  http://localhost:5000"
echo "   - React Frontend: http://localhost:3000"
echo "   - Flask Admin:    http://localhost:5000/admin"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait
