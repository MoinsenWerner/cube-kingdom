import subprocess
import psutil
import re
import socket
import struct
import os
from mcrcon import MCRcon

def read_port_mapping(path="/etc/mc-ports.txt"):
    mapping = {}
    try:
        with open(path, "r") as f:
            for line in f:
                if "=" in line:
                    name, port = line.strip().split("=", 1)
                    mapping[name] = int(port)
    except FileNotFoundError:
        pass
    return mapping

def read_rcon_config(path="/etc/mc-rcon.txt"):
    rcon_map = {}
    try:
        with open(path, "r") as f:
            for line in f:
                if "=" in line:
                    name, val = line.strip().split("=", 1)
                    host, port, password = val.split(":")
                    rcon_map[name] = {
                        "host": host,
                        "port": int(port),
                        "password": password
                    }
    except FileNotFoundError:
        pass
    return rcon_map


def ping_minecraft_server(ip, port, timeout=1.5):
    try:
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            def pack_varint(n):
                out = b""
                while True:
                    temp = n & 0x7F
                    n >>= 7
                    if n:
                        out += struct.pack("B", temp | 0x80)
                    else:
                        out += struct.pack("B", temp)
                        break
                return out

            protocol_version = 754  # Minecraft 1.16+
            server_address = ip.encode("utf-8")
            data = b"\x00" + b"\x04"
            data += struct.pack("!B", len(server_address)) + server_address
            data += struct.pack(">H", port)
            data += b"\x01"
            packet = pack_varint(len(data)) + data
            sock.sendall(packet)
            sock.sendall(b"\x01\x00")

            def read_varint(s):
                num = 0
                for i in range(5):
                    byte = s.recv(1)
                    if not byte:
                        return 0
                    byte = ord(byte)
                    num |= (byte & 0x7F) << (7 * i)
                    if not (byte & 0x80):
                        break
                return num

            read_varint(sock)
            read_varint(sock)
            length = read_varint(sock)
            _ = sock.recv(length)
            return True
    except:
        return False

def list_services():
    result = subprocess.run(
        ["systemctl", "list-unit-files", "--type=service", "--no-pager"],
        capture_output=True, text=True
    )
    matches = re.findall(r"minecraft@([^.]+)\.service", result.stdout)

    port_map = read_port_mapping()
    rcon_map = read_rcon_config()
    status = {}

    for name in matches:
        unit = f"minecraft@{name}"
        mem = cpu = None
        is_active = "inactive"
        is_online = False

        try:
            is_active = subprocess.run(
                ["systemctl", "is-active", unit],
                capture_output=True, text=True
            ).stdout.strip()

            if is_active == "active":
                for proc in psutil.process_iter(['name', 'cwd', 'memory_info', 'cpu_percent']):
                    if (
                        'java' in proc.info['name']
                        and proc.info['cwd']
                        and name in proc.info['cwd']
                    ):
                        mem = proc.info['memory_info'].rss // 1024 // 1024
                        cpu = proc.info['cpu_percent']
                        break

                port = port_map.get(name, 25565)
                is_online = ping_minecraft_server("127.0.0.1", port)

                player_count = None
                rcon = rcon_map.get(name)
                if rcon:
                    player_count = get_player_count_rcon(rcon["host"], rcon["port"], rcon["password"])

            if is_active != "active":
                final_status = "inactive"
            elif is_online:
                final_status = "online"
            else:
                final_status = "active_unresponsive"

            status[unit] = {
                "status": final_status,
                "memory": mem,
                "cpu": cpu,
                "player_count": player_count
            }

        except Exception as e:
            status[unit] = {
                "status": "unknown",
                "error": str(e),
                "memory": None,
                "cpu": None
            }

    return status

def control_service(data):
    action = data.get("action")
    service = data.get("service")
    if action not in ["start", "stop", "restart"]:
        return {"error": "Invalid action"}
    if not service.endswith(".service"):
        service += ".service"
    try:
        subprocess.run(["systemctl", action, service], check=True)
        return {"success": True}
    except:
        return {"success": False}

def get_logs(service):
    if not service.endswith(".service"):
        service += ".service"
    try:
        result = subprocess.run([
            "journalctl", "-u", service, "-n", "50", "--no-pager"
        ], capture_output=True, text=True)
        return {"log": result.stdout}
    except:
        return {"log": "Fehler beim Abrufen"}

def list_server_names():
    result = subprocess.run(
        ["systemctl", "list-unit-files", "--type=service", "--no-pager"],
        capture_output=True, text=True
    )
    matches = re.findall(r"minecraft@([^.]+)\.service", result.stdout)
    return matches

def get_player_count_rcon(host, port, password):
    try:
        with MCRcon(host, password, port) as mcr:
            resp = mcr.command("list")
            match = re.search(r"There (?:are|is) (\d+) of a max (\d+)", resp)
            if match:
                return int(match.group(1))
    except:
        return None


def create_server(name, ram_mb, jar_path="/var/www/html/ck-website/server.jar", rcon_password=""):
    """Create a new Minecraft server using the install script."""
    cmd = ["/root/serverpanel/install_minecraft_server.sh"]
    input_data = f"{name}\n{ram_mb}\n{jar_path}\n{rcon_password}\n"
    try:
        subprocess.run(cmd, input=input_data, text=True, check=True)
        return {"success": True}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
