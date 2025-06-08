#!/bin/bash

echo "🟢 Minecraft-Server-Installer"
read -p "Servername (z. B. server1): " SERVER_NAME
read -p "RAM in MB (z. B. 2048): " RAM_MB
read -p "Pfad zur JAR-Datei (z. B. /root/Downloads/purpur-1.21.4.jar): " JAR_SOURCE_PATH
JAR_SOURCE_PATH=${JAR_SOURCE_PATH:-/root/Downloads/purpur-1.21.4.jar}

if ! id -u mc >/dev/null 2>&1; then
  echo "❌ Benutzer 'mc' existiert nicht. Bitte zuerst anlegen."
  exit 1
fi

SERVER_DIR="/home/mc/$SERVER_NAME"
JAR_NAME=$(basename "$JAR_SOURCE_PATH")

sudo mkdir -p "$SERVER_DIR"
sudo cp "$JAR_SOURCE_PATH" "$SERVER_DIR/"
sudo chown -R mc:mc "$SERVER_DIR"

echo "eula=true" | sudo tee "$SERVER_DIR/eula.txt" >/dev/null
sudo chown mc:mc "$SERVER_DIR/eula.txt"

LAST_PORT_FILE="/home/mc/.mc_last_port"
if [ ! -f "$LAST_PORT_FILE" ]; then
  echo 25565 | sudo tee "$LAST_PORT_FILE" >/dev/null
fi
LAST_PORT=$(cat "$LAST_PORT_FILE")
PORT=$((LAST_PORT + 1))
RCON_PORT=$((PORT + 1))
echo $((PORT + 2)) | sudo tee "$LAST_PORT_FILE" >/dev/null

# server.properties schreiben
sudo tee "$SERVER_DIR/server.properties" > /dev/null <<EOF
server-port=$PORT
enable-rcon=true
rcon.port=$RCON_PORT
EOF
sudo chown mc:mc "$SERVER_DIR/server.properties"

# RCON Passwort
read -p "RCON-Passwort (leer für zufälliges Passwort): " RCON_PASSWORD
if [ -z "$RCON_PASSWORD" ]; then
  RCON_PASSWORD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 10)
fi
echo "rcon.password=$RCON_PASSWORD" | sudo tee -a "$SERVER_DIR/server.properties" >/dev/null
sudo chown mc:mc "$SERVER_DIR/server.properties"

# Portmapping
PORT_LIST_FILE="/etc/mc-ports.txt"
LINE="$SERVER_NAME=$PORT"
if ! grep -q "^$SERVER_NAME=" "$PORT_LIST_FILE" 2>/dev/null; then
  echo "$LINE" | sudo tee -a "$PORT_LIST_FILE" >/dev/null
fi

# RCON-Zugang speichern
RCON_LIST_FILE="/etc/mc-rcon.txt"
RCON_LINE="$SERVER_NAME=localhost:$RCON_PORT:$RCON_PASSWORD"
if ! grep -q "^$SERVER_NAME=" "$RCON_LIST_FILE" 2>/dev/null; then
  echo "$RCON_LINE" | sudo tee -a "$RCON_LIST_FILE" >/dev/null
fi

# systemd Dienst
SERVICE_FILE="/etc/systemd/system/minecraft@$SERVER_NAME.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Minecraft Server %i
After=network.target

[Service]
User=mc
WorkingDirectory=$SERVER_DIR
ExecStart=/usr/bin/java -Xmx${RAM_MB}M -Xms${RAM_MB}M -jar $JAR_NAME nogui
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "minecraft@$SERVER_NAME"
sudo systemctl start "minecraft@$SERVER_NAME"

echo
echo "✅ Server '$SERVER_NAME' wurde auf Port $PORT mit $RAM_MB MB gestartet."
echo "🛡️ RCON aktiv auf Port $RCON_PORT mit Passwort: $RCON_PASSWORD"
sudo systemctl status "minecraft@$SERVER_NAME" --no-pager
