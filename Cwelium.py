# Copyright (c) 2024-2026 Masumani Inc.
# 完全版 – ボイス自動切断防止＋スパマー全バグ修正＋全機能維持
# このファイル全体で既存の masumani.py を完全置換してください。

import getpass
import sys
import select
import threading
import time
import random
import json as json_lib
import base64
import ctypes
import os
import re
import requests
import zlib
import socket
import string
import uuid
import websocket
import concurrent.futures
from collections import defaultdict, deque
from datetime import datetime, timedelta
from colorama import Fore, init; init(autoreset=True)
from colorist import ColorHex as h

# ---------- curl_cffi 優先インポート ----------
try:
    import curl_cffi
    USE_CURL_CFFI = True
except ImportError:
    USE_CURL_CFFI = False
    print("[!] curl_cffi not installed. Install with: pip install curl_cffi")
    print("[!] Falling back to requests (higher detection risk).")

# ---------- 終了イベント（スレッドセーフ） ----------
SHOULD_STOP = threading.Event()

# ---------- 設定 ----------
CONFIG_FILE = "config.json"

def load_config():
    default = {
        "Proxies": True,
        "Theme": "light_blue",
        "ApiVersion": "v10",
        "DelayMean": 4.0,
        "DelayStd": 1.5,
        "MinDelay": 2.0,
        "MaxDelay": 10.0,
        "UseTyping": False,
        "MessageVariation": True,
        "JoinerDelayMin": 15,
        "JoinerDelayMax": 45,
        "GlobalRateLimit": True,
        "RateLimitPerSecond": 2,
        "StatusRotation": True,
        "StatusInterval": 300,
        "CustomStatuses": ["Idle", "AFK", "Online"],
        "CacheTTL": 600,
        "MaxWorkers": 8,
        "MaxRetries": 5,
        "RetryBackoffBase": 3,
        "ProxyRotation": "random"
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                data = json_lib.loads(f.read())
                default.update(data)
            except:
                pass
    return default

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        f.write(json_lib.dumps(config, indent=2))

config = load_config()
proxy = config.get("Proxies", True)
color = config.get("Theme", "light_blue")
api_version = config.get("ApiVersion", "v10")
delay_mean = config.get("DelayMean", 4.0)
delay_std = config.get("DelayStd", 1.5)
min_delay = config.get("MinDelay", 2.0)
max_delay = config.get("MaxDelay", 10.0)
use_typing = config.get("UseTyping", False)
message_variation = config.get("MessageVariation", True)
joiner_delay_min = config.get("JoinerDelayMin", 15)
joiner_delay_max = config.get("JoinerDelayMax", 45)
global_rate_limit = config.get("GlobalRateLimit", True)
rate_limit_per_second = config.get("RateLimitPerSecond", 2)
status_rotation = config.get("StatusRotation", True)
status_interval = config.get("StatusInterval", 300)
custom_statuses = config.get("CustomStatuses", ["Idle", "AFK", "Online"])
cache_ttl = config.get("CacheTTL", 600)
max_workers = config.get("MaxWorkers", 8)
max_retries = config.get("MaxRetries", 5)
retry_backoff = config.get("RetryBackoffBase", 3)
API_BASE = f"https://discord.com/api/{api_version}"

# ---------- 色定義 ----------
C = {
    "green": h("#65fb07"), "red": h("#Fb0707"), "yellow": h("#FFCD00"),
    "magenta": h("#b207f5"), "blue": h("#00aaff"), "cyan": h("#aaffff"),
    "gray": h("#8a837e"), "white": h("#DCDCDC"), "pink": h("#c203fc"),
    "light_blue": h("#07f0ec"), "brown": h("#8B4513"), "black": h("#000000"),
    "aqua": h("#00CED1"), "purple": h("#800080"), "lime": h("#00FF00"),
    "orange": h("#FFA500"), "indigo": h("#4B0082"), "violet": h("#EE82EE"),
    "gold": h("#FFD700"), "silver": h("#C0C0C0"), "teal": h("#008080"),
    "navy": h("#000080"), "olive": h("#808000"), "maroon": h("#800000"),
    "coral": h("#FF7F50"), "salmon": h("#FA8072"), "khaki": h("#F0E68C"),
    "orchid": h("#DA70D6"), "rose": h("#FF007F")
}

# ---------- ユーティリティ ----------
def get_random_str(length):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def wrapper(func):
    def wrapper(*args, **kwargs):
        console.clear()
        console.render_ascii()
        return func(*args, **kwargs)
    return wrapper

def retry_api(func):
    def wrapper(self, *args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(self, *args, **kwargs)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, socket.error) as e:
                last_exception = e
                wait = min(60, retry_backoff * (2 ** attempt) + random.uniform(0, 2))
                console.log("Retry", C["yellow"], False, f"{func.__name__} 接続エラー、{wait:.1f}s待機 ({attempt+1}/{max_retries})")
                time.sleep(wait)
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    wait = min(60, retry_backoff * (2 ** attempt) + random.uniform(0, 5))
                    console.log("RateLimit", C["magenta"], False, f"{func.__name__} 429、{wait:.1f}s待機")
                    time.sleep(wait)
                else:
                    raise
        raise last_exception or Exception("Max retries exceeded")
    return wrapper

class JsonWrapper:
    @staticmethod
    def loads(data, **kwargs):
        return json_lib.loads(data)
    @staticmethod
    def load(fp, **kwargs):
        return json_lib.load(fp)
    @staticmethod
    def dumps(data, indent=None, separators=None, sort_keys=False, **kwargs):
        return json_lib.dumps(data, indent=indent, separators=separators, sort_keys=sort_keys)
    @staticmethod
    def dump(data, fp, indent=None, separators=None, sort_keys=False, **kwargs):
        return json_lib.dump(data, fp, indent=indent, separators=separators, sort_keys=sort_keys)

json = JsonWrapper()

# ---------- コンソールレンダラー ----------
class Render:
    def __init__(self):
        self.size = os.get_terminal_size().columns
        self.print_lock = threading.Lock()
        self.theme_name = color if color in C else "light_blue"
        self.theme_hex = C[self.theme_name].hex
        self.background = C[self.theme_name]
        self.username = getpass.getuser()
    def title(self, title):
        try:
            if os.name == 'nt':
                ctypes.windll.kernel32.SetConsoleTitleW(title)
            else:
                sys.stdout.write(f"\x1b]2;{title}\x07")
                sys.stdout.flush()
        except: pass
    def clear(self):
        sys.stdout.write("\033[2J\033[H\033[3J")
        sys.stdout.flush()
    def _get_shade(self, x, y, width, height):
        def hex_to_rgb(h_code):
            h_code = h_code.lstrip('#')
            return tuple(int(h_code[i:i+2], 16) for i in (0, 2, 4))
        start_rgb = hex_to_rgb(self.theme_hex)
        end_rgb = (int(start_rgb[0] * 0.35), int(start_rgb[1] * 0.35), int(start_rgb[2] * 0.35))
        w_idx, h_idx = max(1, width - 1), max(1, height - 1)
        factor = (x * w_idx + y * h_idx) / (w_idx**2 + h_idx**2)
        factor = max(0, min(1, factor))
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * factor)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * factor)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * factor)
        return h(f'#{r:02x}{g:02x}{b:02x}')
    def center_colored(self, text, visible_len):
        try:
            terminal_width = os.get_terminal_size().columns
        except:
            terminal_width = self.size
        padding = max(0, (terminal_width - visible_len) // 2)
        return (" " * padding) + text
    def render_ascii(self):
        self.clear()
        self.title(f"Masumani Ultimate | {self.username} | by Tips-Discord")
        edges = {"╗", "║", "╚", "╝", "═", "╔"}
        logo = [
            " ███╗   ███╗ █████╗ ███████╗██╗   ██╗███╗   ███╗ █████╗ ███╗   ██╗██╗",
            " ████╗ ████║██╔══██╗██╔════╝██║   ██║████╗ ████║██╔══██╗████╗  ██║██║",
            " ██╔████╔██║███████║███████╗██║   ██║██╔████╔██║███████║██╔██╗ ██║██║",
            " ██║╚██╔╝██║██╔══██║╚════██║██║   ██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║",
            " ██║ ╚═╝ ██║██║  ██║███████║╚██████╔╝██║ ╚═╝ ██║██║  ██║██║ ╚████║██║",
            " ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝",
        ]
        height = len(logo); width = max(len(line) for line in logo)
        print("\n")
        for y, line in enumerate(logo):
            colored_line = ""; visible_len = 0
            for x, char in enumerate(line):
                if char in edges:
                    colored_line += f"{self._get_shade(x, y, width, height)}{char}{C['white']}"
                else:
                    colored_line += char
                visible_len += 1
            print(self.center_colored(colored_line, visible_len))
        print("\n")
    def raider_options(self):
        try:
            with open("data/proxies.txt") as f:
                proxies = [p.strip() for p in f.read().splitlines() if p.strip()]
        except: proxies = []
        try:
            with open("data/tokens.txt", "r") as f:
                tokens = [t.strip() for t in f.read().splitlines() if t.strip()]
        except: tokens = []
        menu_edges = {"─", "╭", "│", "╰", "╯", "╮", "»", "«"}
        menu = [
            "╭─────────────────────────────────────────────────────────────────────────────────────────────────────╮",
            "│ «01» Joiner            «07» Token Formatter    «13» Onliner           «19» Call Spammer             │",
            "│ «02» Leaver            «08» Button Click       «14» Voice Raper       «20» Bio Change               │",
            "│ «03» Spammer           «09» Accept Rules       «15» Change Nick       «21» Voice Joiner             │",
            "│ «04» Token Checker     «10» Guild Check        «16» Thread Spammer    «22» Onboard Bypass           │",
            "│ «05» Emoji Reaction    «11» Friend Spam        «17» Typer             «23» Dm Spammer               │",
            "│ «06» Clear Status      «12» ???                «18» ???               «24» Exit                     │",
            "│ «25» Poll Spammer      «26» Mass Timeout       «27» Mass Nick All     «28» Schedule Spam            │",
            "│ «29» Ext Bot Setup     «30» Ext Bot Spam       «31» Ext Bot Status    «32» Token Quality            │",
            "│ «33» Status Manager    «34» Adv Reaction       «35» Repeat Schedule   «36» Cache Clear              │",
            "╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯",
            "«h» Help   «~» Credits"
        ]
        stats_text = f"Loaded ‹{len(tokens)}› tokens | Loaded ‹{len(proxies)}› proxies"
        stats_colored = f"Loaded ‹{self.background}{len(tokens)}{Fore.RESET}› tokens | Loaded ‹{self.background}{len(proxies)}{Fore.RESET}› proxies"
        print(self.center_colored(stats_colored, len(stats_text)) + "\n")
        h_menu = len(menu); w_menu = len(menu[0])
        for y, line in enumerate(menu):
            colored_line = ""; visible_len = 0
            for x, char in enumerate(line):
                if char in menu_edges:
                    shade = self._get_shade(x, y, w_menu, h_menu)
                    colored_line += f"{shade}{char}{C['white']}"
                else:
                    colored_line += char
                visible_len += 1
            print(self.center_colored(colored_line, visible_len))
        print("\n")
    def run(self):
        self.render_ascii()
        self.raider_options()
    def log(self, text=None, color=None, token=None, log=None):
        response = f"{Fore.RESET}[{datetime.now().strftime(f'{Fore.LIGHTBLACK_EX}%H:%M:%S{Fore.RESET}')}] "
        if text:
            response += f"[{color}{text}{C['white']}] "
        if token:
            response += token
        if log:
            response += f" ({C['gray']}{log}{C['white']})"
        response += f"{Fore.RESET}"
        with self.print_lock:
            print(response)
    def prompt(self, text, ask=None):
        prompted = f"{Fore.RESET}[{Fore.LIGHTBLACK_EX}{datetime.now().strftime('%H:%M:%S')}{Fore.RESET}] {C[color]}➜{Fore.RESET}  {Fore.WHITE}{text}{Fore.RESET}"
        if ask:
            prompted += f" {Fore.LIGHTBLACK_EX}({C['green']}y{Fore.RESET}{Fore.LIGHTBLACK_EX}/{C['red']}n{Fore.RESET}{Fore.LIGHTBLACK_EX}){Fore.LIGHTBLACK_EX}:{Fore.RESET} "
        else:
            prompted += f"{C[color]}:{Fore.RESET} "
        return prompted

console = Render()

# ---------- ヘッダー自動取得 ----------
class AutoFetchHeaders:
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9219 Chrome/138.0.7204.251 Electron/37.6.0 Safari/537.36"
    client_build_number = 482285
    native_build_number = 73385
    client_version = "1.0.9219"
    browser_version = "37.6.0"
    _fetched = False
    @staticmethod
    def fetch():
        if AutoFetchHeaders._fetched: return
        try:
            console.log("Scraping", C["light_blue"], False, "Fetching latest Discord headers...")
            resp = requests.get("https://api.sockets.lol/discord/build", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "clients" in data and "Discord" in data["clients"]:
                    d = data["clients"]["Discord"]["decoded"]
                    if d.get("release_channel") == "stable":
                        AutoFetchHeaders.user_agent = d["browser_user_agent"]
                        AutoFetchHeaders.client_version = d["client_version"]
                        AutoFetchHeaders.browser_version = d["browser_version"]
                        AutoFetchHeaders.native_build_number = d["native_build_number"]
                        AutoFetchHeaders.client_build_number = d["client_build_number"]
                        console.log("Success", C["green"], False, f"Build {AutoFetchHeaders.client_build_number} | v{AutoFetchHeaders.client_version}")
                        AutoFetchHeaders._fetched = True
        except Exception as e:
            console.log("Failed", C["red"], False, f"Header fetch: {e}")

# ---------- グローバルレートリミッター ----------
class GlobalRateLimiter:
    def __init__(self):
        self.buckets = defaultdict(lambda: {"timestamps": deque(maxlen=100), "reset": 0, "retry_after": 0})
        self.lock = threading.Lock()
        self.per_second = rate_limit_per_second

    def can_request(self, endpoint):
        if not global_rate_limit: return True
        with self.lock:
            now = time.time()
            bucket = self.buckets[endpoint]
            if now > bucket["reset"]:
                bucket["timestamps"].clear()
                bucket["reset"] = now + 1.0
                bucket["retry_after"] = 0
            if len(bucket["timestamps"]) >= self.per_second:
                return False
            bucket["timestamps"].append(now)
            return True

    def wait_if_needed(self, endpoint):
        if not global_rate_limit: return
        while not self.can_request(endpoint):
            time.sleep(0.05 + random.uniform(0, 0.1))

    def update_from_response(self, endpoint, response):
        try:
            if response.status_code == 429:
                data = response.json()
                retry_after = data.get("retry_after", 5) + random.uniform(0, 1.5)
                with self.lock:
                    self.buckets[endpoint]["reset"] = time.time() + retry_after
                    self.buckets[endpoint]["retry_after"] = retry_after
        except: pass

global_rate_limiter = GlobalRateLimiter()

# ---------- WebSocketPool 完全強化 ----------
class WebSocketPool:
    def __init__(self):
        self._connections = {}
        self._lock = threading.Lock()

    def _is_ws_alive(self, ws):
        try:
            ws.send(json.dumps({"op": 1, "d": None}))
            return True
        except: return False

    def get_connection(self, token):
        with self._lock:
            now = time.time()
            if token in self._connections:
                ws, last_used, created = self._connections[token]
                if now - last_used < 90 and self._is_ws_alive(ws):
                    self._connections[token] = (ws, now, created)
                    return ws
                else:
                    try: ws.close()
                    except: pass
                    del self._connections[token]
            try:
                ws = websocket.WebSocket()
                ws.connect("wss://gateway.discord.gg/?v=10&encoding=json", timeout=15)
                identify = {
                    "op": 2,
                    "d": {
                        "token": token,
                        "properties": {"os": "Windows", "browser": "Discord", "device": "desktop"},
                        "presence": {"status": "online", "since": 0, "activities": [], "afk": False}
                    }
                }
                ws.send(json.dumps(identify))
                self._connections[token] = (ws, now, now)
                return ws
            except Exception as e:
                console.log("WS Pool Error", C["red"], f"{token[:15]}...", f"接続失敗: {e}")
                return None

    def close_all(self):
        with self._lock:
            for token, (ws, _, _) in self._connections.items():
                try: ws.close()
                except: pass
            self._connections.clear()

ws_pool = WebSocketPool()

# ---------- ユーティリティ ----------
class Utils:
    @staticmethod
    def get_ranges(index, multiplier):
        initial = index * multiplier
        return [[initial, initial + 99], [initial + 100, initial + 199]]
    @staticmethod
    def parse_member_list_update(data):
        d = data["d"]
        return {"online_count": d["online_count"], "member_count": d["member_count"], "guild_id": d["guild_id"], "ops": d["ops"]}
    @staticmethod
    def safe_json_parse(text):
        try: return json.loads(text)
        except: return None

# ---------- DiscordSocket スクレイパー ----------
class DiscordSocket(websocket.WebSocketApp):
    def __init__(self, token, guild_id, channel_id, timeout=30):
        self.start = time.time()
        self.token = token
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.timeout = timeout
        self.blacklisted_ids = {
            "1100342265303547924", "1190052987477958806", "833007032000446505",
            "1273658880039190581", "1308012310396407828", "1326906424873193586",
            "1334512667456442411", "1349869929809186846", "1171574570092871700",
        }
        self.buffer = bytearray()
        self.inflator = zlib.decompressobj()
        self.ready_event = threading.Event()
        self.end_scraping = False
        self.guild_member_count = 0
        self.members = {}
        self.ranges = [[0, 99]]
        self.last_range = 0
        self.packets_recv = 0
        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "User-Agent": AutoFetchHeaders.user_agent,
        }
        super().__init__(
            "wss://gateway.discord.gg/?encoding=json&v=10&compress=zlib-stream",
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )

    def run(self):
        self.run_forever(sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),))
        return self.members

    def scrape_users(self):
        if self.end_scraping: return
        payload = {"op": 14, "d": {"guild_id": self.guild_id, "typing": False, "activities": False, "threads": False, "channels": {self.channel_id: self.ranges}}}
        self.send(json.dumps(payload))

    def on_open(self, ws):
        self.send(json.dumps({
            "op": 2,
            "d": {
                "token": self.token,
                "capabilities": 1734653,
                "properties": {
                    "os": "Windows", "browser": "Chrome", "device": "",
                    "system_locale": "en-US", "browser_user_agent": AutoFetchHeaders.user_agent,
                    "browser_version": AutoFetchHeaders.browser_version, "os_version": "10",
                    "referrer": "", "referring_domain": "", "release_channel": "stable",
                    "client_build_number": AutoFetchHeaders.client_build_number,
                },
                "presence": {"status": "online", "since": 0, "activities": [], "afk": False},
                "compress": False, "client_state": {"guild_hashes": {}, "highest_last_message_id": "0"}
            }
        }))
        self.ready_event.set()

    def heartbeat_thread(self, interval):
        while not self.end_scraping:
            try:
                self.send(json.dumps({"op": 1, "d": self.packets_recv}))
                time.sleep(interval)
            except: break

    def on_message(self, ws, message):
        if isinstance(message, bytes):
            self.buffer.extend(message)
            if len(message) < 4 or message[-4:] != b'\x00\x00\xff\xff': return
            try:
                message = self.inflator.decompress(self.buffer).decode("utf-8")
                self.buffer = bytearray()
            except: return
        decoded = Utils.safe_json_parse(message)
        if decoded is None: return
        op = decoded.get("op"); t = decoded.get("t")
        self.packets_recv += 1 if op != 11 else 0
        if op == 10:
            interval = decoded["d"]["heartbeat_interval"] / 1000
            threading.Thread(target=self.heartbeat_thread, args=(interval,), daemon=True).start()
        elif t == "READY":
            for guild in decoded["d"]["guilds"]:
                if guild["id"] == self.guild_id:
                    self.guild_member_count = guild.get("member_count", 0); break
            console.log("Info", C["yellow"], False, f"Target: {self.guild_member_count} members")
        elif t == "READY_SUPPLEMENTAL":
            self.ranges = Utils.get_ranges(0, 100); self.scrape_users()
        elif t == "GUILD_MEMBER_LIST_UPDATE":
            parsed = Utils.parse_member_list_update(decoded)
            if parsed["guild_id"] == self.guild_id:
                should_continue = False
                for op_chunk in parsed["ops"]:
                    op_type = op_chunk["op"]
                    if op_type in ("SYNC", "UPDATE"):
                        items = op_chunk.get("items") if op_type == "SYNC" else [op_chunk.get("item")]
                        if not items: continue
                        for item in items:
                            member = item.get("member")
                            if not member: continue
                            user = member.get("user")
                            if not user: continue
                            uid = user.get("id")
                            if uid and uid not in self.blacklisted_ids and not user.get("bot"):
                                self.members[uid] = {"tag": f"{user.get('username')}#{user.get('discriminator', '0')}", "id": uid}
                        should_continue = True
                    elif op_type == "INVALIDATE":
                        self.ranges = Utils.get_ranges(self.last_range, 100); self.scrape_users()
                if len(self.members) >= self.guild_member_count or not should_continue:
                    if (self.last_range * 100) >= self.guild_member_count:
                        self.end_scraping = True; self.close(); return
                self.last_range += 2
                self.ranges = Utils.get_ranges(self.last_range, 100)
                self.scrape_users()

    def on_error(self, ws, error):
        if not self.end_scraping:
            console.log("Error", C["red"], False, f"Socket Error: {error}")
    def on_close(self, ws, close_code, close_msg):
        if self.end_scraping:
            console.log("Success", C["green"], False, f"Scraped {len(self.members)} members in {time.time()-self.start:.2f}s")
        else:
            console.log("Info", C["yellow"], False, f"Socket closed, scraped {len(self.members)} members")

# ---------- VoiceConnection クラス（ボイス維持専用） ----------
class VoiceConnection:
    def __init__(self, token, guild_id, channel_id):
        self.token = token
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.ws = None
        self.running = False
        self.thread = None
        self.heartbeat_interval = 30
        self.last_heartbeat = 0
        self.voice_server_id = None
        self.session_id = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

    def _run(self):
        while self.running:
            try:
                self._connect_and_loop()
            except Exception as e:
                console.log("Voice Error", C["red"], f"{self.token[:15]}...", str(e))
                time.sleep(5)

    def _connect_and_loop(self):
        self.ws = websocket.WebSocket()
        self.ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
        self.ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {"os": "Windows", "browser": "Discord", "device": "desktop"},
                "presence": {"status": "online", "since": 0, "activities": [], "afk": False}
            }
        }))
        self.ws.send(json.dumps({
            "op": 4,
            "d": {
                "guild_id": self.guild_id,
                "channel_id": self.channel_id,
                "self_mute": False,
                "self_deaf": False,
                "self_stream": False,
                "self_video": True
            }
        }))
        self.last_heartbeat = time.time()
        while self.running:
            try:
                self.ws.settimeout(5)
                try:
                    msg = self.ws.recv()
                    if msg:
                        data = json.loads(msg)
                        op = data.get("op")
                        if op == 10:
                            interval = data["d"]["heartbeat_interval"] / 1000
                            self.heartbeat_interval = interval
                        elif op == 11:
                            pass
                        elif op == 0 and data.get("t") == "VOICE_SERVER_UPDATE":
                            self.voice_server_id = data["d"]["guild_id"]
                            self.session_id = data["d"].get("session_id")
                except websocket.WebSocketTimeoutException:
                    pass
                if time.time() - self.last_heartbeat > self.heartbeat_interval:
                    self.ws.send(json.dumps({"op": 1, "d": None}))
                    self.last_heartbeat = time.time()
                if time.time() - self.last_heartbeat > 15:
                    self.ws.send(json.dumps({
                        "op": 4,
                        "d": {
                            "guild_id": self.guild_id,
                            "channel_id": self.channel_id,
                            "self_mute": False,
                            "self_deaf": False,
                            "self_stream": False,
                            "self_video": True
                        }
                    }))
            except Exception as e:
                console.log("Voice Loop Error", C["red"], f"{self.token[:15]}...", str(e))
                break
        try:
            self.ws.close()
        except:
            pass

# ---------- Raider クラス ----------
class Raider:
    def __init__(self):
        self._load_tokens_proxies()
        AutoFetchHeaders.fetch()
        self.cached_members = {}
        self.cache_timestamps = {}
        self._sessions = {}
        self._session_lock = threading.Lock()
        self._proxy_pool = self.proxies if proxy else []
        self._proxy_index = 0
        self.status_thread_running = False
        self._impersonate_list = ["chrome110", "chrome120", "chrome124", "chrome136", "edge101", "firefox101", "firefox100"]
        self._voice_connections = {}  # ボイス接続管理
        if USE_CURL_CFFI:
            console.log("Info", C["cyan"], False, "curl_cffi enabled (TLS fingerprint spoofing)")
        else:
            console.log("Info", C["yellow"], False, "curl_cffi unavailable, using requests (higher risk)")

    def _load_tokens_proxies(self):
        try:
            with open("data/proxies.txt") as f:
                self.proxies = [p.strip() for p in f.read().splitlines() if p.strip()]
        except:
            self.proxies = []
        try:
            with open("data/tokens.txt", "r") as f:
                self.tokens = [t.strip() for t in f.read().splitlines() if t.strip()]
        except:
            self.tokens = []

    def _get_next_proxy(self):
        if not self._proxy_pool: return None
        if config.get("ProxyRotation", "random") == "random":
            return random.choice(self._proxy_pool)
        self._proxy_index = (self._proxy_index + 1) % len(self._proxy_pool)
        return self._proxy_pool[self._proxy_index]

    def _get_impersonate(self):
        return random.choice(self._impersonate_list)

    def get_session(self, token, force_new=False):
        with self._session_lock:
            if force_new or token not in self._sessions:
                if USE_CURL_CFFI:
                    try:
                        self._sessions[token] = curl_cffi.Session(impersonate=self._get_impersonate())
                    except Exception as e:
                        console.log("Fallback", C["yellow"], f"{token[:15]}...", f"curl_cffi err ({e}), using requests")
                        self._sessions[token] = requests.Session()
                        self._sessions[token].headers.update({"User-Agent": AutoFetchHeaders.user_agent})
                else:
                    self._sessions[token] = requests.Session()
                    self._sessions[token].headers.update({"User-Agent": AutoFetchHeaders.user_agent})
            return self._sessions[token]

    @retry_api
    def _request(self, method, url, token, headers=None, json=None, params=None, timeout=15):
        endpoint = url.split(f"/api/{api_version}/")[-1] if f"/api/{api_version}/" in url else url
        global_rate_limiter.wait_if_needed(endpoint)
        sess = self.get_session(token)
        if proxy and self._proxy_pool:
            proxy_url = self._get_next_proxy()
            sess.proxies = {"http": f"http://{proxy_url}", "https": f"http://{proxy_url}"}
        else:
            sess.proxies = {}
        resp = sess.request(method=method, url=url, headers=headers, json=json, params=params, timeout=timeout)
        global_rate_limiter.update_from_response(endpoint, resp)
        if resp.status_code >= 500:
            raise Exception(f"Server error {resp.status_code}")
        return resp

    def headers_minimal(self, token):
        return {"Authorization": token, "User-Agent": AutoFetchHeaders.user_agent, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}

    def headers_full(self, token):
        return {
            "Authorization": token, "User-Agent": AutoFetchHeaders.user_agent,
            "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "X-Super-Properties": self.generate_super_properties(),
            "X-Debug-Options": "bugReporterEnabled", "X-Discord-Locale": "en-US"
        }

    def generate_super_properties(self):
        payload = {
            "os": "Windows", "browser": "Discord Client", "release_channel": "stable",
            "client_version": AutoFetchHeaders.client_version, "os_version": "10.0.26100",
            "system_locale": "en-US", "browser_user_agent": AutoFetchHeaders.user_agent,
            "browser_version": AutoFetchHeaders.browser_version,
            "client_build_number": AutoFetchHeaders.client_build_number,
            "native_build_number": AutoFetchHeaders.native_build_number,
            "client_launch_id": str(uuid.uuid4()), "client_heartbeat_session_id": str(uuid.uuid4()),
            "launch_signature": str(uuid.uuid4()), "client_event_source": None, "has_client_mods": False
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def nonce(self):
        return int(time.time() * 1000) - 1420070400000 << 22

    def human_delay(self):
        delay = random.gauss(delay_mean, delay_std)
        delay = max(min_delay, min(delay, max_delay))
        if random.random() < 0.2:
            delay += random.uniform(0.3, 1.2)
        time.sleep(delay)
        return delay

    def vary_message(self, base_message):
        if not message_variation: return base_message
        url_pattern = re.compile(r'https?://[^\s]+|discord\.gg/[^\s]+|discord\.com/invite/[^\s]+', re.IGNORECASE)
        urls = url_pattern.findall(base_message)
        placeholder = "___URL_PLACEHOLDER___"
        temp = base_message
        for i, url in enumerate(urls):
            temp = temp.replace(url, f"{placeholder}{i}")
        zws = "\u200B" * random.randint(0, 2)
        variations = ["", "✨", "🔥", "💀", "🎯", "🚀", "💥", "⚡", "🌀", "🔰", "💫", "🌟", "🕹️", "🎮"]
        spacers = ["", " ", "  ", " - ", " | ", " • ", " · ", " ✦ ", " ❯ ", " ═ "]
        suffixes = ["", "", "", " (auto)", " 🔥", " 💀", " 🚀", " ✨", " ٩(◕‿◕)۶"]
        prefix = random.choice(variations) if random.random() < 0.5 else ""
        spacer = random.choice(spacers) if random.random() < 0.3 else ""
        suffix = random.choice(suffixes) if random.random() < 0.3 else ""
        varied = f"{prefix}{spacer}{temp}{suffix}{zws}".strip()
        for i, url in enumerate(urls):
            varied = varied.replace(f"{placeholder}{i}", url)
        return varied

    def send_typing(self, token, channel_id):
        if not use_typing or random.random() > 0.35: return
        try:
            self._request("POST", f"{API_BASE}/channels/{channel_id}/typing", token, headers=self.headers_full(token), timeout=5)
        except: pass

    def is_token_valid(self, token):
        try:
            resp = self._request("GET", f"{API_BASE}/users/@me", token, headers=self.headers_minimal(token), timeout=10)
            return resp.status_code == 200
        except: return False

    def check_membership(self, token, guild_id):
        if not self.is_token_valid(token):
            console.log("Invalid Token", C["red"], f"{token[:15]}...", "invalid")
            return False
        try:
            resp = self._request("GET", f"{API_BASE}/users/@me/guilds", token, headers=self.headers_minimal(token), timeout=10)
            if resp.status_code == 200:
                return any(g["id"] == guild_id for g in resp.json())
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5) + random.uniform(0, 2)
                time.sleep(wait)
                return self.check_membership(token, guild_id)
            else:
                resp2 = self._request("GET", f"{API_BASE}/guilds/{guild_id}/members/@me", token, headers=self.headers_minimal(token), timeout=10)
                return resp2.status_code == 200
        except: return False

    def get_valid_tokens_for_guild(self, guild_id):
        def check(token):
            return token if self.check_membership(token, guild_id) else None
        console.log("Filtering tokens (parallel)...", C["yellow"])
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(self.tokens))) as ex:
            results = list(ex.map(check, self.tokens))
        valid = [r for r in results if r]
        console.log("Filtering Done", C["cyan"], False, f"Valid: {len(valid)}/{len(self.tokens)}")
        return valid

    def get_text_channels(self, token, guild_id, cache_seconds=60):
        cache_key = f"channels_{guild_id}_{token[:10]}"
        if hasattr(self, '_channel_cache') and cache_key in self._channel_cache:
            data, ts = self._channel_cache[cache_key]
            if time.time() - ts < cache_seconds:
                return data
        try:
            resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/channels", token, headers=self.headers_full(token), timeout=10)
            if resp.status_code == 200:
                channels = resp.json()
                text = [c for c in channels if c.get('type') == 0]
                if not hasattr(self, '_channel_cache'): self._channel_cache = {}
                self._channel_cache[cache_key] = (text, time.time())
                return text
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5) + random.uniform(0, 2)
                time.sleep(wait)
                return self.get_text_channels(token, guild_id, cache_seconds)
            return []
        except: return []

    @retry_api
    def send_message(self, token, channel_id, content, poll=None):
        self.send_typing(token, channel_id)
        varied = self.vary_message(content)
        payload = {"content": varied}
        if poll:
            payload["poll"] = {
                "question": {"text": poll["question"]},
                "answers": [{"poll_media": {"text": opt}} for opt in poll["options"]],
                "duration": 24, "allow_multiselect": False
            }
        resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/messages", token, headers=self.headers_full(token), json=payload, timeout=10)
        if resp.status_code == 200:
            return True
        elif resp.status_code in (400, 403):
            console.log("No permission", C["gray"], f"{token[:15]}...", f"Ch {channel_id} ({resp.status_code})")
            return False
        elif resp.status_code == 429:
            wait = resp.json().get('retry_after', 5) + random.uniform(0, 1)
            time.sleep(wait)
            return self.send_message(token, channel_id, content, poll)
        else:
            console.log("Failed", C["red"], f"{token[:15]}...", f"Ch {channel_id} ({resp.status_code})")
            return False

    # ---------- guild_spammer 完全安定版 ----------
    def guild_spammer(self, token, guild_id, message, pings=0, delay=0, poll=None,
                      massping=False, massping_count=0, random_str=False):
        if not self.check_membership(token, guild_id):
            console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild")
            return
        channels = self.get_text_channels(token, guild_id, cache_seconds=0)
        if not channels:
            console.log("Info", C["yellow"], f"{token[:15]}...", "no text channels")
            return
        console.log("Started", C["green"], f"{token[:15]}...", f"{len(channels)} channels")
        active_channels = channels.copy()
        retry_count = 0
        last_refresh = time.time()
        refresh_interval = 120

        while not SHOULD_STOP.is_set():
            try:
                if time.time() - last_refresh > refresh_interval:
                    new_channels = self.get_text_channels(token, guild_id, cache_seconds=0)
                    if new_channels:
                        existing_ids = {c['id'] for c in active_channels}
                        for ch in new_channels:
                            if ch['id'] not in existing_ids:
                                active_channels.append(ch)
                        console.log("Channels refreshed", C["cyan"], f"{token[:15]}...", f"{len(active_channels)} channels")
                    last_refresh = time.time()

                random.shuffle(active_channels)
                for ch in active_channels[:]:
                    if SHOULD_STOP.is_set(): break
                    content = message
                    if pings > 0:
                        content = ("@everyone " * pings) + content
                    if massping and massping_count > 0:
                        members = self.get_random_members(guild_id, massping_count)
                        if members:
                            content += f" {members}"
                    if random_str:
                        content += f" | {get_random_str(10)}"
                    success = self.send_message(token, ch['id'], content, poll)
                    if not success:
                        if ch in active_channels:
                            active_channels.remove(ch)
                        continue
                    retry_count = 0
                    self.human_delay()
                if not active_channels:
                    console.log("Refreshing channels (empty)", C["yellow"], f"{token[:15]}...", "re-fetching")
                    time.sleep(2)
                    new_channels = self.get_text_channels(token, guild_id, cache_seconds=0)
                    if new_channels:
                        active_channels = new_channels.copy()
                        console.log("Channels refreshed", C["green"], f"{token[:15]}...", f"{len(active_channels)} channels")
                        continue
                    else:
                        console.log("Stopped", C["yellow"], f"{token[:15]}...", "no writable channels")
                        return
                if delay > 0:
                    time.sleep(delay + random.uniform(0, 2))
            except requests.exceptions.ConnectionError:
                retry_count += 1
                wait = min(60, retry_count * 5 + random.uniform(0, 2))
                console.log("Network Error", C["red"], f"{token[:15]}...", f"{wait:.1f}s wait ({retry_count})")
                time.sleep(wait)
                if retry_count > 5:
                    console.log("Giving up", C["red"], f"{token[:15]}...", "too many errors")
                    return
            except Exception as e:
                console.log("Unexpected Error", C["red"], f"{token[:15]}...", str(e))
                time.sleep(5)
                try:
                    new_channels = self.get_text_channels(token, guild_id, cache_seconds=0)
                    if new_channels:
                        active_channels = new_channels.copy()
                    else:
                        return
                except:
                    return

    # ---------- spammer 単一チャンネル安定版 ----------
    def spammer(self, token, channel_id, message, guild=None, massping=False, pings=None,
                random_str=False, delay=None, poll=None):
        if massping and guild and not self.check_membership(token, guild):
            console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild for massping")
            return
        last_refresh = time.time()
        refresh_interval = 90

        while not SHOULD_STOP.is_set():
            try:
                if time.time() - last_refresh > refresh_interval:
                    try:
                        self._request("GET", f"{API_BASE}/channels/{channel_id}",
                                      token, headers=self.headers_minimal(token), timeout=5)
                    except:
                        console.log("Channel gone", C["red"], f"{token[:15]}...", "channel deleted")
                        return
                    last_refresh = time.time()

                content = message
                if massping and pings:
                    members = self.get_random_members(guild, pings)
                    if members:
                        content += f" {members}"
                if random_str:
                    content += f" | {get_random_str(10)}"
                success = self.send_message(token, channel_id, content, poll)
                if not success:
                    console.log("Stopped", C["yellow"], f"{token[:15]}...", "no permission")
                    return
                if delay:
                    time.sleep(delay + random.uniform(0, 1))
                else:
                    self.human_delay()
            except requests.exceptions.ConnectionError:
                console.log("Connection lost", C["red"], f"{token[:15]}...", "retry in 5s")
                time.sleep(5)
            except Exception as e:
                console.log("Spammer Error", C["red"], f"{token[:15]}...", str(e))
                time.sleep(3)

    # ---------- メンバーキャッシュ ----------
    def get_random_members(self, guild_id, count):
        now = time.time()
        if guild_id in self.cache_timestamps and now - self.cache_timestamps[guild_id] < cache_ttl:
            pass
        else:
            try:
                path = f"scraped/{guild_id}.json"
                if os.path.exists(path):
                    with open(path, "r") as f:
                        self.cached_members[guild_id] = json.loads(f.read())
                        self.cache_timestamps[guild_id] = now
                else:
                    return ""
            except: return ""
        members = self.cached_members.get(guild_id, [])
        if not members: return ""
        selected = random.sample(members, min(count, len(members)))
        return " ".join(f"<@!{uid}>" for uid in selected)

    # ---------- メンバースクレイプ ----------
    def member_scrape(self, guild_id, channel_id):
        try:
            if not channel_id:
                for token in self.tokens:
                    resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/channels", token, headers=self.headers_full(token), timeout=5)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text = [c for c in channels if c.get('type') == 0]
                        if text: channel_id = text[0]['id']; break
                    self.human_delay()
                if not channel_id:
                    console.log("Failed", C["red"], "No text channel found")
                    return
            valid = self.get_valid_tokens_for_guild(guild_id)
            if not valid:
                console.log("Failed", C["red"], "No valid token")
                return
            if not os.path.exists(f"scraped/{guild_id}.json"):
                members = DiscordSocket(random.choice(valid), guild_id, channel_id).run()
                with open(f"scraped/{guild_id}.json", "w") as f:
                    json.dump(list(members.keys()), f, indent=2)
                console.log("Scraped", C["green"], False, f"{len(members)} members saved")
        except Exception as e:
            console.log("Failed", C["red"], False, f"member_scrape: {e}")

    # ---------- スケジュールスパム ----------
    def schedule_spam(self, guild_id, channel_id, message, schedule_time, tokens_list,
                      pings=0, delay=0, massping=False, massping_count=0, random_str=False, poll=None):
        try:
            now = datetime.now()
            target = datetime.strptime(schedule_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if target < now: target += timedelta(days=1)
            wait = (target - now).total_seconds()
            console.log("Schedule", C["yellow"], False, f"Start at {target.strftime('%H:%M')} (in {wait:.0f}s)")
            time.sleep(wait)
            console.log("Schedule", C["green"], False, "Starting scheduled spam!")
            for token in tokens_list:
                threading.Thread(target=self.guild_spammer, args=(token, guild_id, message, pings, delay, poll, massping, massping_count, random_str), daemon=True).start()
        except Exception as e:
            console.log("Schedule Error", C["red"], False, str(e))

    def repeat_schedule_spam(self, guild_id, channel_id, message, schedule_time, interval_minutes, tokens_list,
                             pings=0, delay=0, massping=False, massping_count=0, random_str=False, poll=None, max_runs=0):
        def loop():
            runs = 0
            while not SHOULD_STOP.is_set() and (max_runs == 0 or runs < max_runs):
                try:
                    now = datetime.now()
                    target = datetime.strptime(schedule_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                    if target < now: target += timedelta(days=1)
                    wait = (target - now).total_seconds()
                    console.log("Repeat Schedule", C["yellow"], False, f"Next at {target.strftime('%H:%M')} (in {wait:.0f}s)")
                    time.sleep(wait)
                    console.log("Repeat Schedule", C["green"], False, f"Starting run {runs+1}")
                    for token in tokens_list:
                        threading.Thread(target=self.guild_spammer, args=(token, guild_id, message, pings, delay, poll, massping, massping_count, random_str), daemon=True).start()
                    runs += 1
                    if max_runs == 0 or runs < max_runs:
                        time.sleep(interval_minutes * 60)
                except Exception as e:
                    console.log("Repeat Schedule Error", C["red"], False, str(e))
                    time.sleep(60)
        threading.Thread(target=loop, daemon=True).start()

    # ---------- ステータスマネージャー ----------
    def status_manager(self):
        if self.status_thread_running: return
        def rotate():
            while not SHOULD_STOP.is_set():
                try:
                    status = random.choice(custom_statuses)
                    for token in self.tokens:
                        try:
                            ws = ws_pool.get_connection(token)
                            if ws:
                                ws.send(json.dumps({
                                    "op": 2,
                                    "d": {
                                        "token": token,
                                        "properties": {"os": "Windows", "browser": "Discord"},
                                        "presence": {
                                            "status": random.choice(['online', 'idle', 'dnd']),
                                            "since": 0,
                                            "activities": [{"name": status, "type": 0}],
                                            "afk": False
                                        }
                                    }
                                }))
                                console.log("Status", C["green"], f"{token[:15]}...", status)
                                time.sleep(0.3)
                        except: pass
                except: pass
                time.sleep(status_interval)
        threading.Thread(target=rotate, daemon=True).start()
        self.status_thread_running = True

    # ---------- 高度リアクション ----------
    def advanced_reaction(self, channel_id, target_type, target_value, emoji):
        try:
            if target_type == "message_id":
                def react(tok):
                    try:
                        self._request("PUT", f"{API_BASE}/channels/{channel_id}/messages/{target_value}/reactions/{emoji}/@me", tok, headers=self.headers_full(tok), timeout=10)
                        console.log("Reacted", C["green"], f"{tok[:15]}...", emoji)
                    except: pass
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(self.tokens))) as ex:
                    ex.map(react, self.tokens)
                return
            resp = self._request("GET", f"{API_BASE}/channels/{channel_id}/messages", token=self.tokens[0], headers=self.headers_full(self.tokens[0]), params={"limit": 50}, timeout=10)
            if resp.status_code != 200: return
            msgs = resp.json()
            target_msg = None
            if target_type == "user":
                for m in msgs:
                    if m["author"]["id"] == target_value: target_msg = m; break
            elif target_type == "keyword":
                for m in msgs:
                    if target_value.lower() in m.get("content", "").lower(): target_msg = m; break
            if not target_msg: return
            msg_id = target_msg["id"]
            def react(tok):
                try:
                    self._request("PUT", f"{API_BASE}/channels/{channel_id}/messages/{msg_id}/reactions/{emoji}/@me", tok, headers=self.headers_full(tok), timeout=10)
                    console.log("Reacted", C["green"], f"{tok[:15]}...", emoji)
                except: pass
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(self.tokens))) as ex:
                ex.map(react, self.tokens)
        except Exception as e:
            console.log("Adv Reaction Error", C["red"], False, str(e))

    def clear_cache(self):
        self.cached_members.clear(); self.cache_timestamps.clear()
        if hasattr(self, '_channel_cache'): self._channel_cache.clear()
        console.log("Cache Cleared", C["green"])

    # ---------- Joiner ----------
    def joiner(self, invite):
        try:
            params = {"inputValue": f"https://discord.gg/{invite}", "with_counts": "true", "with_expiration": "true", "with_permissions": "true"}
            invite_info = None
            for token in self.tokens:
                resp = self._request("GET", f"{API_BASE}/invites/{invite}", token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code == 200:
                    invite_info = resp.json(); break
                elif resp.status_code == 404:
                    console.log("Failed", C["red"], "Invalid invite"); input(); Menu().main_menu(); return
                self.human_delay()
            if not invite_info:
                console.log("Failed", C["red"], "No invite info"); input(); Menu().main_menu(); return
            guild_id = invite_info["guild"]["id"]
            join = {"location": "Join Guild", "location_guild_id": guild_id,
                    "location_channel_id": invite_info["channel"]["id"],
                    "location_channel_type": invite_info["channel"]["type"]}
            context = base64.b64encode(json.dumps(join).encode()).decode()
            def join_server(token):
                try:
                    self.human_delay()
                    headers = self.headers_full(token)
                    headers["X-Context-Properties"] = context
                    payload = {"session_id": uuid.uuid4().hex}
                    resp = self._request("POST", f"{API_BASE}/invites/{invite}", token, headers=headers, json=payload, timeout=10)
                    if resp.status_code == 200:
                        console.log("Joined", C["green"], f"{token[:25]}...", invite_info["guild"]["name"])
                    elif resp.status_code == 400:
                        console.log("Captcha", C["yellow"], f"{token[:25]}...", "skipping this token")
                    elif resp.status_code == 429:
                        wait = resp.json().get('retry_after', 30) + random.uniform(0, 10)
                        console.log("RateLimit", C["magenta"], f"{token[:25]}...", f"wait {wait:.1f}s")
                        time.sleep(wait)
                        retry = self._request("POST", f"{API_BASE}/invites/{invite}", token, headers=headers, json=payload, timeout=10)
                        if retry.status_code == 200:
                            console.log("Joined (retry)", C["green"], f"{token[:25]}...", invite_info["guild"]["name"])
                    else:
                        console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message", "unknown"))
                except: pass
            args = [(tok,) for tok in self.tokens]
            Menu().run(join_server, args)
        except Exception as e:
            console.log("Failed", C["red"], "Joiner error", e); input(); Menu().main_menu()

    # ---------- Leaver ----------
    def leaver(self, token, guild):
        try:
            resp = self._request("DELETE", f"{API_BASE}/users/@me/guilds/{guild}", token, headers=self.headers_full(token), json={"lurking": False}, timeout=10)
            if resp.status_code == 204:
                console.log("Left", C["green"], f"{token[:25]}...", guild)
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5); time.sleep(wait); self.leaver(token, guild)
            else:
                console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
        except: pass

    # ---------- keep_online ----------
    def keep_online(self, token):
        while not SHOULD_STOP.is_set():
            try:
                ws = ws_pool.get_connection(token)
                if not ws:
                    time.sleep(random.uniform(3, 8)); continue
                console.log("Online", C["green"], f"{token[:15]}...", "connected")
                last_ping = time.time()
                while not SHOULD_STOP.is_set():
                    try:
                        if time.time() - last_ping > 30:
                            ws.send(json.dumps({"op": 1, "d": None})); last_ping = time.time()
                        ws.settimeout(5)
                        try:
                            _ = ws.recv()
                        except websocket.WebSocketTimeoutException:
                            pass
                        except Exception:
                            break
                    except Exception:
                        break
                console.log("Reconnecting", C["yellow"], f"{token[:15]}...", "disconnected")
                time.sleep(random.uniform(2, 6))
            except Exception as e:
                console.log("Fatal", C["red"], f"{token[:15]}...", str(e)); time.sleep(10)

    # ---------- Voice 関連（完全ボイス維持） ----------
    def join_voice_channel(self, token, guild_id, channel_id):
        if token in self._voice_connections:
            self._voice_connections[token].stop()
            del self._voice_connections[token]
        vc = VoiceConnection(token, guild_id, channel_id)
        vc.start()
        self._voice_connections[token] = vc
        console.log("Voice Joined", C["green"], f"{token[:15]}...", f"channel {channel_id}")

    def leave_voice_channel(self, token):
        if token in self._voice_connections:
            self._voice_connections[token].stop()
            del self._voice_connections[token]
            console.log("Voice Left", C["yellow"], f"{token[:15]}...", "exited")

    def voice_spammer(self, token, ws, guild_id, channel_id, close=None):
        try:
            self.onliner_legacy(token, ws)
            ws.send(json.dumps({
                "op": 4,
                "d": {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "self_mute": False,
                    "self_deaf": False,
                    "self_stream": False,
                    "self_video": True,
                },
            }))
            ws.send(json.dumps({
                "op": 18,
                "d": {
                    "type": "guild",
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "preferred_region": "singapore",
                },
            }))
            ws.send(json.dumps({"op": 1, "d": None}))
            if close:
                ws.close()
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def vc_joiner(self, token, guild, channel, ws):
        try:
            for _ in range(1):
                ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
                ws.send(json.dumps({
                    "op": 2,
                    "d": {
                        "token": token,
                        "properties": {"os": "windows", "browser": "Discord", "device": "desktop"}
                    }
                }))
                ws.send(json.dumps({
                    "op": 4,
                    "d": {
                        "guild_id": guild,
                        "channel_id": channel,
                        "self_mute": random.choice([True, False]),
                        "self_deaf": False
                    }
                }))
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def onliner_legacy(self, token, ws):
        try:
            ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
            ws.send(json.dumps({
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {"os": "Windows"},
                    "presence": {
                        "game": {"name": "Masumani", "type": 0},
                        "status": random.choice(['online', 'dnd', 'idle']),
                        "since": 0,
                        "afk": False
                    }
                },
            }))
            console.log("Onlined", C[color], f"{token[:25]}...")
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def soundbord(self, token, channel):
        try:
            sounds = self._request("GET", f"{API_BASE}/soundboard-default-sounds", token, headers=self.headers_full(token), timeout=10).json()
            self.human_delay()
            while True:
                sound = random.choice(sounds)
                payload = {"emoji_id": None, "emoji_name": sound["emoji_name"], "sound_id": sound["sound_id"]}
                resp = self._request("POST", f"{API_BASE}/channels/{channel}/send-soundboard-sound", token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 204:
                    console.log("Success", C["green"], f"{token[:25]}...", f"Played {sound['name']}")
                elif resp.status_code == 429:
                    retry_after = resp.json()["retry_after"]
                    console.log("Ratelimit", C["yellow"], f"{token[:25]}...", f"Ratelimit Exceeded - {retry_after:.2f}s")
                    time.sleep(float(retry_after))
                else:
                    break
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def open_dm(self, token, user_id):
        try:
            payload = {"recipients": [f'{user_id}']}
            resp = self._request("POST", f"{API_BASE}/users/@me/channels", token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json()["id"]
            else:
                console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                return None
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)
            return None

    def call_spammer(self, token, user_id):
        try:
            while True:
                channel_id = self.open_dm(token, user_id)
                if not channel_id:
                    return
                json_data = {'recipients': None}
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/call", token, headers=self.headers_full(token), json=json_data, timeout=10)
                if resp.status_code == 200:
                    console.log("Called", C["green"], f"{token[:25]}...", user_id)
                    ws = websocket.WebSocket()
                    self.voice_spammer(token, ws, channel_id, channel_id, True)
                else:
                    console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                    return
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def dm_spammer(self, token, user_id, message):
        try:
            channel_id = self.open_dm(token, user_id)
            if not channel_id:
                return
            while True:
                payload = {"content": message, "nonce": str(self.nonce())}
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/messages", token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 200:
                    console.log("Send", C["green"], f"{token[:25]}...", user_id)
                else:
                    console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                    break
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def format_tokens(self):
        try:
            formatted = []
            for token in self.tokens:
                token = token.strip()
                if token:
                    parts = token.split(":")
                    if len(parts) >= 3:
                        formatted.append(parts[2])
                    else:
                        formatted.append(token)
            console.log("Success", C["green"], f"Formatted {len(formatted)} tokens")
            with open("data/tokens.txt", "w") as f:
                for token in formatted:
                    f.write(f"{token}\n")
            Menu().main_menu()
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def bio_changer(self, token, bio):
        try:
            payload = {"bio": bio}
            resp = self._request("PATCH", f"{API_BASE}/users/@me/profile", token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 200:
                console.log("Changed", C["green"], f"{token[:25]}...", bio)
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5); time.sleep(wait); self.bio_changer(token, bio)
            else:
                console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def mass_nick(self, token, guild, nick):
        try:
            payload = {"nick": nick}
            resp = self._request("PATCH", f"{API_BASE}/guilds/{guild}/members/@me", token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 200:
                console.log("Success", C["green"], f"{token[:25]}...")
            else:
                console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def thread_spammer(self, token, channel_id, name):
        try:
            payload = {"name": name, "type": 11, "auto_archive_duration": 4320, "location": "Thread Browser Toolbar"}
            while True:
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/threads", token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 201:
                    console.log("Created", C["green"], f"{token[:25]}...", name)
                elif resp.status_code == 429:
                    retry_after = resp.json()["retry_after"]
                    if int(retry_after) > 10:
                        console.log("Stopped", C["magenta"], token[:25], f"Ratelimit Exceeded - {int(round(retry_after))}s")
                        break
                    else:
                        console.log("Ratelimit", C["yellow"], f"{token[:25]}...", f"Ratelimit Exceeded - {retry_after:.2f}s")
                        time.sleep(float(retry_after))
                else:
                    console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                    break
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def typier(self, token, channel_id):
        try:
            while True:
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/typing", token, headers=self.headers_full(token), timeout=10)
                if resp.status_code == 204:
                    console.log("Success", C["green"], f"{token[:25]}...")
                    time.sleep(9)
                else:
                    console.log("Failed", C["red"], f"{token[:25]}...")
                    break
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def friender(self, token, nickname):
        try:
            payload = {"username": nickname, "discriminator": None}
            resp = self._request("POST", f"{API_BASE}/users/@me/relationships", token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 204:
                console.log("Success", C["green"], f"{token[:25]}...")
            elif resp.status_code == 400:
                console.log("Captcha", C["yellow"], f"{token[:25]}...")
            else:
                console.log("Failed", C["red"], f"{token[:25]}...", resp.json())
        except Exception as e:
            console.log("Failed", C["red"], f"{token[:25]}...", e)

    def guild_checker(self, guild_id):
        def main_checker(token):
            try:
                while True:
                    resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}", token, headers=self.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        console.log("Found", C["green"], f"{token[:25]}...", guild_id)
                        break
                    elif resp.status_code == 429:
                        retry_after = resp.json()["retry_after"]
                        console.log("Ratelimit", C["yellow"], f"{token[:25]}...", f"Ratelimit Exceeded - {retry_after:.2f}s")
                        time.sleep(float(retry_after))
                    else:
                        console.log("Not Found", C["red"], f"{token[:25]}...", guild_id)
                        break
            except Exception as e:
                console.log("Failed", C["red"], f"{token[:25]}...", e)
        args = [(token,) for token in self.tokens]
        Menu().run(main_checker, args)

    def token_checker(self):
        valid = []
        def main(token):
            try:
                while True:
                    resp = self._request("GET", f"{API_BASE}/users/@me/library", token, headers=self.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        console.log("Valid", C["green"], f"{token[:25]}...")
                        valid.append(token)
                        break
                    elif resp.status_code == 403:
                        console.log("Locked", C["yellow"], f"{token[:25]}...")
                        break
                    elif resp.status_code == 429:
                        retry_after = resp.json()["retry_after"]
                        console.log("Ratelimit", C["pink"], f"{token[:25]}...", f"{retry_after}s")
                        time.sleep(retry_after)
                    else:
                        console.log("Invalid", C["red"], f"{token[:25]}...", resp.json().get("message"))
                        break
            except Exception as e:
                console.log("Failed", C["red"], f"{token[:25]}...", e)
        with open("data/tokens.txt", "r") as f:
            tokens = list({line.strip().replace('"', '') for line in f if line.strip()})
        args = [(token,) for token in tokens]
        Menu().run(main, args)
        with open("data/tokens.txt", "w") as f:
            f.write("\n".join(valid))

    def accept_rules(self, guild_id):
        try:
            valid = []
            for token in self.tokens:
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/member-verification", token, headers=self.headers_full(token), timeout=10)
                if resp.status_code == 200:
                    valid.append(token)
                    payload = resp.json()
                    break
            if not valid:
                console.log("Failed", C["red"], "All tokens are Invalid")
                input()
                Menu().main_menu()
                return
            def run_main(token):
                try:
                    resp = self._request("PUT", f"{API_BASE}/guilds/{guild_id}/requests/@me", token, headers=self.headers_full(token), json=payload, timeout=10)
                    if resp.status_code == 201:
                        console.log("Accepted", C["green"], f"{token[:25]}...", guild_id)
                    else:
                        console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{token[:25]}...", e)
            args = [(token,) for token in self.tokens]
            Menu().run(run_main, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Accept Rules", e)

    def onboard_bypass(self, guild_id):
        try:
            master_token = None
            for token in self.tokens:
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/onboarding", token, headers=self.headers_full(token), timeout=10)
                if resp.status_code == 200:
                    onboarding_data = resp.json()
                    master_token = token
                    break
            if not master_token:
                console.log("Failed", C["red"], "No tokens have access to this guild's onboarding.")
                return
            responses = []
            prompts_seen = {}
            options_seen = {}
            prompts = onboarding_data.get("prompts", [])
            if not prompts:
                console.log("Info", C["gray"], "Guild has no onboarding prompts.")
                return
            for prompt in prompts:
                p_id = prompt["id"]
                available_options = prompt.get("options", [])
                if not available_options: continue
                selected_option = random.choice(available_options)["id"]
                responses.append(selected_option)
                fake_time = int(time.time()) - random.randint(5, 15)
                prompts_seen[p_id] = fake_time
                for opt in available_options:
                    options_seen[opt["id"]] = fake_time
            def run_task(token):
                token_time = int(time.time()) - random.randint(1, 10)
                t_prompts_seen = {k: token_time for k in prompts_seen}
                t_options_seen = {k: token_time for k in options_seen}
                payload = {
                    "onboarding_responses": responses,
                    "onboarding_prompts_seen": t_prompts_seen,
                    "onboarding_responses_seen": t_options_seen,
                }
                resp = self._request("POST", f"{API_BASE}/guilds/{guild_id}/onboarding-responses", token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 200:
                    console.log("Accepted", C["green"], f"{token[:25]}...")
                else:
                    console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
            args = [(token,) for token in self.tokens]
            Menu().run(run_task, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Pass Onboard", e)
            input()
            Menu().main_menu()

    def reactor_main(self, channel_id, message_id):
        try:
            access_token = None
            emojis = []
            params = {"around": message_id, "limit": 50}
            for token in self.tokens:
                resp = self._request("GET", f"{API_BASE}/channels/{channel_id}/messages", token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code == 200:
                    access_token = token
                    break
            if not access_token:
                console.log("Failed", C["red"], "Missing Permissions")
                input()
                Menu().main_menu()
                return
            data = resp.json()
            for msg in data:
                if msg["id"] == message_id:
                    reactions = msg.get("reactions", [])
                    for emois in reactions:
                        if emois:
                            emoji_id = emois["emoji"]["id"]
                            emoji_name = emois["emoji"]["name"]
                            if emoji_id is None:
                                emojis.append(emoji_name)
                            else:
                                emojis.append(f"{emoji_name}:{emoji_id}")
                    break
            if not emojis:
                console.log("Failed", C["red"], "No reactions Found in this message")
                input()
                Menu().main_menu()
                return
            for i, emoji in enumerate(emojis, start=1):
                print(f"{C[color]}0{i}:{C['white']} {emoji}")
            choice = input(f"\n{console.prompt('Choice')}")
            if choice.startswith('0') and len(choice) == 2:
                choice = str(int(choice))
            selected = emojis[int(choice) - 1]
            def add_reaction(token):
                try:
                    url = f"{API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{selected}/@me"
                    resp = self._request("PUT", url, token, headers=self.headers_full(token), timeout=10)
                    if resp.status_code == 204:
                        console.log("Reacted", C["green"], f"{token[:25]}...", selected)
                    else:
                        console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{token[:25]}...", e)
            args = [(token,) for token in self.tokens]
            Menu().run(add_reaction, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get emojis", e)
            input()
            Menu().main_menu()

    def button_bypass(self, channel_id, message_id, guild_id):
        try:
            access_token = None
            buttons = []
            params = {"around": message_id, "limit": 50}
            for token in self.tokens:
                resp = self._request("GET", f"{API_BASE}/channels/{channel_id}/messages", token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code == 200:
                    access_token = token
                    break
            if not access_token:
                console.log("Failed", C["red"], "Missing Permissions")
                input()
                Menu().main_menu()
                return
            message = next((m for m in resp.json() if m["id"] == message_id), None)
            if not message:
                console.log("Failed", C["red"], "Message not found")
                input()
                Menu().main_menu()
                return
            for row in message.get("components", []):
                for comp in row.get("components", []):
                    if comp.get("type") == 2:
                        label = comp.get("label", "No Label")
                        custom_id = comp["custom_id"]
                        buttons.append({"label": label, "custom_id": custom_id})
            if not buttons:
                console.log("Failed", C["red"], "No buttons found in this message")
                input()
                Menu().main_menu()
                return
            for i, btn in enumerate(buttons, start=1):
                print(f"{C[color]}0{i}:{C['white']} {btn['label']}")
            choice = input(f"\n{console.prompt('Choice')}")
            if choice.startswith('0') and len(choice) == 2:
                choice = str(int(choice))
            btn = buttons[int(choice) - 1]
            custom_id = btn["custom_id"]
            def click_button(token):
                try:
                    payload = {
                        "application_id": message["author"]["id"],
                        "channel_id": channel_id,
                        "data": {"component_type": 2, "custom_id": custom_id},
                        "guild_id": guild_id,
                        "message_flags": 0,
                        "message_id": message_id,
                        "nonce": str(self.nonce()),
                        "session_id": uuid.uuid4().hex,
                        "type": 3,
                    }
                    resp = self._request("POST", f"{API_BASE}/interactions", token, headers=self.headers_full(token), json=payload, timeout=10)
                    if resp.status_code == 204:
                        console.log("Clicked", C["green"], f"{token[:25]}...", btn["label"])
                    else:
                        console.log("Failed", C["red"], f"{token[:25]}...", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{token[:25]}...", e)
            args = [(token,) for token in self.tokens]
            Menu().run(click_button, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get buttons", e)
            input()
            Menu().main_menu()

    def clear_activity(self):
        for token in self.tokens:
            try:
                ws = ws_pool.get_connection(token)
                if ws:
                    ws.send(json.dumps({
                        "op": 2,
                        "d": {
                            "token": token,
                            "properties": {"os": "Windows", "browser": "Discord"},
                            "presence": {"status": "online", "since": 0, "activities": [], "afk": False}
                        }
                    }))
                self._request("PATCH", f"{API_BASE}/users/@me/settings", token, headers=self.headers_full(token), json={"custom_status": None}, timeout=10)
                console.log("Cleared", C["green"], f"{token[:25]}...")
            except Exception as e:
                console.log("Failed", C["red"], f"{token[:25]}...", e)
            self.human_delay()

    def mass_timeout(self, token, guild_id, days=28):
        try:
            members = []
            after = None
            while True:
                params = {"limit": 1000}
                if after:
                    params["after"] = after
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/members", token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code != 200:
                    console.log("Failed", C["red"], f"{token[:25]}...", f"メンバー取得失敗 ({resp.status_code})")
                    return
                data = resp.json()
                if not data: break
                members.extend(data)
                after = data[-1]["user"]["id"]
                if len(data) < 1000: break
            if not members:
                console.log("Info", C["yellow"], f"{token[:25]}...", "メンバーがいません")
                return
            console.log("Info", C["yellow"], f"{token[:25]}...", f"{len(members)}人のメンバーをタイムアウト (最大{days}日)")
            timeout_until = (datetime.now() + timedelta(days=days)).isoformat()
            def timeout_member(member):
                user_id = member["user"]["id"]
                try:
                    r = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}", token, headers=self.headers_full(token), json={"communication_disabled_until": timeout_until}, timeout=10)
                    if r.status_code == 200:
                        console.log("Timeout", C["green"], f"{token[:25]}...", f"@{member['user']['username']}")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        console.log("Ratelimit", C["yellow"], f"{token[:25]}...", f"wait {retry_after:.2f}s")
                        time.sleep(retry_after)
                        r2 = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}", token, headers=self.headers_full(token), json={"communication_disabled_until": timeout_until}, timeout=10)
                        if r2.status_code == 200:
                            console.log("Timeout", C["green"], f"{token[:25]}...", f"@{member['user']['username']} (retry)")
                        else:
                            console.log("Failed", C["red"], f"{token[:25]}...", f"@{member['user']['username']} ({r2.status_code})")
                    else:
                        console.log("Failed", C["red"], f"{token[:25]}...", f"@{member['user']['username']} ({r.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], f"{token[:25]}...", f"@{member['user']['username']}: {e}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, 10)) as executor:
                executor.map(timeout_member, members)
            console.log("Done", C["green"], f"{token[:25]}...", f"{len(members)}人処理完了")
        except Exception as e:
            console.log("Error", C["red"], f"{token[:25]}...", e)

    def mass_nick_all(self, token, guild_id, new_nick):
        try:
            members = []
            after = None
            while True:
                params = {"limit": 1000}
                if after:
                    params["after"] = after
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/members", token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code != 200:
                    console.log("Failed", C["red"], f"{token[:25]}...", f"メンバー取得失敗 ({resp.status_code})")
                    return
                data = resp.json()
                if not data: break
                members.extend(data)
                after = data[-1]["user"]["id"]
                if len(data) < 1000: break
            if not members:
                console.log("Info", C["yellow"], f"{token[:25]}...", "メンバーがいません")
                return
            console.log("Info", C["yellow"], f"{token[:25]}...", f"{len(members)}人のニックネームを '{new_nick}' に変更")
            def change_nick(member):
                user_id = member["user"]["id"]
                try:
                    r = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}", token, headers=self.headers_full(token), json={"nick": new_nick}, timeout=10)
                    if r.status_code == 200:
                        console.log("Changed", C["green"], f"{token[:25]}...", f"@{member['user']['username']} -> {new_nick}")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        console.log("Ratelimit", C["yellow"], f"{token[:25]}...", f"wait {retry_after:.2f}s")
                        time.sleep(retry_after)
                        r2 = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}", token, headers=self.headers_full(token), json={"nick": new_nick}, timeout=10)
                        if r2.status_code == 200:
                            console.log("Changed", C["green"], f"{token[:25]}...", f"@{member['user']['username']} -> {new_nick} (retry)")
                        else:
                            console.log("Failed", C["red"], f"{token[:25]}...", f"@{member['user']['username']} ({r2.status_code})")
                    else:
                        console.log("Failed", C["red"], f"{token[:25]}...", f"@{member['user']['username']} ({r.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], f"{token[:25]}...", f"@{member['user']['username']}: {e}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, 10)) as executor:
                executor.map(change_nick, members)
            console.log("Done", C["green"], f"{token[:25]}...", f"{len(members)}人変更完了")
        except Exception as e:
            console.log("Error", C["red"], f"{token[:25]}...", e)

    def token_quality_check(self):
        console.clear(); console.render_ascii()
        console.title("Masumani - Token Quality Check")
        console.log("Checking", C["yellow"], False, "Token quality analysis...")
        results = []
        for token in self.tokens:
            try:
                resp = self._request("GET", f"{API_BASE}/users/@me", token, headers=self.headers_minimal(token), timeout=10)
                if resp.status_code == 200:
                    user = resp.json()
                    guild_resp = self._request("GET", f"{API_BASE}/users/@me/guilds", token, headers=self.headers_minimal(token), timeout=10)
                    guild_count = len(guild_resp.json()) if guild_resp.status_code == 200 else 0
                    lib_resp = self._request("GET", f"{API_BASE}/users/@me/library", token, headers=self.headers_minimal(token), timeout=10)
                    locked = (lib_resp.status_code == 403)
                    results.append({
                        "token": token[:25] + "...",
                        "username": user.get("username", "Unknown"),
                        "verified": user.get("verified", False),
                        "email": user.get("email", "None"),
                        "guilds": guild_count,
                        "locked": locked,
                        "status": "Valid"
                    })
                elif resp.status_code == 401:
                    results.append({"token": token[:25] + "...", "status": "Invalid (401)"})
                elif resp.status_code == 403:
                    results.append({"token": token[:25] + "...", "status": "Locked (403)"})
                else:
                    results.append({"token": token[:25] + "...", "status": f"Unknown ({resp.status_code})"})
                self.human_delay()
            except Exception as e:
                results.append({"token": token[:25] + "...", "status": f"Error: {e}"})
        console.clear(); console.render_ascii()
        print(f"\n{C['cyan']}【 Token Quality Report 】{C['white']}\n")
        for res in results:
            if "Valid" in res.get("status", ""):
                status_color = C["green"]
                extra = f" | @{res.get('username','')} | Verified:{res.get('verified',False)} | Guilds:{res.get('guilds',0)} | Locked:{res.get('locked',False)}"
            elif "Invalid" in res.get("status", ""):
                status_color = C["red"]; extra = ""
            elif "Locked" in res.get("status", ""):
                status_color = C["yellow"]; extra = ""
            else:
                status_color = C["gray"]; extra = ""
            console.log(res["status"], status_color, res["token"], extra)
        input(f"\n   {console.background}~/> press enter to continue ")
        Menu().main_menu()

    # ---------- クリーンアップ用 ----------
    def cleanup_voice(self):
        for token in list(self._voice_connections.keys()):
            self.leave_voice_channel(token)

# ---------- Menu クラス ----------
class Menu:
    def __init__(self):
        global global_raider
        if global_raider is None:
            self.raider = Raider()
            global_raider = self.raider
        else:
            self.raider = global_raider
        self.background = C[color] if color in C else C["light_blue"]
        self.options = {
            "1": self.joiner, "2": self.leaver, "3": self.spammer, "4": self.checker,
            "5": self.reactor, "6": self.clear_status, "7": self.formatter, "8": self.button,
            "9": self.accept, "10": self.guild, "11": self.friender, "13": self.onliner,
            "14": self.soundbord, "15": self.nick_changer, "16": self.Thread_Spammer,
            "17": self.typier, "19": self.caller, "20": self.bio_changer, "21": self.voice_joiner,
            "22": self.onboard, "23": self.dm_spam, "24": self.exits, "25": self.poll_spammer,
            "26": self.mass_timeout, "27": self.mass_nick_all, "28": self.schedule_spam,
            "32": self.token_quality, "33": self.status_manager, "34": self.advanced_reaction,
            "35": self.repeat_schedule, "36": self.cache_clear,
            "h": self.show_help, "H": self.show_help, "~": self.credit,
        }

    def main_menu(self):
        console.run()
        choice = input(f"{' '*6}{self.background}-> {Fore.RESET}")
        if choice.startswith('0') and len(choice)==2: choice = str(int(choice))
        if choice.lower() in self.options:
            console.render_ascii(); self.options[choice.lower()]()
        else: self.main_menu()

    def run(self, func, args):
        threads = []
        console.clear(); console.render_ascii()
        for idx, arg in enumerate(args):
            t = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(t); t.start()
            if idx % 5 == 0: time.sleep(0.1)
        for t in threads: t.join()
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    def run_spammer(self, func, args):
        SHOULD_STOP.clear()
        console.clear(); console.render_ascii()
        if not args:
            console.log("Error", C["red"], False, "No threads"); input(); self.main_menu(); return
        def listener():
            while not SHOULD_STOP.is_set():
                try:
                    if sys.stdin.isatty():
                        line = sys.stdin.readline()
                        if line and line.strip().lower() == "end":
                            console.log("Stopping", C["red"], False, "end command received")
                            SHOULD_STOP.set(); break
                    else:
                        import select
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            line = sys.stdin.readline()
                            if line and line.strip().lower() == "end":
                                console.log("Stopping", C["red"], False, "end command received")
                                SHOULD_STOP.set(); break
                        time.sleep(0.1)
                except: time.sleep(0.5)
        threading.Thread(target=listener, daemon=True).start()
        threads = []
        for idx, arg in enumerate(args):
            t = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(t); t.start()
            if idx % 5 == 0: time.sleep(0.1)
        while any(t.is_alive() for t in threads) and not SHOULD_STOP.is_set():
            time.sleep(0.3)
        SHOULD_STOP.set()
        time.sleep(0.5)
        for t in threads:
            if t.is_alive(): t.join(timeout=0.1)
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    # ---------- 各メニュー項目 ----------
    @wrapper
    def joiner(self):
        invite = input(console.prompt("Invite")).strip()
        if not invite: self.main_menu()
        invite = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
        self.raider.joiner(invite)

    @wrapper
    def leaver(self):
        guild = input(console.prompt("Guild ID")).strip()
        if not guild: self.main_menu()
        self.run(self.raider.leaver, [(tok, guild) for tok in self.raider.tokens])

    @wrapper
    def spammer(self):
        console.title("Masumani - Spammer")
        console.log("Info", C["yellow"], False, "事前に [04] Token Checker を推奨。")
        msg_dir = "data/messages"
        if not os.path.exists(msg_dir): os.makedirs(msg_dir)
        files = [f for f in os.listdir(msg_dir) if f.endswith('.txt')]
        if files:
            print(f"{C['cyan']}保存済みメッセージ:{C['white']}")
            for idx, fname in enumerate(files, 1):
                print(f"  {idx}: {fname}")
            print("  0: 新規入力")
            choice = input(console.prompt("選択 (番号)"))
            if choice.isdigit() and int(choice) > 0 and int(choice) <= len(files):
                selected = files[int(choice)-1]
                with open(os.path.join(msg_dir, selected), 'r', encoding='utf-8') as f:
                    message = f.read().strip()
                console.log("Loaded", C["green"], False, f"'{selected}' を読み込み")
            else:
                message = input(console.prompt("メッセージ (空でキャンセル)"))
                if message == "": self.main_menu()
                save = input(console.prompt("保存しますか？ (y/n)"))
                if save.lower().startswith('y'):
                    fname = input(console.prompt("ファイル名 (例: spam1.txt)"))
                    if not fname.endswith('.txt'): fname += '.txt'
                    with open(os.path.join(msg_dir, fname), 'w', encoding='utf-8') as f:
                        f.write(message)
                    console.log("Saved", C["green"], False, f"'{fname}' に保存")
        else:
            message = input(console.prompt("メッセージ (空でキャンセル)"))
            if message == "": self.main_menu()
        use_guild = input(console.prompt("Guild IDで全チャンネル送信？ (y/n)"))
        if use_guild.lower().startswith('y'):
            guild_id = input(console.prompt("Guild ID"))
            if not guild_id: self.main_menu()
            found = False
            for token in self.raider.tokens:
                try:
                    resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/channels", token, headers=self.raider.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text = [c for c in channels if c.get('type') == 0]
                        console.log("Found", C["green"], False, f"{len(text)} text channels")
                        found = True; break
                except: pass
            if not found:
                console.log("Failed", C["red"], "チャンネル取得失敗")
                input("Press Enter..."); self.main_menu()
            first_text = None
            for token in self.raider.tokens:
                try:
                    resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/channels", token, headers=self.raider.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text = [c for c in channels if c.get('type') == 0]
                        if text: first_text = text[0]['id']; break
                except: pass
            if first_text:
                self.raider.member_scrape(guild_id, first_text)
            add_poll = input(console.prompt("投票を追加？ (y/n)"))
            poll_data = None
            if add_poll.lower().startswith('y'):
                poll_data = {
                    "question": input(console.prompt("質問 (デフォルト: Raid)")) or "Raid",
                    "options": input(console.prompt("選択肢 (カンマ区切り, デフォルト: join,now,msmn)")).split(",") or ["join","now","msmn"]
                }
                poll_data["options"] = [opt.strip() for opt in poll_data["options"] if opt.strip()]
            pings = int(input(console.prompt("Pings数 (0推奨)")) or "0")
            delay = float(input(console.prompt("サイクル間遅延 (秒, 推奨0~5)")) or "0")
            massping = input(console.prompt("ランダムメンション有効？ (y/n)"))
            massping_count = int(input(console.prompt("メンション数")) or "1") if massping.lower().startswith('y') else 0
            random_str_flag = input(console.prompt("ランダム文字列追加？ (y/n)")).lower().startswith('y')
            valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "参加トークンがありません")
                input("Press Enter..."); self.main_menu()
            args = [(tok, guild_id, message, pings, delay, poll_data, massping.lower().startswith('y'), massping_count, random_str_flag) for tok in valid_tokens]
            self.run_spammer(self.raider.guild_spammer, args)
        else:
            link = input(console.prompt("チャンネルリンク"))
            if not link.startswith("https://"): self.main_menu()
            guild_id = link.split("/")[4]
            channel_id = link.split("/")[5]
            massping = input(console.prompt("Massping", True))
            random_str_flag = input(console.prompt("Random String", True)).lower().startswith('y')
            delay_input = input(console.prompt("Delay (秒)"))
            delay = float(delay_input) if delay_input else None
            ping_count = None
            if massping.lower().startswith('y'):
                self.raider.member_scrape(guild_id, channel_id)
                ping_count = int(input(console.prompt("Pings数")) or "1")
            add_poll = input(console.prompt("投票追加？ (y/n)"))
            poll_data = None
            if add_poll.lower().startswith('y'):
                poll_data = {
                    "question": input(console.prompt("質問")) or "Raid",
                    "options": input(console.prompt("選択肢 (カンマ区切り)")).split(",") or ["join","now","msmn"]
                }
                poll_data["options"] = [opt.strip() for opt in poll_data["options"] if opt.strip()]
            valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "参加トークンがありません")
                input("Press Enter..."); self.main_menu()
            args = [(tok, channel_id, message, guild_id, massping.lower().startswith('y'), ping_count, random_str_flag, delay, poll_data) for tok in valid_tokens]
            self.run_spammer(self.raider.spammer, args)

    @wrapper
    def poll_spammer(self):
        console.log("Info", C["yellow"], False, "投票スパムは [03] Spammer で投票オプションを有効にしてください。")
        input("Press Enter..."); self.main_menu()

    @wrapper
    def schedule_spam(self):
        console.title("Masumani - Schedule Spam")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        channel_id = input(console.prompt("Channel ID (空=全チャンネル)")).strip() or None
        msg_dir = "data/messages"
        if not os.path.exists(msg_dir): os.makedirs(msg_dir)
        files = [f for f in os.listdir(msg_dir) if f.endswith('.txt')]
        if files:
            print(f"{C['cyan']}保存済みメッセージ:{C['white']}")
            for idx, fname in enumerate(files, 1):
                print(f"  {idx}: {fname}")
            print("  0: 新規入力")
            choice = input(console.prompt("選択 (番号)"))
            if choice.isdigit() and int(choice) > 0 and int(choice) <= len(files):
                selected = files[int(choice)-1]
                with open(os.path.join(msg_dir, selected), 'r', encoding='utf-8') as f:
                    message = f.read().strip()
                console.log("Loaded", C["green"], False, f"'{selected}' を読み込み")
            else:
                message = input(console.prompt("メッセージ (空でキャンセル)"))
                if message == "": self.main_menu()
        else:
            message = input(console.prompt("メッセージ (空でキャンセル)"))
            if message == "": self.main_menu()
        schedule_time = input(console.prompt("実行時刻 (HH:MM)"))
        if not re.match(r"^\d{2}:\d{2}$", schedule_time):
            console.log("Invalid time format", C["red"]); input(); self.main_menu()
        pings = int(input(console.prompt("Pings数")) or "0")
        delay = float(input(console.prompt("サイクル間遅延 (秒)")) or "0")
        massping = input(console.prompt("ランダムメンション有効？ (y/n)"))
        massping_count = int(input(console.prompt("メンション数")) or "1") if massping.lower().startswith('y') else 0
        random_str_flag = input(console.prompt("ランダム文字列追加？ (y/n)")).lower().startswith('y')
        add_poll = input(console.prompt("投票追加？ (y/n)"))
        poll_data = None
        if add_poll.lower().startswith('y'):
            poll_data = {
                "question": input(console.prompt("質問")) or "Raid",
                "options": input(console.prompt("選択肢 (カンマ区切り)")).split(",") or ["join","now","msmn"]
            }
            poll_data["options"] = [opt.strip() for opt in poll_data["options"] if opt.strip()]
        valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
        if not valid_tokens:
            console.log("Failed", C["red"], "参加トークンがありません")
            input("Press Enter..."); self.main_menu()
        threading.Thread(target=self.raider.schedule_spam, args=(guild_id, channel_id, message, schedule_time, valid_tokens, pings, delay, massping.lower().startswith('y'), massping_count, random_str_flag, poll_data), daemon=True).start()
        console.log("Schedule set", C["green"], False, f"Start at {schedule_time}")
        input("Press Enter..."); self.main_menu()

    @wrapper
    def repeat_schedule(self):
        console.title("Masumani - Repeat Schedule")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        channel_id = input(console.prompt("Channel ID (空=全チャンネル)")).strip() or None
        msg_dir = "data/messages"
        if not os.path.exists(msg_dir): os.makedirs(msg_dir)
        files = [f for f in os.listdir(msg_dir) if f.endswith('.txt')]
        if files:
            print(f"{C['cyan']}保存済みメッセージ:{C['white']}")
            for idx, fname in enumerate(files, 1):
                print(f"  {idx}: {fname}")
            print("  0: 新規入力")
            choice = input(console.prompt("選択 (番号)"))
            if choice.isdigit() and int(choice) > 0 and int(choice) <= len(files):
                selected = files[int(choice)-1]
                with open(os.path.join(msg_dir, selected), 'r', encoding='utf-8') as f:
                    message = f.read().strip()
                console.log("Loaded", C["green"], False, f"'{selected}' を読み込み")
            else:
                message = input(console.prompt("メッセージ (空でキャンセル)"))
                if message == "": self.main_menu()
        else:
            message = input(console.prompt("メッセージ (空でキャンセル)"))
            if message == "": self.main_menu()
        schedule_time = input(console.prompt("実行時刻 (HH:MM)"))
        if not re.match(r"^\d{2}:\d{2}$", schedule_time):
            console.log("Invalid time format", C["red"]); input(); self.main_menu()
        interval = int(input(console.prompt("繰り返し間隔 (分)")) or "60")
        max_runs = int(input(console.prompt("最大実行回数 (0=無限)")) or "0")
        pings = int(input(console.prompt("Pings数")) or "0")
        delay = float(input(console.prompt("サイクル間遅延 (秒)")) or "0")
        massping = input(console.prompt("ランダムメンション有効？ (y/n)"))
        massping_count = int(input(console.prompt("メンション数")) or "1") if massping.lower().startswith('y') else 0
        random_str_flag = input(console.prompt("ランダム文字列追加？ (y/n)")).lower().startswith('y')
        add_poll = input(console.prompt("投票追加？ (y/n)"))
        poll_data = None
        if add_poll.lower().startswith('y'):
            poll_data = {
                "question": input(console.prompt("質問")) or "Raid",
                "options": input(console.prompt("選択肢 (カンマ区切り)")).split(",") or ["join","now","msmn"]
            }
            poll_data["options"] = [opt.strip() for opt in poll_data["options"] if opt.strip()]
        valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
        if not valid_tokens:
            console.log("Failed", C["red"], "参加トークンがありません")
            input("Press Enter..."); self.main_menu()
        self.raider.repeat_schedule_spam(guild_id, channel_id, message, schedule_time, interval, valid_tokens, pings, delay, massping.lower().startswith('y'), massping_count, random_str_flag, poll_data, max_runs)
        console.log("Repeat schedule started", C["green"])
        input("Press Enter..."); self.main_menu()

    @wrapper
    def status_manager(self):
        console.title("Masumani - Status Manager")
        if self.raider.status_thread_running:
            console.log("Status manager already running", C["yellow"])
            input("Press Enter..."); self.main_menu(); return
        self.raider.status_manager()
        self.raider.status_thread_running = True
        console.log("Status manager started", C["green"])
        input("Press Enter..."); self.main_menu()

    @wrapper
    def advanced_reaction(self):
        console.title("Masumani - Advanced Reaction")
        channel_id = input(console.prompt("Channel ID")).strip()
        if not channel_id: self.main_menu()
        target_type = input(console.prompt("Target type (user/keyword/message_id)")).strip()
        target_value = input(console.prompt("Target value")).strip()
        emoji = input(console.prompt("Emoji")).strip()
        if not all([channel_id, target_type, target_value, emoji]):
            console.log("Missing parameters", C["red"]); input(); self.main_menu()
        self.raider.advanced_reaction(channel_id, target_type, target_value, emoji)
        console.log("Advanced reaction triggered", C["green"])
        input("Press Enter..."); self.main_menu()

    @wrapper
    def cache_clear(self):
        console.title("Masumani - Cache Clear")
        self.raider.clear_cache()
        input("Press Enter..."); self.main_menu()

    @wrapper
    def clear_status(self):
        console.title("Masumani - Clear Status")
        self.run(self.raider.clear_activity, [()])

    @wrapper
    def onliner(self):
        console.title("Masumani - Onliner")
        args = [(tok,) for tok in self.raider.tokens]
        self.run(self.raider.keep_online, args)

    @wrapper
    def mass_timeout(self):
        console.title("Masumani - Mass Timeout")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        days = int(input(console.prompt("タイムアウト日数 (1-28, デフォルト: 28)")) or "28")
        days = max(1, min(28, days))
        valid = []
        for token in self.raider.tokens:
            try:
                resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/members/@me", token, headers=self.raider.headers_full(token), timeout=10)
                if resp.status_code == 200:
                    valid.append(token)
            except: pass
        if not valid:
            console.log("Failed", C["red"], "有効なトークンがありません")
            input("Press Enter..."); self.main_menu()
        args = [(tok, guild_id, days) for tok in valid]
        self.run(self.raider.mass_timeout, args)

    @wrapper
    def mass_nick_all(self):
        console.title("Masumani - Mass Nick All")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        new_nick = input(console.prompt("新しいニックネーム")).strip()
        if not new_nick: self.main_menu()
        valid = []
        for token in self.raider.tokens:
            try:
                resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/members/@me", token, headers=self.raider.headers_full(token), timeout=10)
                if resp.status_code == 200:
                    valid.append(token)
            except: pass
        if not valid:
            console.log("Failed", C["red"], "有効なトークンがありません")
            input("Press Enter..."); self.main_menu()
        args = [(tok, guild_id, new_nick) for tok in valid]
        self.run(self.raider.mass_nick_all, args)

    @wrapper
    def token_quality(self):
        console.title("Masumani - Token Quality")
        self.raider.token_quality_check()

    @wrapper
    def dm_spam(self):
        console.title("Masumani - Dm Spammer")
        user_id = input(console.prompt("User ID")).strip()
        if not user_id: self.main_menu()
        message = input(console.prompt("Message")).strip()
        if not message: self.main_menu()
        args = [(tok, user_id, message) for tok in self.raider.tokens]
        self.run(self.raider.dm_spammer, args)

    @wrapper
    def soundbord(self):
        console.title("Masumani - Soundboard Spam")
        link = input(console.prompt("Channel LINK")).strip()
        if not link.startswith("https://"): self.main_menu()
        channel = link.split("/")[5]
        guild = link.split("/")[4]
        for token in self.raider.tokens:
            threading.Thread(target=self.raider.join_voice_channel, args=(token, guild, channel), daemon=True).start()
            threading.Thread(target=self.raider.soundbord, args=(token, channel), daemon=True).start()

    @wrapper
    def friender(self):
        console.title("Masumani - Friender")
        nickname = input(console.prompt("Nick")).strip()
        if not nickname: self.main_menu()
        args = [(tok, nickname) for tok in self.raider.tokens]
        self.run(self.raider.friender, args)

    @wrapper
    def caller(self):
        console.title("Masumani - Call Spammer")
        user_id = input(console.prompt("User ID")).strip()
        if not user_id: self.main_menu()
        args = [(tok, user_id) for tok in self.raider.tokens]
        self.run(self.raider.call_spammer, args)

    @wrapper
    def typier(self):
        console.title("Masumani - Typer")
        link = input(console.prompt("Channel LINK")).strip()
        if not link.startswith("https://"): self.main_menu()
        channel_id = link.split("/")[5]
        args = [(tok, channel_id) for tok in self.raider.tokens]
        self.run(self.raider.typier, args)

    @wrapper
    def nick_changer(self):
        console.title("Masumani - Nickname Changer")
        nick = input(console.prompt("Nick")).strip()
        if not nick or len(nick)>32: self.main_menu()
        guild = input(console.prompt("Guild ID")).strip()
        if not guild: self.main_menu()
        args = [(tok, guild, nick) for tok in self.raider.tokens]
        self.run(self.raider.mass_nick, args)

    @wrapper
    def voice_joiner(self):
        console.title("Masumani - Voice Joiner")
        link = input(console.prompt("Channel LINK")).strip()
        if not link.startswith("https://"): self.main_menu()
        guild = link.split("/")[4]; channel = link.split("/")[5]
        args = [(tok, guild, channel) for tok in self.raider.tokens]
        self.run(self.raider.join_voice_channel, args)

    @wrapper
    def Thread_Spammer(self):
        console.title("Masumani - Thread Spammer")
        link = input(console.prompt("Channel LINK")).strip()
        if not link.startswith("https://"): self.main_menu()
        name = input(console.prompt("Thread name")).strip()
        if not name: self.main_menu()
        channel_id = link.split("/")[5]
        args = [(tok, channel_id, name) for tok in self.raider.tokens]
        self.run(self.raider.thread_spammer, args)

    @wrapper
    def reactor(self):
        console.title("Masumani - Reactor")
        link = input(console.prompt("Message Link")).strip()
        if not link.startswith("https://"): self.main_menu()
        channel_id = link.split("/")[5]; message_id = link.split("/")[6]
        self.raider.reactor_main(channel_id, message_id)

    @wrapper
    def button(self):
        console.title("Masumani - Button Click")
        link = input(console.prompt("Message Link")).strip()
        if not link.startswith("https://"): self.main_menu()
        guild_id = link.split("/")[4]; channel_id = link.split("/")[5]; message_id = link.split("/")[6]
        self.raider.button_bypass(channel_id, message_id, guild_id)

    @wrapper
    def accept(self):
        console.title("Masumani - Accept Rules")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        self.raider.accept_rules(guild_id)

    @wrapper
    def guild(self):
        console.title("Masumani - Guild Checker")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        self.raider.guild_checker(guild_id)

    @wrapper
    def bio_changer(self):
        console.title("Masumani - Bio Changer")
        bio = input(console.prompt("Bio")).strip()
        if not bio: self.main_menu()
        args = [(tok, bio) for tok in self.raider.tokens]
        self.run(self.raider.bio_changer, args)

    @wrapper
    def onboard(self):
        console.title("Masumani - Onboarding Bypass")
        guild_id = input(console.prompt("Guild ID")).strip()
        if not guild_id: self.main_menu()
        self.raider.onboard_bypass(guild_id)

    def checker(self):
        console.title("Masumani - Checker")
        self.raider.token_checker()

    def formatter(self):
        console.title("Masumani - Formatter")
        self.run(self.raider.format_tokens, [()])

    @wrapper
    def credit(self):
        lines = [
            "Special Thanks to",
            "Coder: Tips",
            "Scraper: Aniell4",
            "Original Owner of Helium/Masumani: Ekkore",
            "And last but not least, you!"
        ]
        for line in lines:
            print(f"{self.background}{line.center(os.get_terminal_size().columns)}{Fore.RESET}")
        input("\n ~/> press enter to continue ")
        self.main_menu()

    def show_help(self):
        console.clear(); console.render_ascii()
        help_text = f"""
{C['cyan']}【 Masumani Ultimate ヘルプ 】{C['white']}
全34機能 + ボイス自動維持 + スパマー安定化
endコマンドでスパム停止
設定: config.json で遅延・リトライ・プロキシローテーション調整
"""
        print(help_text)
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    @wrapper
    def exits(self):
        if input(console.prompt("Quit?", ask=True)).lower().startswith('y'):
            self.raider.cleanup_voice()
            ws_pool.close_all()
            os._exit(0)
        else: self.main_menu()

global_raider = None

# ---------- クリーンアップ ----------
def cleanup():
    SHOULD_STOP.set()
    ws_pool.close_all()
    if global_raider:
        global_raider.cleanup_voice()
        try:
            for tok, sess in global_raider._sessions.items():
                sess.close()
        except: pass
    console.log("Cleanup", C["green"], False, "All connections closed.")

# ---------- エントリーポイント ----------
if __name__ == "__main__":
    try:
        Menu().main_menu()
    except KeyboardInterrupt:
        cleanup()
        print("\nExited.")
    finally:
        cleanup()
