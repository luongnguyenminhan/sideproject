#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    touch .env
fi

# Check if PayOS variables exist, add them if not
if ! grep -q "PAYOS_CLIENT_ID" .env; then
    echo "Adding PayOS environment variables..."
    echo "" >> .env
    echo "# PayOS Configuration" >> .env
    echo "PAYOS_CLIENT_ID=your_payos_client_id" >> .env
    echo "PAYOS_API_KEY=your_payos_api_key" >> .env
    echo "PAYOS_CHECKSUM_KEY=your_payos_checksum_key" >> .env
fi

echo "PayOS environment variables have been added to your .env file."
echo "Please update them with your actual PayOS credentials."
