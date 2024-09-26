import requests
import json
import time
import random
from setproctitle import setproctitle
from convert import get
from colorama import Fore, Style, init
import crayons
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse
import os
import socket

url = "https://notpx.app/api/v1"

init(autoreset=True)
setproctitle("notpixel")

image = get("")

c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

def log_message(log_type, message):
    if log_type == "INFO":
        info_color = Fore.BLUE
    elif log_type == "ERROR":
        info_color = Fore.RED
    else:
        info_color = Style.RESET_ALL
    color_reset = Style.RESET_ALL
    formatted_message = f"{info_color}| {log_type} |{color_reset} {message}"
    print(formatted_message)

def resolve_hostname_to_ip(hostname):
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        return None

def get_country_from_ip(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = response.json()
        if data['status'] == 'success':
            return data['countryCode']
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

def load_proxies_from_file(filename='proxy.txt'):
    if not os.path.exists(filename):
        log_message("INFO", "File proxy.txt tidak ditemukan. Melanjutkan tanpa proxy.")
        return []
    with open(filename, 'r') as file:
        proxies = [line.strip() for line in file if line.strip()]
    return proxies

def parse_proxy(proxy_str):
    proxy_type = 'http'
    for pt in ['socks5', 'socks4', 'https', 'http']:
        if proxy_str.startswith(f'{pt}://'):
            proxy_type = pt
            proxy_str = proxy_str[len(f'{pt}://'):]
            break

    ip_address = None
    formatted_proxy = None

    formats_to_try = [
        lambda s: s.split('@') if '@' in s else None,
        lambda s: s.split(':') if len(s.split(':')) == 4 else None,
        lambda s: s.split('@')[::-1] if '@' in s else None,
        lambda s: s.split(':') if len(s.split(':')) == 4 else None,
    ]

    for format_func in formats_to_try:
        result = format_func(proxy_str)
        if result:
            if isinstance(result, list) and len(result) == 2:
                user_info = result[0]
                proxy_details = result[1]
                if ':' in proxy_details:
                    proxy_ip_or_hostname, port = proxy_details.split(':', 1)
                else:
                    continue
            elif isinstance(result, list) and len(result) == 4:
                if result[0].replace('.', '').isdigit() or resolve_hostname_to_ip(result[0]):
                    proxy_ip_or_hostname = result[0]
                    port = result[1]
                    user_info = f"{result[2]}:{result[3]}"
                else:
                    user_info = f"{result[0]}:{result[1]}"
                    proxy_ip_or_hostname = result[2]
                    port = result[3]
            else:
                continue

            if not proxy_ip_or_hostname.replace('.', '').isdigit():
                ip_address = resolve_hostname_to_ip(proxy_ip_or_hostname)
            else:
                ip_address = proxy_ip_or_hostname

            if ip_address:
                if user_info:
                    formatted_proxy = f"{proxy_type}://{user_info}@{proxy_ip_or_hostname}:{port}"
                else:
                    formatted_proxy = f"{proxy_type}://{proxy_ip_or_hostname}:{port}"
                return formatted_proxy, ip_address
            else:
                continue

    return None, None

def get_session_with_proxy_and_retries(proxy=None, retries=3, backoff_factor=0.3,
                                       status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
    return session

def get_color(pixel, header, session):
    try:
        response = session.get(f"{url}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 401:
            return -1
        return response.json()['pixel']['color']
    except Exception:
        return "#000000"

def claim(header, session):
    log_message("INFO", "Claim Resources | Process")
    try:
        response = session.get(f"{url}/mining/claim", headers=header, timeout=10)
        if response.status_code == 200:
            log_message("INFO", "Claim Resources | Success!!")
        else:
            return "Failed"
    except Exception:
        return "Failed"

def get_pixel(x, y):
    return y * 1000 + x + 1

def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

def get_canvas_pos(x, y):
    return get_pixel(start_x + x - 1, start_y + y - 1)

start_x = 893
start_y = 818

def paint(canvas_pos, color, header, session):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }
    try:
        response = session.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        x, y = get_pos(canvas_pos, 1000)
        if response.status_code == 400:
            log_message("ERROR", "Print | Out of Energy")
            return False
        if response.status_code == 401:
            return -1
        log_message("INFO", f"Print: {x},{y} | Success!!")
        return True
    except Exception as e:
        log_message("ERROR", f"Print | Failed: {e}")
        return False

def extract_username_from_initdata(init_data):
    decoded_data = urllib.parse.unquote(init_data)
    username_start = decoded_data.find('"username":"') + len('"username":"')
    username_end = decoded_data.find('"', username_start)
    if username_start != -1 and username_end != -1:
        return decoded_data[username_start:username_end]
    return "Unknown"

def load_accounts_from_file(filename):
    if not os.path.exists(filename):
        log_message("ERROR", f"File {filename} tidak ditemukan.")
        return []
    with open(filename, 'r') as file:
        accounts = [f"initData {line.strip()}" for line in file if line.strip()]
    return accounts

def fetch_mining_data(header, session):
    try:
        response = session.get(f"{url}/mining/status", headers=header, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_balance = data.get('userBalance', 'Unknown')
            log_message("INFO", f"Balance | {user_balance}")
        else:
            log_message("ERROR", f"Data Mining | Failed: {response.status_code}")
            return "Failed"
    except Exception:
        return "Failed"

def pause_and_wait():
    wait_time = random.randint(2400, 3600)
    for remaining in range(wait_time, 0, -1):
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"| INFO | Waiting Full Energy {hours:02}:{minutes:02}:{seconds:02}...", end='\r')
        time.sleep(1)

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(crayons.cyan('=============================================='))
    print(crayons.cyan('         NOT PIXEL BOT | AIRDROP ASC         '))
    print(crayons.cyan('=============================================='))
    print(crayons.cyan('Telegram Channel : @airdropasc               '))
    print(crayons.cyan('Telegram Group   : @autosultan_group         '))
    print(crayons.cyan('=============================================='))

def main(auth, account, proxy):
    headers = {'authorization': auth}
    session = get_session_with_proxy_and_retries(proxy)
    try:
        fetch_status = fetch_mining_data(headers, session)
        if fetch_status == "Failed":
            log_message("ERROR", "Data Mining | Failed")
        claim_status = claim(headers, session)
        if claim_status == "Failed":
            log_message("ERROR", "Claim Resources | Failed")
        size_y = len(image)
        size_x = len(image[0]) if size_y > 0 else 0
        size = size_y * size_x
        order = list(range(size))
        random.shuffle(order)
        for pos_image in order:
            x, y = get_pos(pos_image, size_x)
            time.sleep(0.05 + random.uniform(0.01, 0.1))
            try:
                color = get_color(get_canvas_pos(x, y), headers, session)
                if color == -1:
                    log_message("ERROR", "Token Invalid - Please Update Token")
                    break
                if image[y][x] == ' ' or color == c[image[y][x]]:
                    log_message("INFO", f"Skip: {start_x + x - 1},{start_y + y - 1} | Skip")
                    continue
                result = paint(get_canvas_pos(x, y), c[image[y][x]], headers, session)
                if result == -1:
                    log_message("ERROR", "Token Invalid - Please Update Token")
                    break
                elif result:
                    continue
                else:
                    break
            except IndexError:
                log_message("ERROR", f"Index Error | pos_image: {pos_image}, y: {y}, x: {x}")
    except Exception as e:
        log_message("ERROR", f"Network Error | Account {account}: {e}")

def process_accounts(accounts, proxies):
    first_account_start_time = datetime.now()
    for idx, account in enumerate(accounts):
        username = extract_username_from_initdata(account)
        log_message("INFO", f"Account | {username}")
        if proxies:
            proxy_str = proxies[idx % len(proxies)]
            formatted_proxy, ip_address = parse_proxy(proxy_str)
            if formatted_proxy:
                country_code = get_country_from_ip(ip_address)
                log_message("INFO", "Login With Proxy | Success!!")
                log_message("INFO", f"Log Proxy | IP: {ip_address} Country: {country_code}")
                main(account, account, formatted_proxy)
            else:
                main(account, account, None)
        else:
            main(account, account, None)
    time_elapsed = datetime.now() - first_account_start_time
    time_to_wait = timedelta(hours=1) - time_elapsed
    if time_to_wait.total_seconds() > 0:
        pause_and_wait()
    else:
        log_message("INFO", "No Pause Needed | Total processing time exceeded 1 hour")

def main_loop():
    while True:
        process_accounts(accounts, proxies)

if __name__ == "__main__":
    print_banner()
    accounts = load_accounts_from_file('data.txt')
    if not accounts:
        log_message("ERROR", "Tidak ada akun yang ditemukan. Pastikan file data.txt berisi akun.")
        exit(1)
    proxies = load_proxies_from_file('proxy.txt')
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
        exit(0)
    except Exception as e:
        log_message("ERROR", f"Terjadi kesalahan yang tidak terduga: {e}")
