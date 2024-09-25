import os
import requests
import json
import time
import random
import config
from data import accounts, load_proxies  
from setproctitle import setproctitle
from config import url, print_block  
from convert import get
import crayons  

setproctitle("notpixel")

image = get("image.png")  

c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print(crayons.cyan('=============================================='))
    print(crayons.cyan('         NOT PIXEL BOT | AIRDROP ASC         '))
    print(crayons.cyan('=============================================='))
    print(crayons.cyan('Telegram Channel : @airdropasc               '))
    print(crayons.cyan('Telegram Group   : @autosultan_group         '))
    print(crayons.cyan('=============================================='))

def get_color(pixel, header):
    query = requests.get(f"{url}/image/get/{str(pixel)}", headers=header)
    if query.status_code == 401:
        return -1
    if query.status_code != 200:
        print(f"ERROR | Unable to get color for pixel {pixel}. Status code: {query.status_code}, Response: {query.text}")
        return -1
    try:
        return query.json()['pixel']['color']
    except (KeyError, json.JSONDecodeError):
        print(f"ERROR | JSON decode error for pixel {pixel}. Response: {query.text}")
        return "#000000"

def claim(header):
    response = requests.get(f"{url}/mining/claim", headers=header)
    if response.status_code == 200:
        print("INFO | Claim successful.")
        return True  
    else:
        print("ERROR | Claim failed.")  # Changed error message
        return False

def get_pixel(x, y):
    return y * 1000 + x + 1

def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

def get_canvas_pos(x, y):
    return get_pixel(print_block['start_x'] + x - 1, print_block['start_y'] + y - 1)

def paint(canvas_pos, color, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }
    response = requests.post(f"{url}/repaint/start", data=json.dumps(data), headers=header)
    x, y = get_pos(canvas_pos, 1000)

    if response.status_code == 400:
        print(crayons.red("INFO | Out of Energy"))
        return False  

    if response.status_code == 401:
        return -1

    print(f"INFO | Paint: {x},{y} | " + crayons.green("Success!!"))
    return True

def check_account_data(account):
    """ Check if account contains 'user=' or 'query=' in the token """
    return "user=" in account or "query=" in account

def extract_ip(proxy_url):
    """ Extract the IP from the proxy URL, accommodating different formats. """
    try:
        if '@' in proxy_url:
            hostname = proxy_url.split('@')[1].split(':')[0]  
            return hostname
        elif '://' in proxy_url:
            return proxy_url.split('://')[1].split('@')[-1].split(':')[0]  
        else:
            return proxy_url.split(':')[0]  
    except Exception as e:
        print(f"ERROR | Could not extract IP from proxy: {e}")
    return None

def get_proxy_info(proxy_url):
    ip = extract_ip(proxy_url)
    if ip:
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}")
            if response.status_code == 200:
                data = response.json()
                return data.get('query'), data.get('country')
        except Exception as e:
            print(f"ERROR | Could not get proxy info: {e}")
    return None, None

def main(auth, proxy=None):
    headers = {'authorization': auth}
    
    session = requests.Session()
    if proxy:
        session.proxies.update({'http': proxy, 'https': proxy})

    claim_successful = claim(headers)  

    size = len(image) * len(image[0])
    order = [i for i in range(size)]
    random.shuffle(order)

    for pos_image in order:
        x, y = get_pos(pos_image, len(image[0]))
        time.sleep(0.05 + random.uniform(0.01, 0.1))
        try:
            color = get_color(get_canvas_pos(x, y), headers)
            if color == -1:
                print(crayons.red("ERROR | Token User Error - Please Update Token"))
                break  

            if image[y][x] == ' ' or color == c[image[y][x]]:
                print(f"INFO | Skip: {print_block['start_x'] + x - 1},{print_block['start_y'] + y - 1} | " + crayons.green("Skip"))
                continue

            result = paint(get_canvas_pos(x, y), c[image[y][x]], headers)
            if result == -1:
                print(crayons.red("ERROR | Token User Error - Please Update Token"))
                break
            elif not result:
                break  

        except IndexError:
            print(f"ERROR | IndexError at position: {pos_image}, Coordinates: ({y}, {x})")

while True:
    clear_screen()  
    print_banner()

    account_found = False
    proxies = load_proxies()  

    random.shuffle(proxies)

    for index, (username, auth) in enumerate(accounts.items()):  
        if check_account_data(auth):
            proxy_index = index % len(proxies)  
            proxy = proxies[proxy_index] if proxies else None
            
            ip, country = get_proxy_info(proxy) if proxy else (None, None)
            if ip and country:
                print(f"INFO | {username} | Starting with proxy | Country: {country}")
            else:
                print(f"INFO | {username} | Starting without a valid proxy")
            
            main(auth, proxy)  
            account_found = True

    if not account_found:
        print(crayons.red("INFO | No valid account found."))

    print(crayons.red(f"ZERO") + " | Waiting Full Energy...")
    wait_time = random.randint(1200, 1800)  # 20-30 minutes
    for remaining in range(wait_time, 0, -1):
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"ZERO | Waiting Full Energy {hours:02}:{minutes:02}:{seconds:02}...", end='\r')
        time.sleep(1)

    print()  
