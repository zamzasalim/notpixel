import os
import requests
import json
import time
import random
import config
import logging
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
    try:
        return query.json()['pixel']['color']
    except KeyError:
        return "#000000"

def claim(header):
    requests.get(f"{url}/mining/claim", headers=header)

def get_pixel(x, y):
    return y * 1000 + x + 1

def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

def get_canvas_pos(x, y):
    return get_pixel(print_block['start_x'] + x - 1, print_block['start_y'] + y - 1)

def next_pixel(pos_image, size):
    return (pos_image + 1) % size

def paint(canvas_pos, color, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }
    response = requests.post(f"{url}/repaint/start", data=json.dumps(data), headers=header)
    x, y = get_pos(canvas_pos, 1000)

    if response.status_code == 400:
        print(crayons.red("INFO | Out of Energy"))
        wait_time = random.randint(1800, 2400)
        for remaining in range(wait_time, 0, -1):
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(crayons.red(f"ZERO") + f" | Waiting Full Energy {hours:02}:{minutes:02}:{seconds:02}...", end='\r')
            time.sleep(1)
        print()  
        return False  

    if response.status_code == 401:
        return -1

    print(f"INFO | Paint: {x},{y} | " + crayons.green("Success!!"))
    return True

def main(auth):
    headers = {'authorization': auth}
    claim(headers)

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
            print(pos_image, y, x)

while True:
    clear_screen()  
    print_banner()
    for username, auth in config.accounts.items():  
        print(f"INFO | {username} | Starting")  
        main(auth)  
    print(crayons.yellow("INFO | Restarting..."))
    wait_time = random.randint(1200, 1800)  
    for remaining in range(wait_time, 0, -1):
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(crayons.red(f"INFO") + f" | Restart Countdown {hours:02}:{minutes:02}:{seconds:02}...", end='\r')
        time.sleep(1)

    print()  
