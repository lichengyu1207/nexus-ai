#!/bin/bash
set -e

ROLE=${1:-backup}
INTERFACE=${2:-eth0}
VIP=${3:-192.168.1.100}
BACKEND_URL=${4:-http://localhost:8000}
WEBHOOK_URL=${5:-}
PRIORITY=${6:-}

echo "=========================================="
echo "  Backup Gateway Deployment Script"
echo "=========================================="
echo "Role: $ROLE"
echo "Interface: $INTERFACE"
echo "VIP: $VIP"
echo "Backend URL: $BACKEND_URL"
echo "=========================================="

if [ "$ROLE" != "master" ] && [ "$ROLE" != "backup" ]; then
    echo "Error: Role must be 'master' or 'backup'"
    echo "Usage: $0 [master|backup] [interface] [vip] [backend_url] [webhook_url]"
    exit 1
fi

echo "[1/8] Updating package list..."
apt update

echo "[2/8] Installing dependencies..."
apt install -y nginx keepalived python3 python3-pip curl

if [ "$ROLE" == "master" ]; then
    echo "[3/8] Configuring Nginx (master)..."
    cat > /etc/nginx/conf.d/forward.conf << 'NGINX_EOF'
upstream backend {
    server BACKEND_URL_PLACEHOLDER;
    keepalive 32;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
NGINX_EOF
    
    sed -i "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL#http://}|g" /etc/nginx/conf.d/forward.conf
    
    nginx -t
    systemctl enable nginx
    systemctl restart nginx
    
    echo "[4/8] Creating Nginx health check script..."
    cat > /usr/local/bin/check_nginx.sh << 'CHECK_EOF'
#!/bin/bash
if pgrep -x nginx > /dev/null; then
    exit 0
else
    exit 1
fi
CHECK_EOF
    chmod +x /usr/local/bin/check_nginx.sh
    
    PRIORITY=${PRIORITY:-100}
    CHECK_SCRIPT="check_nginx"
    ROUTER_ID="LVS_MASTER"
else
    echo "[3/8] Setting up backup gateway..."
    mkdir -p /opt/backup_gateway
    
    cat > /opt/backup_gateway/gateway.py << 'GATEWAY_EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import os
import logging

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')
PORT = int(os.environ.get('PORT', 18790))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def do_PUT(self):
        self.proxy_request()
    
    def do_DELETE(self):
        self.proxy_request()
    
    def proxy_request(self):
        url = BACKEND_URL + self.path
        try:
            req = urllib.request.Request(url, method=self.command)
            for header in self.headers:
                req.add_header(header, self.headers[header])
            if 'Content-Length' in self.headers:
                length = int(self.headers['Content-Length'])
                req.data = self.rfile.read(length)
            with urllib.request.urlopen(req, timeout=5) as response:
                self.send_response(response.getcode())
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            logging.error(f"Proxy error: {e}")
            self.send_error(502, "Bad Gateway")
    
    def log_message(self, format, *args):
        logging.info("%s - %s", self.address_string(), format % args)

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        logging.info(f"Gateway listening on port {PORT}, backend {BACKEND_URL}")
        httpd.serve_forever()
GATEWAY_EOF
    chmod +x /opt/backup_gateway/gateway.py
    
    echo "[4/8] Creating systemd service..."
    cat > /etc/systemd/system/backup-gateway.service << SERVICE_EOF
[Unit]
Description=Backup Gateway
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/backup_gateway/gateway.py
Environment="BACKEND_URL=$BACKEND_URL"
Environment="PORT=80"
Restart=always
User=nobody
Group=nogroup

[Install]
WantedBy=multi-user.target
SERVICE_EOF
    
    systemctl daemon-reload
    systemctl enable backup-gateway
    systemctl start backup-gateway
    
    cat > /usr/local/bin/check_gateway.sh << 'CHECK_EOF'
#!/bin/bash
if systemctl is-active --quiet backup-gateway; then
    exit 0
else
    exit 1
fi
CHECK_EOF
    chmod +x /usr/local/bin/check_gateway.sh
    
    PRIORITY=${PRIORITY:-50}
    CHECK_SCRIPT="check_gateway"
    ROUTER_ID="LVS_BACKUP"
fi

echo "[5/8] Creating notification script..."
cat > /usr/local/bin/notify.sh << NOTIFY_EOF
#!/bin/bash
STATE=\$2
VIP=\$3
if [ "\$STATE" == "MASTER" ]; then
    MESSAGE="VIP \$VIP 已切换到当前节点，成为 MASTER"
elif [ "\$STATE" == "BACKUP" ]; then
    MESSAGE="当前节点成为 BACKUP"
else
    MESSAGE="状态异常: \$STATE"
fi

WEBHOOK_URL="$WEBHOOK_URL"
if [ -n "\$WEBHOOK_URL" ]; then
    curl -X POST -H "Content-Type: application/json" -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"\$MESSAGE\"}}" \$WEBHOOK_URL 2>/dev/null || true
fi

logger -t keepalived-notify "\$MESSAGE"
NOTIFY_EOF
chmod +x /usr/local/bin/notify.sh

echo "[6/8] Configuring Keepalived..."
cat > /etc/keepalived/keepalived.conf << KEEPALIVED_EOF
global_defs {
    router_id $ROUTER_ID
    notification_email {
        admin@example.com
    }
    notification_email_from keepalived@example.com
    smtp_server localhost
    smtp_connect_timeout 30
}

vrrp_script check_service {
    script "/usr/local/bin/$CHECK_SCRIPT.sh"
    interval 2
    weight -20
}

vrrp_instance VI_1 {
    state ${ROLE^^}
    interface $INTERFACE
    virtual_router_id 51
    priority $PRIORITY
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 1234
    }
    virtual_ipaddress {
        $VIP/24 dev $INTERFACE label ${INTERFACE}:1
    }
    track_script {
        check_service
    }
    notify "/usr/local/bin/notify.sh"
}
KEEPALIVED_EOF

echo "[7/8] Enabling and starting Keepalived..."
systemctl enable keepalived
systemctl restart keepalived

echo "[8/8] Verifying deployment..."
sleep 2

if [ "$ROLE" == "master" ]; then
    if systemctl is-active --quiet nginx; then
        echo "✓ Nginx is running"
    else
        echo "✗ Nginx is not running"
    fi
else
    if systemctl is-active --quiet backup-gateway; then
        echo "✓ Backup gateway is running"
    else
        echo "✗ Backup gateway is not running"
    fi
fi

if systemctl is-active --quiet keepalived; then
    echo "✓ Keepalived is running"
else
    echo "✗ Keepalived is not running"
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo "Role: $ROLE"
echo "VIP: $VIP"
echo "Interface: $INTERFACE"
echo "Priority: $PRIORITY"
echo ""
echo "To verify VIP assignment:"
echo "  ip addr show $INTERFACE | grep $VIP"
echo ""
echo "To check logs:"
echo "  journalctl -u keepalived -f"
echo "=========================================="
