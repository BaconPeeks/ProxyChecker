import os
import time
import requests
import logging
import platform
import urllib.parse
import re
from colorama import init as colorama_init, Fore, Style
from concurrent.futures import ThreadPoolExecutor
from tabulate import tabulate
import json

colorama_init()

logging.basicConfig(filename='proxy_checker.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('proxy_checker')


class ProxyChecker:
    def __init__(self, config):
        self.config = config
        self.retries = config.get("retries", 1)
        self.delay = config.get("delay", 1)
        self.timeout = config.get("timeout", 5)
        self.threads = config.get("threads", 10)

    def clear_screen(self):
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    def download_proxies(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text.strip().split('\n')
        except requests.RequestException as e:
            logger.error(f"Failed to download proxies from {url}: {e}")
            return []

    def check_proxy(self, proxy, target_url, protocol_selection):
        parsed_url = urllib.parse.urlparse(target_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid target URL: {target_url}")
            return False, "Invalid URL", None

        delay = self.delay
        for attempt in range(self.retries):
            try:
                proxies = {protocol_selection: proxy}
                start = time.time()
                response = requests.get(target_url, proxies=proxies, timeout=self.timeout)
                elapsed = time.time() - start
                return response.status_code == 200, response.status_code, elapsed
            except requests.Timeout as e:
                logger.warning(f"Timeout with {proxy}: {e}")
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= 2
            except requests.RequestException as e:
                logger.error(f"Request error with {proxy}: {e}")
                return False, str(e), None

        return False, "Timeout", None

    def save_proxies(self, proxies, filename):
        valid_proxies = [p for p in proxies if self.is_valid_proxy(p)]
        with open(filename, 'w') as file:
            file.write('\n'.join(valid_proxies))
        print(f"Saved {len(valid_proxies)} valid proxies to {filename}")

    def is_valid_proxy(self, proxy):
        return re.match(r'\d{1,3}(\.\d{1,3}){3}:\d+$', proxy) is not None

    def gather_proxies(self, protocol_selection):
        self.clear_screen()
        print(Fore.RED + f"Gathering proxies for {protocol_selection}" + Style.RESET_ALL)
        proxies = []
        for source in self.config['proxy_sources'].get(protocol_selection, []):
            proxies.extend(self.download_proxies(source))
        return proxies

    def process_proxy(self, proxy, target_urls, protocol_selection):
        results = [self.check_proxy(proxy.strip(), url, protocol_selection) for url in target_urls]
        is_good = all(r[0] for r in results)

        for result, url in zip(results, target_urls):
            status, code, resp_time = result
            color = Fore.GREEN if status else Fore.RED
            time_info = f"{resp_time:.2f}s" if resp_time else "N/A"
            print(f"{color}{proxy}{Style.RESET_ALL} | {color}{code}{Style.RESET_ALL} | "
                  f"{Fore.CYAN}{url}{Style.RESET_ALL} | {Fore.BLUE}{time_info}{Style.RESET_ALL}")

        return proxy if is_good else None

    def setup_logging(self, log_file):
        logger.handlers.clear()
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    def prompt_protocol_selection(self):
        protocols = self.config['protocols']
        for k, v in protocols.items():
            print(f"{Fore.RED}{k}. {v.capitalize()}{Style.RESET_ALL}")
        selection = input(Fore.RED + "Select a protocol: " + Style.RESET_ALL)
        return protocols.get(selection)

    def test_proxies(self, proxies, protocol, threads):
        self.clear_screen()
        good, bad = [], []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.process_proxy, p, self.config['target_urls'], protocol): p for p in proxies}
            for future in futures:
                result = future.result()
                (good if result else bad).append(futures[future])
        return good, bad

    def display_results(self, good, bad):
        self.clear_screen()
        data = [
            [Fore.GREEN + "Good Proxies" + Style.RESET_ALL, len([p for p in good if self.is_valid_proxy(p)])],
            [Fore.RED + "Bad Proxies" + Style.RESET_ALL, len([p for p in bad if self.is_valid_proxy(p)])]
        ]
        print("\nProxy Testing Summary:")
        print(tabulate(data, headers=["Result", "Count"], tablefmt="fancy_grid"))

    def main(self):
        start = time.time()
        self.setup_logging(self.config['log_file'])

        print(Fore.RED + r"""
 ____  ____   __   _  _   __   ____  ____ 
(  _ \(  _ \/  \ ( \/ ) (  ) (  __)/ ___)
 ) __/ )   /(  O ) )  (   )(   ) _) \___ \
(__)  (__\_) \__/ (_/\_) (__) (____)(____/
""" + Style.RESET_ALL)

        protocol = self.prompt_protocol_selection()
        if not protocol:
            return

        proxies = self.gather_proxies(protocol)
        if not proxies:
            print("No proxies downloaded. Exiting.")
            return

        threads = self.config.get("threads", 10)
        good, bad = self.test_proxies(proxies, protocol, threads)

        self.save_proxies(good, self.config['output_filename'])
        self.display_results(good, bad)

        print(Fore.BLUE + "Script Execution Time:" + Style.RESET_ALL, f"{time.time() - start:.2f} seconds")


if __name__ == '__main__':
    with open('config.json') as f:
        cfg = json.load(f)
    ProxyChecker(cfg).main()
