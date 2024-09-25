accounts = {
    "account1": "initData Paste-Here",
    "account2": "initData Paste-Here",
    "account3": "initData Paste-Here",
    "account4": "initData Paste-Here",
    "account5": "initData Paste-Here",
    "account6": "initData Paste-Here",
    # Add up to 100 accounts in this format
}

def load_proxies(filename='proxy.txt'):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File {filename} tidak ditemukan.")
        return []
