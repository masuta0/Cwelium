# Copyright (c) 2024-2026 Masumani Inc.
# This project is licensed under the Masumani License, which includes additional
# terms under the GNU Affero General Public License (AGPL) v3.0.
#
# Author: Tips-Discord
# Original Repository: https://github.com/Tips-Discord/Masumani
#
# Additional Terms can be found at:
# https://github.com/Tips-Discord/Masumani/blob/main/LICENSE

# ============================================================================
#  ⚠️ 警告 : このツールは Discord 利用規約に違反します。
#          アカウント停止・法的措置のリスクがあります。
#          教育目的以外での使用は厳に慎んでください。
# ============================================================================

import getpass
import sys
import select
from colorama import Fore, init; init(autoreset=True)
from colorist import ColorHex as h
from datetime import datetime, timedelta
import base64
import ctypes
import os
import random
import re
import requests
import zlib
import socket
import string
import threading
import time
import uuid
import websocket
import orjson
import concurrent.futures
import json as json_lib
import math
from collections import defaultdict, deque

# ==================== curl_cffi で TLS フィンガープリントを偽装 ====================
try:
    import curl_cffi
    USE_CURL_CFFI = True
except ImportError:
    USE_CURL_CFFI = False
    print("[!] curl_cffi not installed. Install with: pip install curl_cffi")
    print("[!] Without curl_cffi, your requests will be easily detected.")
    print("[!] Continuing with requests (high risk of detection)...")

# ==================== 設定ファイル ====================
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return orjson.loads(f.read())
    return {
        "Proxies": True,
        "Theme": "light_blue",
        "ApiVersion": "v10",
        "DelayMean": 3.0,
        "DelayStd": 1.0,
        "MinDelay": 1.5,
        "MaxDelay": 8.0,
        "UseTyping": True,
        "MessageVariation": True,
        "JoinerRetries": 0,
        "JoinerDelayMin": 10,
        "JoinerDelayMax": 30,
        "GlobalRateLimit": True,
        "RateLimitPerSecond": 3,
        "StatusRotation": True,
        "StatusInterval": 180,
        "CustomStatuses": ["Playing Games", "Listening to Music", "Watching YouTube"],
        "CacheTTL": 300,
        "MaxWorkers": 10,
    }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        f.write(orjson.dumps(config, option=orjson.OPT_INDENT_2).decode())

# ==================== グローバル終了フラグ ====================
SHOULD_STOP = False

class JsonWrapper:
    @staticmethod
    def loads(data, **kwargs):
        return orjson.loads(data)
    @staticmethod
    def load(fp, **kwargs):
        return orjson.loads(fp.read())
    @staticmethod
    def dumps(data, indent=None, separators=None, sort_keys=False, **kwargs):
        option = 0
        if indent:
            option |= orjson.OPT_INDENT_2
        if sort_keys:
            option |= orjson.OPT_SORT_KEYS
        option |= orjson.OPT_NON_STR_KEYS
        return orjson.dumps(data, option=option).decode()
    @staticmethod
    def dump(data, fp, indent=None, separators=None, sort_keys=False, **kwargs):
        option = 0
        if indent:
            option |= orjson.OPT_INDENT_2
        if sort_keys:
            option |= orjson.OPT_SORT_KEYS
        payload = orjson.dumps(data, option=option)
        try:
            fp.write(payload)
        except TypeError:
            fp.write(payload.decode())

json = JsonWrapper()

def get_random_str(length):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def wrapper(func):
    def wrapper(*args, **kwargs):
        console.clear()
        console.render_ascii()
        result = func(*args, **kwargs)
        return result
    return wrapper

C = {
    "green": h("#65fb07"),
    "red": h("#Fb0707"),
    "yellow": h("#FFCD00"),
    "magenta": h("#b207f5"),
    "blue": h("#00aaff"),
    "cyan": h("#aaffff"),
    "gray": h("#8a837e"),
    "white": h("#DCDCDC"),
    "pink": h("#c203fc"),
    "light_blue": h("#07f0ec"),
    "brown": h("#8B4513"),
    "black": h("#000000"),
    "aqua": h("#00CED1"),
    "purple": h("#800080"),
    "lime": h("#00FF00"),
    "orange": h("#FFA500"),
    "indigo": h("#4B0082"),
    "violet": h("#EE82EE"),
    "gold": h("#FFD700"),
    "silver": h("#C0C0C0"),
    "teal": h("#008080"),
    "navy": h("#000080"),
    "olive": h("#808000"),
    "maroon": h("#800000"),
    "coral": h("#FF7F50"),
    "salmon": h("#FA8072"),
    "khaki": h("#F0E68C"),
    "orchid": h("#DA70D6"),
    "rose": h("#FF007F")
}

class Files:
    @staticmethod
    def write_config():
        try:
            if not os.path.exists("config.json"):
                data = {
                    "Proxies": True,
                    "Theme": "light_blue",
                    "ApiVersion": "v10",
                    "DelayMean": 3.0,
                    "DelayStd": 1.0,
                    "MinDelay": 1.5,
                    "MaxDelay": 8.0,
                    "UseTyping": True,
                    "MessageVariation": True,
                    "JoinerRetries": 0,
                    "JoinerDelayMin": 10,
                    "JoinerDelayMax": 30,
                    "GlobalRateLimit": True,
                    "RateLimitPerSecond": 3,
                    "StatusRotation": True,
                    "StatusInterval": 180,
                    "CustomStatuses": ["Playing Games", "Listening to Music", "Watching YouTube"],
                    "CacheTTL": 300,
                    "MaxWorkers": 10,
                }
                with open("config.json", "w") as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Write Config", e)
    @staticmethod
    def write_folders():
        folders = ["data", "scraped", "data/messages", "data/templates"]
        for folder in folders:
            try:
                if not os.path.exists(folder):
                    os.mkdir(folder)
            except Exception as e:
                console.log("Failed", C["red"], "Failed to Write Folders", e)
    @staticmethod
    def write_files():
        files = ["tokens.txt", "proxies.txt"]
        for file in files:
            try:
                if not os.path.exists(file):
                    with open(f"data/{file}", "a") as f:
                        f.close()
            except Exception as e:
                console.log("Failed", C["red"], "Failed to Write Files", e)
    @staticmethod
    def run_tasks():
        tasks = [Files.write_config, Files.write_folders, Files.write_files]
        for task in tasks:
            task()

Files.run_tasks()

config = load_config()
proxy = config.get("Proxies", True)
color = config.get("Theme", "light_blue")
api_version = config.get("ApiVersion", "v10")
delay_mean = config.get("DelayMean", 3.0)
delay_std = config.get("DelayStd", 1.0)
min_delay = config.get("MinDelay", 1.5)
max_delay = config.get("MaxDelay", 8.0)
use_typing = config.get("UseTyping", True)
message_variation = config.get("MessageVariation", True)
joiner_retries = config.get("JoinerRetries", 0)
joiner_delay_min = config.get("JoinerDelayMin", 10)
joiner_delay_max = config.get("JoinerDelayMax", 30)
global_rate_limit = config.get("GlobalRateLimit", True)
rate_limit_per_second = config.get("RateLimitPerSecond", 3)
status_rotation = config.get("StatusRotation", True)
status_interval = config.get("StatusInterval", 180)
custom_statuses = config.get("CustomStatuses", ["Playing Games", "Listening to Music", "Watching YouTube"])
cache_ttl = config.get("CacheTTL", 300)
max_workers = config.get("MaxWorkers", 10)
global_raider = None
API_BASE = f"https://discord.com/api/{api_version}"

# ==================== グローバルレートリミッター（バケット対応） ====================
class GlobalRateLimiter:
    def __init__(self):
        self.buckets = defaultdict(lambda: {"timestamps": deque(maxlen=100), "reset": 0})
        self.lock = threading.Lock()
        self.per_second = rate_limit_per_second

    def can_request(self, endpoint):
        if not global_rate_limit:
            return True
        with self.lock:
            now = time.time()
            bucket = self.buckets[endpoint]
            # リセット時間をチェック
            if now > bucket["reset"]:
                bucket["timestamps"].clear()
                bucket["reset"] = now + 1.0
            # 1秒あたりの制限をチェック
            if len(bucket["timestamps"]) >= self.per_second:
                return False
            bucket["timestamps"].append(now)
            return True

    def wait_if_needed(self, endpoint):
        if not global_rate_limit:
            return
        while not self.can_request(endpoint):
            time.sleep(0.05)

    def update_from_response(self, endpoint, response):
        """429レスポンスからretry_afterを取得して更新"""
        try:
            if response.status_code == 429:
                data = response.json()
                retry_after = data.get("retry_after", 5)
                with self.lock:
                    self.buckets[endpoint]["reset"] = time.time() + retry_after + 0.5
        except:
            pass

global_rate_limiter = GlobalRateLimiter()

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
        except Exception:
            pass
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
        denom = (w_idx**2 + h_idx**2)
        factor = (x * w_idx + y * h_idx) / denom
        factor = max(0, min(1, factor))
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * factor)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * factor)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * factor)
        return h(f'#{r:02x}{g:02x}{b:02x}')
    def center_colored(self, text, visible_len):
        try:
            terminal_width = os.get_terminal_size().columns
        except OSError:
            terminal_width = self.size
        padding = max(0, (terminal_width - visible_len) // 2)
        return (" " * padding) + text
    def render_ascii(self):
        self.clear()
        self.title(f"Masumani | Connected as {self.username} | made by Tips-Discord")
        edges = {"╗", "║", "╚", "╝", "═", "╔"}
        logo = [
            " ███╗   ███╗ █████╗ ███████╗██╗   ██╗███╗   ███╗ █████╗ ███╗   ██╗██╗",
            " ████╗ ████║██╔══██╗██╔════╝██║   ██║████╗ ████║██╔══██╗████╗  ██║██║",
            " ██╔████╔██║███████║███████╗██║   ██║██╔████╔██║███████║██╔██╗ ██║██║",
            " ██║╚██╔╝██║██╔══██║╚════██║██║   ██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║",
            " ██║ ╚═╝ ██║██║  ██║███████║╚██████╔╝██║ ╚═╝ ██║██║  ██║██║ ╚████║██║",
            " ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝",
        ]
        height = len(logo)
        width = max(len(line) for line in logo)
        print("\n")
        for y, line in enumerate(logo):
            colored_line = ""
            visible_len = 0
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
                global proxies
                proxies = [p.strip() for p in f.read().splitlines() if p.strip()]
        except FileNotFoundError:
            proxies = []
        try:
            with open("data/tokens.txt", "r") as f:
                global tokens
                tokens = [t.strip() for t in f.read().splitlines() if t.strip()]
        except FileNotFoundError:
            tokens = []
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
        h_menu = len(menu)
        w_menu = len(menu[0])
        for y, line in enumerate(menu):
            colored_line = ""
            visible_len = 0
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

if USE_CURL_CFFI:
    try:
        console.log("Info", C["cyan"], False, "curl_cffi enabled (TLS fingerprint spoofing)")
    except:
        pass

class AutoFetchHeaders:
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9219 Chrome/138.0.7204.251 Electron/37.6.0 Safari/537.36"
    client_build_number = 482285
    native_build_number = 73385
    client_version = "1.0.9219"
    browser_version = "37.6.0"
    _fetched = False
    @staticmethod
    def fetch():
        try:
            if AutoFetchHeaders._fetched:
                return
            console.log("Scraping", C["light_blue"], False, "Fetching latest Discord headers...")
            response = requests.get("https://api.sockets.lol/discord/build", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "clients" in data and "Discord" in data["clients"]:
                    discord_data = data["clients"]["Discord"]["decoded"]
                    if discord_data.get("release_channel") == "stable":
                        AutoFetchHeaders.user_agent = discord_data["browser_user_agent"]
                        AutoFetchHeaders.client_version = discord_data["client_version"]
                        AutoFetchHeaders.browser_version = discord_data["browser_version"]
                        AutoFetchHeaders.native_build_number = discord_data["native_build_number"]
                        AutoFetchHeaders.client_build_number = discord_data["client_build_number"]
                        console.log("Success", C["green"], False, f"Updated: Build {AutoFetchHeaders.client_build_number} | v{AutoFetchHeaders.client_version}")
                        AutoFetchHeaders._fetched = True
                    else:
                        console.log("Failed", C["red"], False, "Fetched data was not Stable channel.")
                else:
                    console.log("Failed", C["red"], False, "Stable 'Discord' client data not found in API.")
            else:
                console.log("Failed", C["red"], False, f"API returned status {response.status_code}")
        except Exception as e:
            console.log("Failed", C["red"], "AutoFetch", e)

class Utils:
    @staticmethod
    def get_ranges(index, multiplier):
        initial_num = index * multiplier
        return [[initial_num, initial_num + 99], [initial_num + 100, initial_num + 199]]
    @staticmethod
    def parse_member_list_update(data):
        d = data["d"]
        return {
            "online_count": d["online_count"],
            "member_count": d["member_count"],
            "guild_id": d["guild_id"],
            "ops": d["ops"]
        }
    @staticmethod
    def safe_json_parse(text):
        try:
            return json.loads(text)
        except:
            return None

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
        self.end_scraping = False
        self.guild_member_count = 0
        self.members = {}
        self.ranges = [[0, 99]]
        self.last_range = 0
        self.packets_recv = 0
    def run(self):
        self.run_forever(sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),))
        return self.members
    def scrape_users(self):
        if self.end_scraping:
            return
        payload = {
            "op": 14,
            "d": {
                "guild_id": self.guild_id,
                "typing": False,
                "activities": False,
                "threads": False,
                "channels": {self.channel_id: self.ranges}
            }
        }
        self.send(json.dumps(payload))
    def on_open(self, ws):
        self.send(json.dumps({
            "op": 2,
            "d": {
                "token": self.token,
                "capabilities": 1734653,
                "properties": {
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": AutoFetchHeaders.user_agent,
                    "browser_version": AutoFetchHeaders.browser_version,
                    "os_version": "10",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": AutoFetchHeaders.client_build_number,
                    "client_event_source": None
                },
                "presence": {
                    "status": "online",
                    "since": 0,
                    "activities": [],
                    "afk": False
                },
                "compress": False,
                "client_state": {
                    "guild_hashes": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1
                }
            }
        }))
        self.ready_event.set()
    def heartbeat_thread(self, interval):
        while not self.end_scraping:
            try:
                self.send(json.dumps({"op": 1, "d": self.packets_recv}))
                time.sleep(interval)
            except Exception:
                break
    def on_message(self, ws, message):
        if isinstance(message, bytes):
            self.buffer.extend(message)
            if len(message) < 4 or message[-4:] != b'\x00\x00\xff\xff':
                return
            try:
                message = self.inflator.decompress(self.buffer)
                message = message.decode("utf-8")
                self.buffer = bytearray()
            except Exception:
                return
        decoded = Utils.safe_json_parse(message)
        if decoded is None:
            return
        op = decoded.get("op")
        t = decoded.get("t")
        self.packets_recv += 1 if op != 11 else 0
        if op == 10:
            interval = decoded["d"]["heartbeat_interval"] / 1000
            threading.Thread(target=self.heartbeat_thread, args=(interval,), daemon=True).start()
        elif t == "READY":
            for guild in decoded["d"]["guilds"]:
                if guild["id"] == self.guild_id:
                    self.guild_member_count = guild.get("member_count", 0)
                    break
            console.log("Info", C["yellow"], False, f"Target: {self.guild_member_count} members")
        elif t == "READY_SUPPLEMENTAL":
            self.ranges = Utils.get_ranges(0, 100)
            self.scrape_users()
        elif t == "GUILD_MEMBER_LIST_UPDATE":
            parsed = Utils.parse_member_list_update(decoded)
            if parsed["guild_id"] == self.guild_id:
                should_continue = False
                for op_chunk in parsed["ops"]:
                    op_type = op_chunk["op"]
                    if op_type in ("SYNC", "UPDATE"):
                        if op_type == "SYNC":
                            items = op_chunk.get("items")
                        else:
                            items = [op_chunk.get("item")]
                        if not items:
                            continue
                        for item in items:
                            member = item.get("member")
                            if not member:
                                continue
                            user = member.get("user")
                            if not user:
                                continue
                            uid = user.get("id")
                            if uid and uid not in self.blacklisted_ids and not user.get("bot"):
                                self.members[uid] = {
                                    "tag": f"{user.get('username')}#{user.get('discriminator', '0')}",
                                    "id": uid
                                }
                        should_continue = True
                    elif op_type == "INVALIDATE":
                        self.ranges = Utils.get_ranges(self.last_range, 100)
                        self.scrape_users()
                if len(self.members) >= self.guild_member_count or not should_continue:
                    if (self.last_range * 100) >= self.guild_member_count:
                        self.end_scraping = True
                        self.close()
                        return
                self.last_range += 2
                self.ranges = Utils.get_ranges(self.last_range, 100)
                self.scrape_users()
    def on_error(self, ws, error):
        if not self.end_scraping:
            console.log("Error", C["red"], False, f"Socket Error: {error}")
    def on_close(self, ws, close_code, close_msg):
        if not self.end_scraping:
            console.log("Info", C["yellow"], False, f"Socket closed, scraped {len(self.members)} members")
        else:
            console.log("Success", C["green"], False, f"Scraped {len(self.members)} members in {time.time() - self.start:.2f}s")

def scrape(token, guild_id, channel_id):
    sb = DiscordSocket(token, guild_id, channel_id)
    return sb.run()

class WebSocketPool:
    """WebSocket接続をプールして再利用する（ステータス更新・オンライン維持用）"""
    def __init__(self):
        self._connections = {}
        self._lock = threading.Lock()
        self._heartbeat_threads = {}
    
    def get_connection(self, token):
        with self._lock:
            if token in self._connections:
                ws, last_used = self._connections[token]
                if time.time() - last_used < 60:
                    return ws
            # 新規接続
            try:
                ws = websocket.WebSocket()
                ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
                self._connections[token] = (ws, time.time())
                return ws
            except Exception as e:
                console.log("WS Pool Error", C["red"], f"{token[:15]}...", str(e))
                return None
    
    def close_all(self):
        with self._lock:
            for token, (ws, _) in self._connections.items():
                try:
                    ws.close()
                except:
                    pass
            self._connections.clear()

ws_pool = WebSocketPool()

# ============================================================================
#  超強化 Raider クラス（全機能実装・最新API v10）
# ============================================================================
class Raider:
    def __init__(self):
        global proxies, tokens
        try:
            with open("data/proxies.txt") as f:
                proxies = [p.strip() for p in f.read().splitlines() if p.strip()]
        except FileNotFoundError:
            proxies = []
            console.log("Warning", C["yellow"], False, "proxies.txt not found, using no proxy")
        try:
            with open("data/tokens.txt", "r") as f:
                tokens = [t.strip() for t in f.read().splitlines() if t.strip()]
        except FileNotFoundError:
            tokens = []
            console.log("Warning", C["yellow"], False, "tokens.txt not found, no tokens loaded")
        
        AutoFetchHeaders.fetch()
        self.cached_members = {}
        self.cache_timestamps = {}
        self._sessions = {}
        self._session_lock = threading.Lock()
        self._proxy_pool = proxies if proxy else []
        self._proxy_index = 0
        self.status_thread_running = False
        
        if USE_CURL_CFFI:
            console.log("Info", C["cyan"], False, "curl_cffi enabled (TLS fingerprint spoofing)")
        else:
            console.log("Info", C["yellow"], False, "curl_cffi not available, using requests (higher risk)")

    def _get_next_proxy(self):
        if not self._proxy_pool:
            return None
        self._proxy_index = (self._proxy_index + 1) % len(self._proxy_pool)
        return self._proxy_pool[self._proxy_index]

    def _get_impersonate(self):
        safe_choices = [
            "chrome110", "chrome120", "chrome124", "chrome136",
            "edge101", "edge120",
            "firefox102", "firefox128"
        ]
        return random.choice(safe_choices)

    def get_session(self, token, force_new=False):
        with self._session_lock:
            if force_new or token not in self._sessions:
                if USE_CURL_CFFI:
                    try:
                        impersonate = self._get_impersonate()
                        self._sessions[token] = curl_cffi.Session(impersonate=impersonate)
                    except Exception as e:
                        console.log("Fallback", C["yellow"], f"{token[:15]}...", f"curl_cffi failed ({e}), using requests")
                        self._sessions[token] = requests.Session()
                        self._sessions[token].headers.update({"User-Agent": AutoFetchHeaders.user_agent})
                else:
                    self._sessions[token] = requests.Session()
                    self._sessions[token].headers.update({"User-Agent": AutoFetchHeaders.user_agent})
            return self._sessions[token]

    def _request(self, method, url, token, headers=None, json=None, params=None, timeout=15):
        endpoint = url.split(f"/api/{api_version}/")[-1] if f"/api/{api_version}/" in url else url
        global_rate_limiter.wait_if_needed(endpoint)
        sess = self.get_session(token)
        if proxy and self._proxy_pool:
            proxy_url = self._get_next_proxy()
            sess.proxies = {"http": f"http://{proxy_url}", "https": f"http://{proxy_url}"}
        else:
            sess.proxies = {}
        try:
            resp = sess.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                params=params,
                timeout=timeout
            )
            global_rate_limiter.update_from_response(endpoint, resp)
            return resp
        except Exception as e:
            console.log("Request Error", C["red"], f"{token[:15]}...", str(e))
            raise

    def headers_minimal(self, token):
        return {
            "Authorization": token,
            "User-Agent": AutoFetchHeaders.user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def headers_full(self, token):
        return {
            "Authorization": token,
            "User-Agent": AutoFetchHeaders.user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "X-Super-Properties": self.generate_super_properties(),
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
        }

    def generate_super_properties(self):
        payload = {
            "os": "Windows",
            "browser": "Discord Client",
            "release_channel": "stable",
            "client_version": AutoFetchHeaders.client_version,
            "os_version": "10.0.26100",
            "system_locale": "en-US",
            "browser_user_agent": AutoFetchHeaders.user_agent,
            "browser_version": AutoFetchHeaders.browser_version,
            "client_build_number": AutoFetchHeaders.client_build_number,
            "native_build_number": AutoFetchHeaders.native_build_number,
            "client_launch_id": str(uuid.uuid4()),
            "client_heartbeat_session_id": str(uuid.uuid4()),
            "launch_signature": str(uuid.uuid4()),
            "client_event_source": None,
            "has_client_mods": False,
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def nonce(self):
        return int(time.time() * 1000) - 1420070400000 << 22

    def human_delay(self):
        delay = random.gauss(delay_mean, delay_std)
        delay = max(min_delay, min(delay, max_delay))
        if random.random() < 0.2:
            delay += random.uniform(0.3, 1.0)
        time.sleep(delay)
        return delay

    def vary_message(self, base_message):
        if not message_variation:
            return base_message
        emojis = ["", "✨", "🔥", "💀", "🎯", "🚀", "💥", "⚡", "🌀", "🔰", "💫", "🌟"]
        spacers = ["", " ", "  ", " - ", " | ", " • ", " · ", " ✦ "]
        suffixes = ["", "", "", " (auto)", " 🔥", " 💀", " 🚀"]
        parts = [base_message]
        if random.random() < 0.5:
            parts.insert(0, random.choice(emojis))
        if random.random() < 0.3:
            parts.insert(1, random.choice(spacers))
        if random.random() < 0.3:
            parts.append(random.choice(suffixes))
        random.shuffle(parts)
        return "".join(parts).strip()

    def send_typing(self, token, channel_id):
        if not use_typing:
            return
        if random.random() < 0.4:
            try:
                self._request("POST", f"{API_BASE}/channels/{channel_id}/typing",
                              token, headers=self.headers_full(token), timeout=5)
            except:
                pass

    def is_token_valid(self, token):
        try:
            resp = self._request("GET", f"{API_BASE}/users/@me",
                                 token, headers=self.headers_minimal(token), timeout=10)
            return resp.status_code == 200
        except:
            return False

    def check_membership(self, token, guild_id):
        if not self.is_token_valid(token):
            console.log("Invalid Token", C["red"], f"{token[:15]}...", "Token is invalid")
            return False
        try:
            resp = self._request("GET", f"{API_BASE}/users/@me/guilds",
                                 token, headers=self.headers_minimal(token), timeout=10)
            if resp.status_code == 200:
                guilds = resp.json()
                for guild in guilds:
                    if guild["id"] == guild_id:
                        return True
                return False
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5) + random.uniform(0, 2)
                console.log("Ratelimit", C["yellow"], f"{token[:15]}...", f"guilds wait {wait:.1f}s")
                time.sleep(wait)
                return self.check_membership(token, guild_id)
            else:
                resp2 = self._request("GET", f"{API_BASE}/guilds/{guild_id}/members/@me",
                                      token, headers=self.headers_minimal(token), timeout=10)
                return resp2.status_code == 200
        except Exception as e:
            console.log("Error in check_membership", C["red"], f"{token[:15]}...", str(e))
            return False

    def get_valid_tokens_for_guild(self, guild_id):
        def check_token(token):
            try:
                return token if self.check_membership(token, guild_id) else None
            except:
                return None

        console.log("Filtering tokens (parallel)...", C["yellow"])
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(tokens))) as executor:
            results = list(executor.map(check_token, tokens))

        valid = [r for r in results if r is not None]
        console.log("Filtering Done", C["cyan"], False, f"Valid tokens in guild: {len(valid)}/{len(tokens)}")
        if not valid:
            console.log("Warning", C["yellow"], False, "No valid tokens found in guild.")
        return valid

    def get_text_channels(self, token, guild_id):
        try:
            resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/channels",
                                 token, headers=self.headers_full(token), timeout=10)
            if resp.status_code == 200:
                channels = resp.json()
                return [c for c in channels if c.get('type') == 0]
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5) + random.uniform(0, 2)
                console.log("Ratelimit", C["yellow"], f"{token[:15]}...", f"channels wait {wait:.1f}s")
                time.sleep(wait)
                return self.get_text_channels(token, guild_id)
            else:
                console.log("Failed to get channels", C["red"], f"{token[:15]}...", f"status {resp.status_code}")
                return []
        except Exception as e:
            console.log("Error get_text_channels", C["red"], f"{token[:15]}...", str(e))
            return []

    def send_message(self, token, channel_id, content, poll=None):
        self.send_typing(token, channel_id)
        varied_content = self.vary_message(content)
        payload = {"content": varied_content}
        if poll:
            payload["poll"] = {
                "question": {"text": poll["question"]},
                "answers": [{"poll_media": {"text": opt}} for opt in poll["options"]],
                "duration": 24,
                "allow_multiselect": False
            }
        for attempt in range(2):
            try:
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/messages",
                                     token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 200:
                    return True
                elif resp.status_code == 429:
                    wait = resp.json().get('retry_after', 3) + random.uniform(0, 1)
                    console.log("Ratelimit", C["yellow"], f"{token[:15]}...", f"wait {wait:.1f}s")
                    time.sleep(wait)
                    continue
                elif resp.status_code in (400, 403):
                    console.log("No permission", C["gray"], f"{token[:15]}...", f"Ch {channel_id} ({resp.status_code})")
                    return False
                else:
                    console.log("Failed", C["red"], f"{token[:15]}...", f"Ch {channel_id} ({resp.status_code})")
                    return False
            except Exception as e:
                console.log("Error send_message", C["red"], f"{token[:15]}...", str(e))
                return False
        return False

    def guild_spammer(self, token, guild_id, message, pings, delay, poll=None):
        if not self.check_membership(token, guild_id):
            console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild")
            return
        channels = self.get_text_channels(token, guild_id)
        if not channels:
            console.log("Info", C["yellow"], f"{token[:15]}...", "no text channels")
            return
        console.log("Started", C["green"], f"{token[:15]}...", f"{len(channels)} channels")
        active_channels = channels.copy()

        while not SHOULD_STOP:
            random.shuffle(active_channels)
            for ch in active_channels[:]:
                if SHOULD_STOP:
                    break
                success = self.send_message(token, ch['id'], message, poll)
                if not success:
                    console.log("Removing channel", C["gray"], f"{token[:15]}...", f"Ch {ch['id']} (no permission)")
                    active_channels.remove(ch)
                    continue
                self.human_delay()
            if not active_channels:
                console.log("Stopped", C["yellow"], f"{token[:15]}...", "No writable channels left")
                return
            console.log("Cycle Done", C["cyan"], f"{token[:15]}...", f"{len(active_channels)} channels remaining")
            if delay > 0:
                time.sleep(delay + random.uniform(0, 2))

    def spammer(self, token, channel_id, message, guild=None, massping=None,
                pings=None, random_str=None, delay=None, poll=None):
        if massping and guild:
            if not self.check_membership(token, guild):
                console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild for massping")
                return
        while not SHOULD_STOP:
            content = message
            if massping:
                members = self.get_random_members(guild, pings)
                if members:
                    content += f" {members}"
            if random_str:
                content += f" | {get_random_str(10)}"
            success = self.send_message(token, channel_id, content, poll)
            if not success:
                console.log("Stopped", C["yellow"], f"{token[:15]}...", "No permission on this channel")
                return
            if delay:
                time.sleep(delay + random.uniform(0, 1))
            else:
                self.human_delay()

    def get_random_members(self, guild_id, count):
        # キャッシュの有効期限チェック
        now = time.time()
        if guild_id in self.cache_timestamps:
            if now - self.cache_timestamps[guild_id] > cache_ttl:
                self.cached_members.pop(guild_id, None)
                self.cache_timestamps.pop(guild_id, None)
        
        if guild_id not in self.cached_members:
            try:
                file_path = f"scraped/{guild_id}.json"
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        self.cached_members[guild_id] = json.loads(f.read())
                        self.cache_timestamps[guild_id] = now
                else:
                    return ""
            except Exception as e:
                console.log("Error", C["red"], f"Cache Load Failed: {e}")
                return ""
        members = self.cached_members.get(guild_id, [])
        if not members:
            return ""
        # 上限を超えないように調整
        actual_count = min(count, len(members))
        selected = random.sample(members, actual_count)
        return " ".join(f"<@!{uid}>" for uid in selected)

    def member_scrape(self, guild_id, channel_id):
        try:
            if channel_id is None:
                for token in tokens:
                    resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/channels",
                                         token, headers=self.headers_full(token), timeout=5)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text_channels = [c for c in channels if c.get('type') == 0]
                        if text_channels:
                            channel_id = text_channels[0]['id']
                            break
                    self.human_delay()
                if channel_id is None:
                    console.log("Failed", C["red"], "No text channel found")
                    return
            valid_tokens = self.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "No valid token in guild")
                return
            if not os.path.exists(f"scraped/{guild_id}.json"):
                members = scrape(random.choice(valid_tokens), guild_id, channel_id)
                with open(f"scraped/{guild_id}.json", "w") as f:
                    json.dump(list(members.keys()), f, indent=2)
                console.log("Scraped", C["green"], False, f"{len(members)} members saved")
        except Exception as e:
            console.log("Failed", C["red"], False, f"member_scrape: {e}")

    def schedule_spam(self, guild_id, channel_id, message, schedule_time, tokens_list):
        try:
            now = datetime.now()
            target = datetime.strptime(schedule_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if target < now:
                target += timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            console.log("Schedule", C["yellow"], False, f"Spam will start at {target.strftime('%H:%M')} (in {wait_seconds:.0f}s)")
            time.sleep(wait_seconds)
            console.log("Schedule", C["green"], False, "Starting scheduled spam!")
            for token in tokens_list:
                threading.Thread(target=self.guild_spammer, args=(token, guild_id, message, 0, 0, None), daemon=True).start()
        except Exception as e:
            console.log("Schedule Error", C["red"], False, str(e))

    def repeat_schedule_spam(self, guild_id, channel_id, message, schedule_time, interval_minutes, tokens_list, max_runs=0):
        def run_loop():
            runs = 0
            while not SHOULD_STOP and (max_runs == 0 or runs < max_runs):
                try:
                    now = datetime.now()
                    target = datetime.strptime(schedule_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                    if target < now:
                        target += timedelta(days=1)
                    wait_seconds = (target - now).total_seconds()
                    console.log("Repeat Schedule", C["yellow"], False, f"Next run at {target.strftime('%H:%M')} (in {wait_seconds:.0f}s)")
                    time.sleep(wait_seconds)
                    console.log("Repeat Schedule", C["green"], False, f"Starting scheduled spam (run {runs+1})")
                    for token in tokens_list:
                        threading.Thread(target=self.guild_spammer, args=(token, guild_id, message, 0, 0, None), daemon=True).start()
                    runs += 1
                    if max_runs == 0 or runs < max_runs:
                        time.sleep(interval_minutes * 60)
                except Exception as e:
                    console.log("Repeat Schedule Error", C["red"], False, str(e))
                    time.sleep(60)
        threading.Thread(target=run_loop, daemon=True).start()

    def status_manager(self):
        if not status_rotation:
            return
        def rotate_status():
            while not SHOULD_STOP:
                try:
                    status = random.choice(custom_statuses)
                    for token in tokens:
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
                                console.log("Status Updated", C["green"], f"{token[:15]}...", status)
                                time.sleep(0.3)
                        except Exception as e:
                            console.log("Status Error", C["red"], f"{token[:15]}...", str(e))
                except Exception as e:
                    console.log("Status Manager Error", C["red"], False, str(e))
                time.sleep(status_interval)
        threading.Thread(target=rotate_status, daemon=True).start()

    def advanced_reaction(self, channel_id, target_type, target_value, emoji):
        try:
            if target_type == "message_id":
                def react_to_message(token):
                    try:
                        self._request("PUT", f"{API_BASE}/channels/{channel_id}/messages/{target_value}/reactions/{emoji}/@me",
                                      token, headers=self.headers_full(token), timeout=10)
                        console.log("Reacted", C["green"], f"{token[:15]}...", emoji)
                    except:
                        pass
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(tokens))) as executor:
                    executor.map(react_to_message, tokens)
                return
            # メッセージ取得
            resp = self._request("GET", f"{API_BASE}/channels/{channel_id}/messages",
                                 token=tokens[0], headers=self.headers_full(tokens[0]), params={"limit": 50}, timeout=10)
            if resp.status_code != 200:
                console.log("Failed to fetch messages", C["red"])
                return
            messages = resp.json()
            target_msg = None
            if target_type == "user":
                for msg in messages:
                    if msg["author"]["id"] == target_value:
                        target_msg = msg
                        break
            elif target_type == "keyword":
                for msg in messages:
                    if target_value.lower() in msg.get("content", "").lower():
                        target_msg = msg
                        break
            if not target_msg:
                console.log("No matching message found", C["yellow"])
                return
            msg_id = target_msg["id"]
            def react(token):
                try:
                    self._request("PUT", f"{API_BASE}/channels/{channel_id}/messages/{msg_id}/reactions/{emoji}/@me",
                                  token, headers=self.headers_full(token), timeout=10)
                    console.log("Reacted", C["green"], f"{token[:15]}...", emoji)
                except:
                    pass
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(tokens))) as executor:
                executor.map(react, tokens)
        except Exception as e:
            console.log("Advanced Reaction Error", C["red"], False, str(e))

    def clear_cache(self):
        """キャッシュをクリア（新機能 36）"""
        self.cached_members.clear()
        self.cache_timestamps.clear()
        console.log("Cache Cleared", C["green"], False, "All cached data has been cleared")

    def joiner(self, invite):
        try:
            params = {
                "inputValue": f"https://discord.gg/{invite}",
                "with_counts": "true",
                "with_expiration": "true",
                "with_permissions": "true",
            }
            invite_info = None
            for token in tokens:
                resp = self._request("GET", f"{API_BASE}/invites/{invite}",
                                     token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code == 200:
                    invite_info = resp.json()
                    break
                elif resp.status_code == 404:
                    console.log("Failed", C["red"], "Invalid or expired invite")
                    input()
                    Menu().main_menu()
                    return
                self.human_delay()
            if not invite_info:
                console.log("Failed", C["red"], "Could not retrieve invite info")
                input()
                Menu().main_menu()
                return
            guild_name = invite_info["guild"]["name"]
            guild_id = invite_info["guild"]["id"]
            channel_id = invite_info["channel"]["id"]
            channel_type = invite_info["channel"]["type"]
            join = {
                "location": "Join Guild",
                "location_guild_id": guild_id,
                "location_channel_id": channel_id,
                "location_channel_type": channel_type
            }
            context = base64.b64encode(json.dumps(join).encode()).decode()

            def join_server(token):
                max_retries = joiner_retries
                for attempt in range(max_retries + 1):
                    try:
                        self.human_delay()
                        headers = self.headers_full(token)
                        headers["X-Context-Properties"] = context
                        payload = {"session_id": uuid.uuid4().hex}
                        resp = self._request("POST", f"{API_BASE}/invites/{invite}",
                                             token, headers=headers, json=payload, timeout=10)
                        if resp.status_code == 200:
                            console.log("Joined", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_name)
                            return
                        elif resp.status_code == 400:
                            console.log("Captcha", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", "Captcha detected - skipping this token")
                            return
                        elif resp.status_code == 429:
                            wait = resp.json().get('retry_after', 30) + random.uniform(0, 10)
                            console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Rate limited, waiting {wait:.1f}s")
                            time.sleep(wait)
                            if attempt < max_retries:
                                continue
                            else:
                                return
                        else:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message", "Unknown error"))
                            return
                    except Exception as e:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
                        return
                console.log("Skipped", C["gray"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", "Max retries reached")
            args = [(token,) for token in tokens]
            Menu().run(join_server, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get invite info", e)
            input()
            Menu().main_menu()

    def leaver(self, token, guild):
        try:
            def get_guild_name(guild):
                try:
                    resp = self._request("GET", f"{API_BASE}/guilds/{guild}",
                                         token, headers=self.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        try:
                            return resp.json()["name"]
                        except:
                            return guild
                except:
                    pass
                return guild
            self.guild = get_guild_name(guild)
            payload = {"lurking": False}
            resp = self._request("DELETE", f"{API_BASE}/users/@me/guilds/{guild}",
                                 token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 204:
                console.log("Left", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", self.guild)
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5)
                console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"wait {wait}s")
                time.sleep(wait)
                self.leaver(token, guild)
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

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
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def vc_joiner(self, token, guild, channel, ws):
        try:
            for _ in range(1):
                ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
                ws.send(json.dumps({
                    "op": 2,
                    "d": {
                        "token": token,
                        "properties": {
                            "os": "windows",
                            "browser": "Discord",
                            "device": "desktop"
                        }
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
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

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
            console.log("Onlined", C[color], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def join_voice_channel(self, token, guild_id, channel_id):
        ws = websocket.WebSocket()
        def check_for_guild(token):
            try:
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}",
                                     token, headers=self.headers_full(token), timeout=10)
                return resp.status_code == 200
            except:
                return False
        def check_for_channel(token):
            if check_for_guild(token):
                try:
                    resp = self._request("GET", f"{API_BASE}/channels/{channel_id}",
                                         token, headers=self.headers_full(token), timeout=10)
                    return resp.status_code == 200
                except:
                    pass
            return False
        if check_for_channel(token):
            console.log("Joined", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            self.vc_joiner(token, guild_id, channel_id, ws)
        else:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")

    def soundbord(self, token, channel):
        try:
            sounds = self._request("GET", f"{API_BASE}/soundboard-default-sounds",
                                   token, headers=self.headers_full(token), timeout=10).json()
            self.human_delay()
            while True:
                sound = random.choice(sounds)
                payload = {
                    "emoji_id": None,
                    "emoji_name": sound["emoji_name"],
                    "sound_id": sound["sound_id"],
                }
                resp = self._request("POST", f"{API_BASE}/channels/{channel}/send-soundboard-sound",
                                     token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 204:
                    console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Played {sound['name']}")
                elif resp.status_code == 429:
                    retry_after = resp.json()["retry_after"]
                    console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s")
                    time.sleep(float(retry_after))
                else:
                    break
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def open_dm(self, token, user_id):
        try:
            payload = {"recipients": [f'{user_id}']}
            resp = self._request("POST", f"{API_BASE}/users/@me/channels",
                                 token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json()["id"]
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                return None
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
            return None

    def call_spammer(self, token, user_id):
        try:
            while True:
                channel_id = self.open_dm(token, user_id)
                if not channel_id:
                    return
                json_data = {'recipients': None}
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/call",
                                     token, headers=self.headers_full(token), json=json_data, timeout=10)
                if resp.status_code == 200:
                    console.log("Called", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", user_id)
                    ws = websocket.WebSocket()
                    self.voice_spammer(token, ws, channel_id, channel_id, True)
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                    return
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def dm_spammer(self, token, user_id, message):
        try:
            channel_id = self.open_dm(token, user_id)
            if not channel_id:
                return
            while True:
                payload = {"content": message, "nonce": str(self.nonce())}
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/messages",
                                     token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 200:
                    console.log("Send", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", user_id)
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                    break
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def format_tokens(self):
        try:
            formatted = []
            for token in tokens:
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
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def bio_changer(self, token, bio):
        try:
            payload = {"bio": bio}
            resp = self._request("PATCH", f"{API_BASE}/users/@me/profile",
                                 token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 200:
                console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", bio)
            elif resp.status_code == 429:
                wait = resp.json().get('retry_after', 5)
                console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"wait {wait}s")
                time.sleep(wait)
                self.bio_changer(token, bio)
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def mass_nick(self, token, guild, nick):
        try:
            payload = {"nick": nick}
            resp = self._request("PATCH", f"{API_BASE}/guilds/{guild}/members/@me",
                                 token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 200:
                console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def thread_spammer(self, token, channel_id, name):
        try:
            payload = {
                "name": name,
                "type": 11,
                "auto_archive_duration": 4320,
                "location": "Thread Browser Toolbar",
            }
            while True:
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/threads",
                                     token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 201:
                    console.log("Created", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", name)
                elif resp.status_code == 429:
                    retry_after = resp.json()["retry_after"]
                    if int(retry_after) > 10:
                        console.log("Stopped", C["magenta"], token[:25], f"Ratelimit Exceeded - {int(round(retry_after))}s")
                        break
                    else:
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s")
                        time.sleep(float(retry_after))
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                    break
                self.human_delay()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def typier(self, token, channel_id):
        try:
            while True:
                resp = self._request("POST", f"{API_BASE}/channels/{channel_id}/typing",
                                     token, headers=self.headers_full(token), timeout=10)
                if resp.status_code == 204:
                    console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                    time.sleep(9)
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                    break
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def friender(self, token, nickname):
        try:
            payload = {"username": nickname, "discriminator": None}
            resp = self._request("POST", f"{API_BASE}/users/@me/relationships",
                                 token, headers=self.headers_full(token), json=payload, timeout=10)
            if resp.status_code == 204:
                console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            elif resp.status_code == 400:
                console.log("Captcha", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json())
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def guild_checker(self, guild_id):
        def main_checker(token):
            try:
                while True:
                    resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}",
                                         token, headers=self.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        console.log("Found", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                        break
                    elif resp.status_code == 429:
                        retry_after = resp.json()["retry_after"]
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s")
                        time.sleep(float(retry_after))
                    else:
                        console.log("Not Found", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                        break
            except Exception as e:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
        args = [(token,) for token in tokens]
        Menu().run(main_checker, args)

    def token_checker(self):
        valid = []
        def main(token):
            try:
                while True:
                    resp = self._request("GET", f"{API_BASE}/users/@me/library",
                                         token, headers=self.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        console.log("Valid", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        valid.append(token)
                        break
                    elif resp.status_code == 403:
                        console.log("Locked", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        break
                    elif resp.status_code == 429:
                        retry_after = resp.json()["retry_after"]
                        console.log("Ratelimit", C["pink"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{retry_after}s")
                        time.sleep(retry_after)
                    else:
                        console.log("Invalid", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                        break
            except Exception as e:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
        with open("data/tokens.txt", "r") as f:
            tokens = list({line.strip().replace('"', '') for line in f if line.strip()})
        args = [(token,) for token in tokens]
        Menu().run(main, args)
        with open("data/tokens.txt", "w") as f:
            f.write("\n".join(valid))

    def accept_rules(self, guild_id):
        try:
            valid = []
            for token in tokens:
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/member-verification",
                                     token, headers=self.headers_full(token), timeout=10)
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
                    resp = self._request("PUT", f"{API_BASE}/guilds/{guild_id}/requests/@me",
                                         token, headers=self.headers_full(token), json=payload, timeout=10)
                    if resp.status_code == 201:
                        console.log("Accepted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
            args = [(token,) for token in tokens]
            Menu().run(run_main, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Accept Rules", e)

    def onboard_bypass(self, guild_id):
        try:
            master_token = None
            for token in tokens:
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/onboarding",
                                     token, headers=self.headers_full(token), timeout=10)
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
                resp = self._request("POST", f"{API_BASE}/guilds/{guild_id}/onboarding-responses",
                                     token, headers=self.headers_full(token), json=payload, timeout=10)
                if resp.status_code == 200:
                    console.log("Accepted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
            args = [(token,) for token in tokens]
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
            for token in tokens:
                resp = self._request("GET", f"{API_BASE}/channels/{channel_id}/messages",
                                     token, headers=self.headers_full(token), params=params, timeout=10)
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
                        console.log("Reacted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", selected)
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
            args = [(token,) for token in tokens]
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
            for token in tokens:
                resp = self._request("GET", f"{API_BASE}/channels/{channel_id}/messages",
                                     token, headers=self.headers_full(token), params=params, timeout=10)
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
                        "data": {
                            "component_type": 2,
                            "custom_id": custom_id,
                        },
                        "guild_id": guild_id,
                        "message_flags": 0,
                        "message_id": message_id,
                        "nonce": str(self.nonce()),
                        "session_id": uuid.uuid4().hex,
                        "type": 3,
                    }
                    resp = self._request("POST", f"{API_BASE}/interactions",
                                         token, headers=self.headers_full(token), json=payload, timeout=10)
                    if resp.status_code == 204:
                        console.log("Clicked", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", btn["label"])
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
            args = [(token,) for token in tokens]
            Menu().run(click_button, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get buttons", e)
            input()
            Menu().main_menu()

    def clear_activity(self):
        for token in tokens:
            try:
                ws = ws_pool.get_connection(token)
                if ws:
                    ws.send(json.dumps({
                        "op": 2,
                        "d": {
                            "token": token,
                            "properties": {"os": "Windows", "browser": "Discord"},
                            "presence": {
                                "status": "online",
                                "since": 0,
                                "activities": [],
                                "afk": False
                            }
                        }
                    }))
                self._request("PATCH", f"{API_BASE}/users/@me/settings",
                              token, headers=self.headers_full(token), json={"custom_status": None}, timeout=10)
                console.log("Cleared", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            except Exception as e:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
            self.human_delay()

    def keep_online(self, token):
        while True:
            try:
                ws = ws_pool.get_connection(token)
                if not ws:
                    time.sleep(5)
                    continue
                console.log("Online", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                while True:
                    time.sleep(30)
                    ws.send(json.dumps({"op": 1, "d": None}))
            except Exception as e:
                console.log("Reconnecting", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", str(e))
                time.sleep(5)

    def mass_timeout(self, token, guild_id, days=28):
        try:
            members = []
            after = None
            while True:
                params = {"limit": 1000}
                if after:
                    params["after"] = after
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/members",
                                     token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code != 200:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"メンバー取得失敗 ({resp.status_code})")
                    return
                data = resp.json()
                if not data:
                    break
                members.extend(data)
                after = data[-1]["user"]["id"]
                if len(data) < 1000:
                    break
            if not members:
                console.log("Info", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", "メンバーがいません")
                return
            console.log("Info", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{len(members)}人のメンバーをタイムアウトします (最大{days}日)")
            timeout_until = (datetime.now() + timedelta(days=days)).isoformat()
            def timeout_member(member):
                user_id = member["user"]["id"]
                try:
                    r = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}",
                                      token, headers=self.headers_full(token), json={"communication_disabled_until": timeout_until}, timeout=10)
                    if r.status_code == 200:
                        console.log("Timeout", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']}")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"wait {retry_after:.2f}s")
                        time.sleep(retry_after)
                        r2 = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}",
                                           token, headers=self.headers_full(token), json={"communication_disabled_until": timeout_until}, timeout=10)
                        if r2.status_code == 200:
                            console.log("Timeout", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} (retry)")
                        else:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r2.status_code})")
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']}: {e}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, 10)) as executor:
                executor.map(timeout_member, members)
            console.log("Done", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{len(members)}人のタイムアウト処理完了")
        except Exception as e:
            console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def mass_nick_all(self, token, guild_id, new_nick):
        try:
            members = []
            after = None
            while True:
                params = {"limit": 1000}
                if after:
                    params["after"] = after
                resp = self._request("GET", f"{API_BASE}/guilds/{guild_id}/members",
                                     token, headers=self.headers_full(token), params=params, timeout=10)
                if resp.status_code != 200:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"メンバー取得失敗 ({resp.status_code})")
                    return
                data = resp.json()
                if not data:
                    break
                members.extend(data)
                after = data[-1]["user"]["id"]
                if len(data) < 1000:
                    break
            if not members:
                console.log("Info", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", "メンバーがいません")
                return
            console.log("Info", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{len(members)}人のニックネームを '{new_nick}' に変更します")
            def change_nick(member):
                user_id = member["user"]["id"]
                try:
                    r = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}",
                                      token, headers=self.headers_full(token), json={"nick": new_nick}, timeout=10)
                    if r.status_code == 200:
                        console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} -> {new_nick}")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"wait {retry_after:.2f}s")
                        time.sleep(retry_after)
                        r2 = self._request("PATCH", f"{API_BASE}/guilds/{guild_id}/members/{user_id}",
                                           token, headers=self.headers_full(token), json={"nick": new_nick}, timeout=10)
                        if r2.status_code == 200:
                            console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} -> {new_nick} (retry)")
                        else:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r2.status_code})")
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']}: {e}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, 10)) as executor:
                executor.map(change_nick, members)
            console.log("Done", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{len(members)}人のニックネーム変更完了")
        except Exception as e:
            console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def token_quality_check(self):
        console.clear()
        console.render_ascii()
        console.title("Masumani - Token Quality Check")
        console.log("Checking", C["yellow"], False, "Token quality analysis...")
        results = []
        for token in tokens:
            try:
                resp = self._request("GET", f"{API_BASE}/users/@me",
                                     token, headers=self.headers_minimal(token), timeout=10)
                if resp.status_code == 200:
                    user = resp.json()
                    guild_resp = self._request("GET", f"{API_BASE}/users/@me/guilds",
                                               token, headers=self.headers_minimal(token), timeout=10)
                    guild_count = len(guild_resp.json()) if guild_resp.status_code == 200 else 0
                    lib_resp = self._request("GET", f"{API_BASE}/users/@me/library",
                                             token, headers=self.headers_minimal(token), timeout=10)
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
        console.clear()
        console.render_ascii()
        print(f"\n{C['cyan']}【 Token Quality Report 】{C['white']}\n")
        for res in results:
            if "Valid" in res.get("status", ""):
                status_color = C["green"]
                extra = f" | @{res.get('username','')} | Verified:{res.get('verified',False)} | Guilds:{res.get('guilds',0)} | Locked:{res.get('locked',False)}"
            elif "Invalid" in res.get("status", ""):
                status_color = C["red"]
                extra = ""
            elif "Locked" in res.get("status", ""):
                status_color = C["yellow"]
                extra = ""
            else:
                status_color = C["gray"]
                extra = ""
            console.log(res["status"], status_color, res["token"], extra)
        input(f"\n   {console.background}~/> press enter to continue ")
        Menu().main_menu()


# ============================================================================
#  Menu クラス（全機能メニュー）
# ============================================================================
class Menu:
    def __init__(self):
        global global_raider
        if not color:
            self.background = C["light_blue"]
        else:
            self.background = C[color]
        if global_raider is None:
            self.raider = Raider()
            global_raider = self.raider
        else:
            self.raider = global_raider
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
        if choice.startswith('0') and len(choice) == 2:
            choice = str(int(choice))
        if choice.lower() in self.options:
            console.render_ascii()
            self.options[choice.lower()]()
        else:
            self.main_menu()

    def run(self, func, args):
        threads = []
        console.clear()
        console.render_ascii()
        for idx, arg in enumerate(args):
            thread = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    def run_spammer(self, func, args):
        global SHOULD_STOP
        SHOULD_STOP = False
        console.clear()
        console.render_ascii()
        if not args:
            console.log("Error", C["red"], False, "実行するスレッドがありません。")
            input("Press Enter to continue...")
            self.main_menu()
            return
        
        def input_listener():
            global SHOULD_STOP
            while True:
                try:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        cmd = sys.stdin.readline().strip()
                        if cmd and cmd.lower() == "end":
                            SHOULD_STOP = True
                            console.log("Stopping", C["red"], False, "Received stop command...")
                            break
                except:
                    break
        
        listener = threading.Thread(target=input_listener, daemon=True)
        listener.start()
        
        threads = []
        for idx, arg in enumerate(args):
            t = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(t)
            t.start()
        
        if not threads:
            console.log("Error", C["red"], False, "スレッドが起動しませんでした。")
            SHOULD_STOP = True
            input("Press Enter to continue...")
            self.main_menu()
            return
        
        while any(t.is_alive() for t in threads):
            time.sleep(0.3)
            if SHOULD_STOP:
                break
        
        SHOULD_STOP = True
        time.sleep(0.3)
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    def get_message_from_file_or_input(self):
        msg_dir = "data/messages"
        if not os.path.exists(msg_dir):
            os.makedirs(msg_dir)
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
                    msg = f.read().strip()
                console.log("Loaded", C["green"], False, f"メッセージ '{selected}' を読み込みました")
                return msg
            else:
                console.log("Info", C["yellow"], False, "新規メッセージを入力します")
        else:
            console.log("Info", C["yellow"], False, "保存済みメッセージはありません。新規入力します。")
        msg = input(console.prompt("メッセージ (空でキャンセル)"))
        if msg == "":
            return None
        save = input(console.prompt("このメッセージを保存しますか？ (y/n)"))
        if save.lower().startswith('y'):
            fname = input(console.prompt("ファイル名 (例: spam1.txt)"))
            if not fname.endswith('.txt'):
                fname += '.txt'
            with open(os.path.join(msg_dir, fname), 'w', encoding='utf-8') as f:
                f.write(msg)
            console.log("Saved", C["green"], False, f"'{fname}' に保存しました")
        return msg

    @wrapper
    def spammer(self):
        console.title("Masumani - Spammer")
        console.log("Info", C["yellow"], False, "事前に [04] Token Checker を推奨します。")
        message = self.get_message_from_file_or_input()
        if message is None:
            self.main_menu()
        use_guild = input(console.prompt("Use Guild ID for all channels? (y/n)"))
        if use_guild.lower().startswith('y'):
            guild_id = input(console.prompt("Guild ID"))
            if not guild_id:
                self.main_menu()
            console.log("Fetching channel list...", C["yellow"])
            found = False
            for token in tokens:
                try:
                    resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/channels",
                                                token, headers=self.raider.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text_channels = [c for c in channels if c.get('type') == 0]
                        console.log("Found", C["green"], False, f"{len(text_channels)} text channels")
                        for ch in text_channels[:15]:
                            console.log("Channel", C["cyan"], False, f"{ch['id']} - #{ch.get('name', 'No name')}")
                        if len(text_channels) > 15:
                            console.log("Info", C["gray"], False, f"... and {len(text_channels)-15} more")
                        found = True
                        break
                    else:
                        console.log("Failed", C["red"], False, f"Token {token[:15]}... failed ({resp.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], False, f"Token {token[:15]}... error: {e}")
            if not found:
                console.log("Failed", C["red"], "All tokens failed to fetch channels.")
                input("Press Enter to continue...")
                self.main_menu()
            console.log("Pre-fetching members for random mentions...", C["yellow"])
            first_text_channel = None
            for token in tokens:
                try:
                    resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/channels",
                                                token, headers=self.raider.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text_channels = [c for c in channels if c.get('type') == 0]
                        if text_channels:
                            first_text_channel = text_channels[0]['id']
                            break
                except:
                    pass
            if first_text_channel:
                self.raider.member_scrape(guild_id, first_text_channel)
            else:
                console.log("Warning", C["yellow"], False, "No text channel found, skipping member pre-fetch.")
            add_poll = input(console.prompt("投票を追加しますか？ (y/n)"))
            poll_data = None
            if add_poll.lower().startswith('y'):
                poll_data = {
                    "question": "Raid by Masumani",
                    "options": ["join", "now", "discord.gg/", "msmn"]
                }
                console.log("Poll", C["green"], False, "質問: 'Raid by Masumani', 選択肢: join, now, discord.gg/, msmn")
            pings = int(input(console.prompt("Pings amount (0推奨)")) or "0")
            delay = float(input(console.prompt("Delay between cycles (秒, 推奨: 0〜5)")) or "0")
            valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "対象サーバーに参加しているトークンがありません。")
                input("Press Enter to continue...")
                self.main_menu()
            console.log("Info", C["green"], False, f"{len(valid_tokens)}/{len(tokens)} 個のトークンが参加しています。")
            console.clear()
            console.render_ascii()
            args = [(token, guild_id, message, pings, delay, poll_data) for token in valid_tokens]
            self.run_spammer(self.raider.guild_spammer, args)
        else:
            link = input(console.prompt("Channel LINK"))
            if link == "" or not link.startswith("https://"):
                self.main_menu()
            guild_id = link.split("/")[4]
            channel_id = link.split("/")[5]
            massping = input(console.prompt("Massping", True))
            random_str = input(console.prompt("Random String", True))
            delay_input = input(console.prompt("Delay (seconds)"))
            delay = None
            if delay_input != "":
                delay = float(delay_input)
            ping_count = None
            if "y" in massping:
                console.log("Scraping users", self.background, False, "this may take a while...")
                self.raider.member_scrape(guild_id, channel_id)
                count_str = input(console.prompt("Pings Amount"))
                if count_str == "":
                    self.main_menu()
                ping_count = int(count_str)
            add_poll = input(console.prompt("投票を追加しますか？ (y/n)"))
            poll_data = None
            if add_poll.lower().startswith('y'):
                poll_data = {
                    "question": "Raid by Masumani",
                    "options": ["join", "now", "discord.gg/", "msmn"]
                }
                console.log("Poll", C["green"], False, "質問: 'Raid by Masumani', 選択肢: join, now, discord.gg/, msmn")
            valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "対象サーバーに参加しているトークンがありません。")
                input("Press Enter to continue...")
                self.main_menu()
            console.log("Info", C["green"], False, f"{len(valid_tokens)}/{len(tokens)} 個のトークンが参加しています。")
            args = [
                (token, channel_id, message, guild_id, "y" in massping, ping_count, "y" in random_str, delay, poll_data)
                for token in valid_tokens
            ]
            self.run_spammer(self.raider.spammer, args)

    @wrapper
    def poll_spammer(self):
        console.title("Masumani - Poll Spammer")
        console.log("Info", C["yellow"], False, "事前に [04] Token Checker を推奨します。")
        use_guild = input(console.prompt("Use Guild ID for all channels? (y/n)"))
        if use_guild.lower().startswith('y'):
            guild_id = input(console.prompt("Guild ID"))
            if not guild_id:
                self.main_menu()
            console.log("Fetching channel list...", C["yellow"])
            for token in tokens:
                try:
                    resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/channels",
                                                token, headers=self.raider.headers_full(token), timeout=10)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text_channels = [c for c in channels if c.get('type') == 0]
                        console.log("Found", C["green"], False, f"{len(text_channels)} text channels")
                        for ch in text_channels[:10]:
                            console.log("Channel", C["cyan"], False, f"{ch['id']} - #{ch.get('name', 'No name')}")
                        if len(text_channels) > 10:
                            console.log("Info", C["gray"], False, f"... and {len(text_channels)-10} more")
                        break
                except:
                    pass
            question = input(console.prompt("質問 (デフォルト: Raid by Masumani)"))
            if question == "":
                question = "Raid by Masumani"
            options_input = input(console.prompt("選択肢 (カンマ区切り, デフォルト: join,now,discord.gg/,msmn)"))
            if options_input == "":
                options = ["join", "now", "discord.gg/", "msmn"]
            else:
                options = [opt.strip() for opt in options_input.split(",") if opt.strip()]
            poll_data = {
                "question": question,
                "options": options
            }
            pings = 0
            delay = float(input(console.prompt("Delay between cycles (秒, 推奨: 3〜5)")) or "3")
            message = ""
            valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "対象サーバーに参加しているトークンがありません。")
                input("Press Enter to continue...")
                self.main_menu()
            console.clear()
            console.render_ascii()
            args = [(token, guild_id, message, pings, delay, poll_data) for token in valid_tokens]
            self.run_spammer(self.raider.guild_spammer, args)
        else:
            link = input(console.prompt("Channel LINK"))
            if link == "" or not link.startswith("https://"):
                self.main_menu()
            channel_id = link.split("/")[5]
            question = input(console.prompt("質問 (デフォルト: Raid by Masumani)"))
            if question == "":
                question = "Raid by Masumani"
            options_input = input(console.prompt("選択肢 (カンマ区切り, デフォルト: join,now,discord.gg/,msmn)"))
            if options_input == "":
                options = ["join", "now", "discord.gg/", "msmn"]
            else:
                options = [opt.strip() for opt in options_input.split(",") if opt.strip()]
            poll_data = {
                "question": question,
                "options": options
            }
            guild_id = link.split("/")[4]
            valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "対象サーバーに参加しているトークンがありません。")
                input("Press Enter to continue...")
                self.main_menu()
            args = [(token, channel_id, "", None, False, None, False, None, poll_data) for token in valid_tokens]
            self.run_spammer(self.raider.spammer, args)

    @wrapper
    def schedule_spam(self):
        console.title("Masumani - Schedule Spam")
        guild_id = input(console.prompt("Guild ID"))
        if not guild_id:
            self.main_menu()
        channel_id = input(console.prompt("Channel ID (or leave empty for all channels)"))
        if channel_id == "":
            channel_id = None
        message = input(console.prompt("Message"))
        if not message:
            self.main_menu()
        schedule_time = input(console.prompt("Schedule time (HH:MM)"))
        if not re.match(r"^\d{2}:\d{2}$", schedule_time):
            console.log("Invalid time format", C["red"])
            input("Press Enter...")
            self.main_menu()
        valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
        if not valid_tokens:
            console.log("Failed", C["red"], "No valid tokens in guild")
            input("Press Enter...")
            self.main_menu()
        threading.Thread(target=self.raider.schedule_spam, args=(guild_id, channel_id, message, schedule_time, valid_tokens), daemon=True).start()
        console.log("Schedule set", C["green"], False, f"Spam will start at {schedule_time}")
        input("Press Enter to continue...")
        self.main_menu()

    @wrapper
    def repeat_schedule(self):
        console.title("Masumani - Repeat Schedule")
        guild_id = input(console.prompt("Guild ID"))
        if not guild_id:
            self.main_menu()
        channel_id = input(console.prompt("Channel ID (or leave empty for all channels)"))
        if channel_id == "":
            channel_id = None
        message = input(console.prompt("Message"))
        if not message:
            self.main_menu()
        schedule_time = input(console.prompt("Schedule time (HH:MM)"))
        if not re.match(r"^\d{2}:\d{2}$", schedule_time):
            console.log("Invalid time format", C["red"])
            input("Press Enter...")
            self.main_menu()
        interval = int(input(console.prompt("Interval between runs (minutes)")) or "60")
        max_runs = int(input(console.prompt("Max runs (0 for infinite)")) or "0")
        valid_tokens = self.raider.get_valid_tokens_for_guild(guild_id)
        if not valid_tokens:
            console.log("Failed", C["red"], "No valid tokens in guild")
            input("Press Enter...")
            self.main_menu()
        self.raider.repeat_schedule_spam(guild_id, channel_id, message, schedule_time, interval, valid_tokens, max_runs)
        console.log("Repeat schedule started", C["green"])
        input("Press Enter to continue...")
        self.main_menu()

    @wrapper
    def status_manager(self):
        console.title("Masumani - Status Manager")
        if self.raider.status_thread_running:
            console.log("Status manager already running", C["yellow"])
            input("Press Enter...")
            self.main_menu()
            return
        self.raider.status_manager()
        self.raider.status_thread_running = True
        console.log("Status manager started", C["green"])
        input("Press Enter to continue...")
        self.main_menu()

    @wrapper
    def advanced_reaction(self):
        console.title("Masumani - Advanced Reaction")
        channel_id = input(console.prompt("Channel ID"))
        if not channel_id:
            self.main_menu()
        target_type = input(console.prompt("Target type (user/keyword/message_id)"))
        target_value = input(console.prompt("Target value (user_id/keyword/message_id)"))
        emoji = input(console.prompt("Emoji (name or :emoji:)"))
        if not all([channel_id, target_type, target_value, emoji]):
            console.log("Missing parameters", C["red"])
            input("Press Enter...")
            self.main_menu()
        self.raider.advanced_reaction(channel_id, target_type, target_value, emoji)
        console.log("Advanced reaction triggered", C["green"])
        input("Press Enter to continue...")
        self.main_menu()

    @wrapper
    def cache_clear(self):
        console.title("Masumani - Cache Clear")
        self.raider.clear_cache()
        input("Press Enter to continue...")
        self.main_menu()

    @wrapper
    def joiner(self):
        console.title("Masumani - Joiner")
        invite = input(console.prompt("Invite"))
        if invite == "":
            self.main_menu()
        invite = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
        self.raider.joiner(invite)

    @wrapper
    def leaver(self):
        console.title("Masumani - Leaver")
        guild = input(console.prompt("Guild ID"))
        if guild == "":
            self.main_menu()
        args = [(token, guild) for token in tokens]
        self.run(self.raider.leaver, args)

    @wrapper
    def clear_status(self):
        console.title("Masumani - Clear Status")
        self.run(self.raider.clear_activity, [()])

    def onliner(self):
        console.title("Masumani - Onliner")
        args = [(token,) for token in tokens]
        self.run(self.raider.keep_online, args)

    @wrapper
    def mass_timeout(self):
        console.title("Masumani - Mass Timeout")
        guild_id = input(console.prompt("Guild ID"))
        if not guild_id:
            self.main_menu()
        days = int(input(console.prompt("タイムアウト日数 (1-28, デフォルト: 28)")) or "28")
        days = max(1, min(28, days))
        console.log("Info", C["yellow"], False, "権限のあるトークンを探しています...")
        valid_tokens = []
        for token in tokens:
            try:
                resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/members/@me",
                                            token, headers=self.raider.headers_full(token), timeout=10)
                if resp.status_code == 200:
                    valid_tokens.append(token)
                    console.log("Token", C["green"], False, f"{token[:15]}... 有効")
                else:
                    console.log("Token", C["red"], False, f"{token[:15]}... 無効 ({resp.status_code})")
            except:
                pass
        if not valid_tokens:
            console.log("Failed", C["red"], "有効なトークンがありません。")
            input("Press Enter to continue...")
            self.main_menu()
        console.log("Info", C["yellow"], False, f"{len(valid_tokens)}個のトークンでタイムアウトを実行します")
        args = [(token, guild_id, days) for token in valid_tokens]
        self.run(self.raider.mass_timeout, args)

    @wrapper
    def mass_nick_all(self):
        console.title("Masumani - Mass Nick All")
        guild_id = input(console.prompt("Guild ID"))
        if not guild_id:
            self.main_menu()
        new_nick = input(console.prompt("新しいニックネーム"))
        if not new_nick:
            self.main_menu()
        console.log("Info", C["yellow"], False, "権限のあるトークンを探しています...")
        valid_tokens = []
        for token in tokens:
            try:
                resp = self.raider._request("GET", f"{API_BASE}/guilds/{guild_id}/members/@me",
                                            token, headers=self.raider.headers_full(token), timeout=10)
                if resp.status_code == 200:
                    valid_tokens.append(token)
                    console.log("Token", C["green"], False, f"{token[:15]}... 有効")
                else:
                    console.log("Token", C["red"], False, f"{token[:15]}... 無効 ({resp.status_code})")
            except:
                pass
        if not valid_tokens:
            console.log("Failed", C["red"], "有効なトークンがありません。")
            input("Press Enter to continue...")
            self.main_menu()
        console.log("Info", C["yellow"], False, f"{len(valid_tokens)}個のトークンでニックネーム変更を実行します")
        args = [(token, guild_id, new_nick) for token in valid_tokens]
        self.run(self.raider.mass_nick_all, args)

    @wrapper
    def token_quality(self):
        console.title("Masumani - Token Quality")
        self.raider.token_quality_check()

    @wrapper
    def dm_spam(self):
        console.title("Masumani - Dm Spammer")
        user_id = input(console.prompt("User ID"))
        if user_id == "":
            self.main_menu()
        message = input(console.prompt("Message"))
        if message == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        args = [(token, user_id, message) for token in tokens]
        self.run(self.raider.dm_spammer, args)

    @wrapper
    def soundbord(self):
        console.title("Masumani - Soundboard Spam")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        channel = Link.split("/")[5]
        guild = Link.split("/")[4]
        console.clear()
        console.render_ascii()
        for token in tokens:
            threading.Thread(target=self.raider.join_voice_channel, args=(token, guild, channel), daemon=True).start()
            threading.Thread(target=self.raider.soundbord, args=(token, channel), daemon=True).start()

    @wrapper
    def friender(self):
        console.title("Masumani - Friender")
        nickname = input(console.prompt("Nick"))
        if nickname == "":
            self.main_menu()
        args = [(token, nickname) for token in tokens]
        self.run(self.raider.friender, args)

    @wrapper
    def caller(self):
        console.title("Masumani - Call Spammer")
        user_id = input(console.prompt("User ID"))
        if user_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        args = [(token, user_id) for token in tokens]
        self.run(self.raider.call_spammer, args)

    @wrapper
    def typier(self):
        console.title("Masumani - Typer")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        channelid = Link.split("/")[5]
        args = [(token, channelid) for token in tokens]
        self.run(self.raider.typier, args)

    @wrapper
    def nick_changer(self):
        console.title("Masumani - Nickname Changer")
        nick = input(console.prompt("Nick"))
        if nick == "" or len(nick) > 32:
            self.main_menu()
        guild = input(console.prompt("Guild ID"))
        if guild == "":
            self.main_menu()
        args = [(token, guild, nick) for token in tokens]
        self.run(self.raider.mass_nick, args)

    @wrapper
    def voice_joiner(self):
        console.title("Masumani - Voice Joiner")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        guild = Link.split("/")[4]
        channel = Link.split("/")[5]
        args = [(token, guild, channel) for token in tokens]
        self.run(self.raider.join_voice_channel, args)

    @wrapper
    def Thread_Spammer(self):
        console.title("Masumani - Thread Spammer")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        name = input(console.prompt("Name"))
        if name == "":
            self.main_menu()
        channel_id = Link.split("/")[5]
        args = [(token, channel_id, name) for token in tokens]
        self.run(self.raider.thread_spammer, args)

    @wrapper
    def reactor(self):
        console.title("Masumani - Reactor")
        Link = input(console.prompt("Message Link"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        channel_id = Link.split("/")[5]
        message_id = Link.split("/")[6]
        console.clear()
        console.render_ascii()
        self.raider.reactor_main(channel_id, message_id)

    @wrapper
    def button(self):
        console.title("Masumani - Button Click")
        Link = input(console.prompt("Message Link"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
            return
        guild_id = Link.split("/")[4]
        channel_id = Link.split("/")[5]
        message_id = Link.split("/")[6]
        console.clear()
        console.render_ascii()
        self.raider.button_bypass(channel_id, message_id, guild_id)

    @wrapper
    def accept(self):
        console.title("Masumani - Accept Rules")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        self.raider.accept_rules(guild_id)

    @wrapper
    def guild(self):
        console.title("Masumani - Guild Checker")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        self.raider.guild_checker(guild_id)

    @wrapper
    def bio_changer(self):
        console.title("Masumani - Bio Changer")
        bio = input(console.prompt("Bio"))
        if bio == "":
            self.main_menu()
        args = [(token, bio) for token in tokens]
        self.run(self.raider.bio_changer, args)

    @wrapper
    def onboard(self):
        console.title("Masumani - Onboarding Bypass")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        self.raider.onboard_bypass(guild_id)

    def checker(self):
        console.title("Masumani - Checker")
        self.raider.token_checker()

    def formatter(self):
        console.title("Masumani - Formatter")
        self.run(self.raider.format_tokens, [()])

    @wrapper
    def credit(self):
        credits_lines = [
            "Special Thanks to",
            "Coder: Tips",
            "Scraper: Aniell4",
            "Original Owner of Helium/Masumani: Ekkore",
            "And last but not least, you! Without you, this project wouldn't be possible.",
        ]
        for line in credits_lines:
            centered_line = line.center(os.get_terminal_size().columns)
            print(f"{Fore.RESET}{self.background}{centered_line}{Fore.RESET}")
        input("\n ~/> press enter to continue ")
        self.main_menu()

    def show_help(self):
        console.clear()
        console.render_ascii()
        help_text = f"""
{C['cyan']}【 Masumani ヘルプ 】{C['white']}

{C['green']}基本操作:{C['white']}
  番号を入力して Enter で実行します。
  h または H でヘルプを表示します。
  ~ でクレジットを表示します。

{C['yellow']}機能一覧:{C['white']}
  {C['light_blue']}01{C['white']} Joiner          : サーバー参加（キャプチャ対策強化）
  {C['light_blue']}02{C['white']} Leaver          : サーバー退出
  {C['light_blue']}03{C['white']} Spammer         : メッセージスパム（永久ループ・投票対応）
  {C['light_blue']}04{C['white']} Token Checker   : トークン有効性チェック
  {C['light_blue']}05{C['white']} Emoji Reaction  : リアクション
  {C['light_blue']}06{C['white']} Clear Status    : ステータス消去
  {C['light_blue']}07{C['white']} Token Formatter : トークン整形
  {C['light_blue']}08{C['white']} Button Click    : ボタンクリック
  {C['light_blue']}09{C['white']} Accept Rules    : ルール承認
  {C['light_blue']}10{C['white']} Guild Check     : ギルド参加チェック
  {C['light_blue']}11{C['white']} Friend Spam     : フレンドリクエスト
  {C['light_blue']}13{C['white']} Onliner         : オンライン維持
  {C['light_blue']}14{C['white']} Voice Raper     : サウンドボードスパム
  {C['light_blue']}15{C['white']} Change Nick     : ニック変更
  {C['light_blue']}16{C['white']} Thread Spammer  : スレッド作成
  {C['light_blue']}17{C['white']} Typer           : 入力中偽装
  {C['light_blue']}19{C['white']} Call Spammer    : 通話スパム
  {C['light_blue']}20{C['white']} Bio Change      : バイオ変更
  {C['light_blue']}21{C['white']} Voice Joiner    : ボイス参加
  {C['light_blue']}22{C['white']} Onboard Bypass  : オンボーディング回避
  {C['light_blue']}23{C['white']} DM Spammer      : DMスパム
  {C['light_blue']}25{C['white']} Poll Spammer    : 投票スパム
  {C['light_blue']}26{C['white']} Mass Timeout    : 一斉タイムアウト
  {C['light_blue']}27{C['white']} Mass Nick All   : 一斉ニック変更
  {C['light_blue']}28{C['white']} Schedule Spam   : 予約スパム
  {C['light_blue']}32{C['white']} Token Quality   : トークン品質レポート
  {C['light_blue']}33{C['white']} Status Manager  : ステータス自動切替
  {C['light_blue']}34{C['white']} Adv Reaction    : 高度なリアクション
  {C['light_blue']}35{C['white']} Repeat Schedule : 繰り返し予約スパム
  {C['light_blue']}36{C['white']} Cache Clear     : キャッシュクリア

{C['yellow']}【 コツ 】{C['white']}
  1. プロキシは必ず設定（data/proxies.txt）
  2. 遅延は config.json で調整
  3. @everyone は極力避ける
  4. 古いアカウントほど制限が緩い

{C['red']}注意:{C['white']}
  自己ボット（ユーザートークン）を使用。利用規約に違反します。
        """
        print(help_text)
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    @wrapper
    def exits(self):
        choice = input(console.prompt("Are you sure you want to quit", ask=True))
        if choice.lower().startswith("y"):
            os._exit(0)
        else:
            self.main_menu()

if __name__ == "__main__":
    Menu().main_menu()
    # 終了時にWebSocketプールをクリーンアップ
    try:
        ws_pool.close_all()
    except:
        pass
