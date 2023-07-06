import os
import time
import requests
from colorama import init as colorama_init, Fore, Style
from concurrent.futures import ThreadPoolExecutor
import logging
from tabulate import tabulate
import platform
import urllib.parse

colorama_init()

# Set up logging
logging.basicConfig(filename='proxy_checker.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def clear_screen():
    # Clear the screen based on the operating system
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')


def download_proxies(url):
    try:
        # Download proxies from the specified URL
        response = requests.get(url)
        time.sleep(1)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        return response.text.strip().split('\n')
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download proxies from {url}: {e}")
        return []


def check_proxy(proxy, target_url, protocol_selection):
    retries = 1  # Maximum number of retries
    delay = 1  # Initial delay in seconds
    timeout = 5  # Timeout for each request in seconds

    # Parse and validate the target URL
    try:
        parsed_url = urllib.parse.urlparse(target_url)
    except ValueError:
        logging.error(f"Invalid target URL: {target_url}")
        return False, "Invalid URL", None

    if not parsed_url.scheme or not parsed_url.netloc:
        logging.error(f"Invalid target URL: {target_url}")
        return False, "Invalid URL", None

    for attempt in range(retries):
        try:
            # Check the proxy by sending a request to the target URL
            proxies = {protocol_selection: proxy}
            start_time = time.time()
            response = requests.get(
                target_url, proxies=proxies, timeout=timeout)
            end_time = time.time()
            response_time = end_time - start_time
            if response.status_code == 200:
                return True, response.status_code, response_time
            else:
                return False, response.status_code, response_time
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                # Retry with increasing delay
                time.sleep(delay)
                delay *= 2
            else:
                logging.error(
                    f"Error occurred while checking proxy {proxy}: {e}")
                return False, str(e), None
        except requests.exceptions.Timeout:
            logging.error(f"Timeout occurred while checking proxy {proxy}")
            return False, "Timeout", None


def save_proxies(proxies, output_filename):
    try:
        # Save the good proxies to a file
        with open(output_filename, 'w') as file:
            file.write('\n'.join(proxies))
        logging.info("Good proxies have been saved to %s", output_filename)
    except IOError as e:
        logging.error(
            f"Error occurred while saving proxies to {output_filename}: {e}")


def gather_proxies(protocol_selection):
    clear_screen()
    print(Fore.RED +
          f"Gathering proxies for {protocol_selection} protocol" + Style.RESET_ALL)
    proxy_sources = {
        'HTTPS': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=500&country=all',
            'https://proxy.webshare.io/proxy/list',
            'https://www.proxyscan.io/download?type=http',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://www.proxy-list.download/api/v1/get?type=http&anon=elite',
            'https://www.proxyscan.io/download?type=http&anon=elite'
        ],
        'SOCKS4': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=500&country=all',
            'https://www.proxyscan.io/download?type=socks4',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://www.proxy-list.download/api/v1/get?type=socks4',
            'https://www.proxy-list.download/api/v1/get?type=socks4&anon=elite',
            'https://www.proxyscan.io/download?type=socks4&anon=elite',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
            'https://www.proxynova.com/proxy-server-list/',
            'https://www.socks-proxy.net/',
            'https://proxy-daily.com/',
            'https://openproxy.space/list'
        ],
        'SOCKS5': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=500&country=all',
            'https://www.proxyscan.io/download?type=socks5',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://www.proxy-list.download/api/v1/get?type=socks5',
            'https://www.proxy-list.download/api/v1/get?type=socks5&anon=elite',
            'https://www.proxyscan.io/download?type=socks5&anon=elite',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
            'https://www.proxynova.com/proxy-server-list/',
            'https://www.socks-proxy.net/',
            'https://proxy-daily.com/'
        ]
    }
    proxies = []

    if protocol_selection in proxy_sources:
        sources = proxy_sources[protocol_selection]

        for source in sources:
            # Download proxies from each source
            source_proxies = download_proxies(source)
            proxies.extend(source_proxies)

    return proxies


def process_proxy(proxy, target_urls, protocol_selection):
    formatted_proxy = proxy.strip()
    results = []

    for target_url in target_urls:
        # Check the proxy for each target URL
        result = check_proxy(formatted_proxy, target_url, protocol_selection)
        results.append(result)

    # Check if all results are good
    is_good = all(result[0] for result in results)

    for result, target_url in zip(results, target_urls):
        _, status_code, response_time = result

        if is_good:
            # Print information for a good proxy
            logging.info("Good proxy for %s: %s | Status code: %d | Response time: %.2f seconds",
                         target_url, formatted_proxy, status_code, response_time)
            print(Fore.GREEN + formatted_proxy + Style.RESET_ALL + " | " +
                  Fore.GREEN + str(status_code) + Style.RESET_ALL + " | " +
                  Fore.CYAN + target_url + Style.RESET_ALL +
                  " | " + Fore.BLUE + f"{response_time:.2f} s" + Style.RESET_ALL)
        else:
            # Print information for a bad proxy
            logging.info("Bad proxy for %s: %s | Status code: %s |Response time: N/A",
                         target_url, formatted_proxy, status_code)
            print(Fore.RED + formatted_proxy + Style.RESET_ALL + " | " +
                  Fore.RED + str(status_code) + Style.RESET_ALL + " | " +
                  Fore.CYAN + target_url + Style.RESET_ALL +
                  " | " + Fore.BLUE + "N/A" + Style.RESET_ALL)

    return formatted_proxy if is_good else None


def main():
    start_time = time.time()
    output_filename = 'proxylist.txt'  # Update with your output filename
    log_file = 'proxy_checker.log'
    with open(log_file, 'w'):
        pass
    print(Fore.RED + r"""
 ____  ____   __   _  _   __   ____  ____ 
(  _ \(  _ \ /  \ ( \/ ) (  ) (  __)/ ___)
 ) __/ )   /(  O ) )  (   )(   ) _) \___ \
(__)  (__\_) \__/ (_/\_) (__) (____)(____/
  """ + Style.RESET_ALL)

    # Prompt user to select protocol
    protocols = {
        '1': 'HTTPS',
        '2': 'SOCKS4',
        '3': 'SOCKS5'
    }
    for key, value in protocols.items():
        print(f"{Fore.RED}{key}. {value.capitalize()}{Style.RESET_ALL}")
    print(Fore.RED + "Select a protocol:" + Style.RESET_ALL)
    protocol_selection = input()
    selected_protocol = protocols.get(protocol_selection)
    if not selected_protocol:
        print("Invalid selection.")
        return
    
    clear_screen()

    # Gather proxies
    proxies = gather_proxies(selected_protocol)
    if not proxies:
        print("No proxies were downloaded. Exiting.")
        return

    # Configure testing
    clear_screen()
    print(Fore.RED + "Enter the number of threads to use:" + Style.RESET_ALL)
    num_threads = int(input())
    target_urls = ['http://icanhazip.com/', 'http://ipv4.icanhazip.com/']

    clear_screen()

    # Test proxies
    good_proxies = []
    bad_proxies = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for proxy in proxies:
            future = executor.submit(
                process_proxy, proxy, target_urls, selected_protocol)
            futures.append(future)

        for future in futures:
            result = future.result()
            if result:
                good_proxies.append(result)
            else:
                bad_proxies.append(result)

    # Save good proxies to a file
    save_proxies(good_proxies, output_filename)

    # Calculate script execution time
    end_time = time.time()
    execution_time = end_time - start_time

    clear_screen()

    # Display results
    print("\nProxy Testing Summary:")
    print("----------------------")
    table_data = [
        [Fore.GREEN + "Good Proxies" + Style.RESET_ALL, len(good_proxies)],
        [Fore.RED + "Bad Proxies" + Style.RESET_ALL, len(bad_proxies)],
        [Fore.BLUE + "Script Execution Time" + Style.RESET_ALL, "{:.2f} seconds".format(execution_time)]
    ]
    print(tabulate(table_data, headers=["Result", "Count"], tablefmt="fancy_grid"))

if __name__ == '__main__':
    main()