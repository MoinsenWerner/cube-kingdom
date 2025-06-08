#!/bin/bash

echo "🔧 Schritt 1: Tailwind CSS bauen..."
./tailwindcss -i ./src/index.css -o ./src/output.css --minify

if [ $? -ne 0 ]; then
  echo "❌ Fehler beim Bauen von Tailwind CSS"
  exit 1
fi

echo "✅ Tailwind CSS fertig → ./src/output.css"

echo "🔧 Schritt 2: React-App bauen (npm run build)..."
npm run build

if [ $? -ne 0 ]; then
  echo "❌ Fehler beim React-Build"
  exit 1
fi

echo "✅ React-App erfolgreich gebaut → ./build/ bereit für Apache2 oder nginx"

cp -r build/* /var/www/serverpanel/build/

echo "wurde kopiert"

systemctl reload apache2

echo "apache wurde neu gestartet"

systemctl restart serverpanel-api.service 

echo "api wurde neu gestartet"