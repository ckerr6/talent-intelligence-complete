#!/bin/bash
# Quick restart script for API and Frontend

echo "🔄 Stopping any running processes..."
pkill -f "python run_api.py" || true
pkill -f "npm run dev" || true
sleep 2

echo ""
echo "🚀 Starting API server..."
echo "   (This will run in the background)"
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python run_api.py > api.log 2>&1 &
API_PID=$!
echo "   API started with PID: $API_PID"
echo "   Logs: tail -f api.log"

sleep 3

echo ""
echo "🌐 Starting Frontend..."
echo "   (This will run in the background)"
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/frontend
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend started with PID: $FRONTEND_PID"
echo "   Logs: tail -f frontend/frontend.log"

sleep 3

echo ""
echo "✅ BOTH SERVICES STARTED!"
echo ""
echo "📊 Status:"
echo "   API:      http://localhost:8000 (PID: $API_PID)"
echo "   Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "📝 Logs:"
echo "   API logs:      tail -f api.log"
echo "   Frontend logs: tail -f frontend/frontend.log"
echo ""
echo "🛑 To stop:"
echo "   kill $API_PID $FRONTEND_PID"
echo ""
echo "🧪 Test URLs:"
echo "   - Search: http://localhost:3000/search"
echo "   - Market: http://localhost:3000/market"
echo "   - Network: http://localhost:3000/network/enhanced"
echo ""
echo "⏳ Waiting 5 seconds for services to fully start..."
sleep 5

echo ""
echo "🔍 Testing API health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ API not responding yet, give it a few more seconds"

echo ""
echo "✨ Ready to test! Open http://localhost:3000 in your browser"
echo ""

