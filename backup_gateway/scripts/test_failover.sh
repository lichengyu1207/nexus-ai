#!/bin/bash
set -e

echo "=========================================="
echo "  Failover Test Script"
echo "=========================================="

VIP=${1:-192.168.1.100}
INTERFACE=${2:-eth0}
BACKEND_URL=${3:-http://localhost:8000}

check_vip() {
    ip addr show $INTERFACE | grep -q "$VIP"
    return $?
}

check_backend() {
    curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null
}

echo "[1] Checking initial state..."
if check_vip; then
    echo "✓ VIP $VIP is present on this node"
else
    echo "✗ VIP $VIP is NOT present on this node"
fi

echo ""
echo "[2] Testing backend connectivity..."
HTTP_CODE=$(check_backend)
if [ "$HTTP_CODE" == "200" ]; then
    echo "✓ Backend is healthy (HTTP $HTTP_CODE)"
else
    echo "✗ Backend returned HTTP $HTTP_CODE"
fi

echo ""
echo "[3] Testing failover (stopping main service)..."
read -p "Stop nginx/keepalived to test failover? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping nginx..."
    sudo systemctl stop nginx 2>/dev/null || true
    
    echo "Waiting for failover (up to 10 seconds)..."
    for i in {1..10}; do
        sleep 1
        if check_vip; then
            echo "✓ VIP acquired after $i seconds"
            break
        fi
        echo "Waiting... ($i/10)"
    done
    
    if check_vip; then
        echo "✓ Failover successful!"
    else
        echo "✗ Failover failed - VIP not acquired"
    fi
    
    echo ""
    echo "[4] Testing backend through VIP..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$VIP/health" 2>/dev/null)
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✓ Backend accessible through VIP (HTTP $HTTP_CODE)"
    else
        echo "✗ Backend not accessible (HTTP $HTTP_CODE)"
    fi
    
    echo ""
    echo "[5] Restoring master..."
    sudo systemctl start nginx 2>/dev/null || true
    
    echo "Waiting for VIP to return to master..."
    sleep 5
    
    if check_vip; then
        echo "VIP still on this node (expected for backup)"
    else
        echo "VIP returned to master"
    fi
fi

echo ""
echo "=========================================="
echo "  Test Complete"
echo "=========================================="
