#!/bin/bash
# Deploy callback URL fix to production server

echo "=== Deploying AzamPay Callback URL Fix ==="

# 1. Go to project directory
cd ~/rhci_backend_v1/rhci-portal-backend

# 2. Pull latest changes
git pull origin main

# 3. Restart Django/Gunicorn
echo "Restarting Django services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# 4. Check status
echo "Checking service status..."
sudo systemctl status gunicorn --no-pager
sudo systemctl status nginx --no-pager

echo "=== Deployment Complete ==="
echo "Test callback URL: https://rhci.co.tz/api/v1.0/donors/payment/azampay/callback/"
