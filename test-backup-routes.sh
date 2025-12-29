#!/bin/bash

echo "Testing backup routes..."
echo ""

# First login as admin to get token
echo "1. Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to login. Response:"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Login successful, got token"
echo ""

# Test backup info endpoint
echo "2. Testing GET /api/settings/backup/info..."
INFO_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/settings/backup/info)

HTTP_STATUS=$(echo "$INFO_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$INFO_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ Backup info endpoint working! Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "❌ Backup info endpoint failed with status: $HTTP_STATUS"
    echo "Response: $BODY"
fi

echo ""

# Test backup download endpoint
echo "3. Testing GET /api/settings/backup/download..."
DOWNLOAD_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -I \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/settings/backup/download)

HTTP_STATUS=$(echo "$DOWNLOAD_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ Backup download endpoint working!"
    echo "$DOWNLOAD_RESPONSE" | grep -i "content-disposition"
else
    echo "❌ Backup download endpoint failed with status: $HTTP_STATUS"
fi

echo ""
echo "Testing complete!"
