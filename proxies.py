import os  # Used for clearing the screen
import time  # Used for introducing delays
import requests  # Used for making HTTP requests
import logging  # Used for logging
import platform  # Used for detecting the operating system
import urllib.parse  # Used for parsing and validating URLs
import regex as re  # Used for regular expressions
from colorama import init as colorama_init, Fore, Style  # Used for colored output
from concurrent.futures import ThreadPoolExecutor  # Used for concurrent execution
from tabulate import tabulate  # Used for tabular output
import json  # Used for reading the configuration file

colorama_init()  # Initialize colorama for colored output

# Set up logging
logging.basicConfig(filename='proxy_checker.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('proxy_checker')


class ProxyChecker:
    def __init__(self, config):
        self.config = config
        self.retries = config.get("retries", 1)  # Maximum number of retries
        self.delay = config.get("delay", 1)  # Initial delay in seconds
        self.timeout = config.get("timeout", 5)  # Timeout for each request in seconds
        self.threads = config.get("threads", 10)  # Number of threads to use for testing

    def clear_screen(self):
        # Clear the screen based on the operating system
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def download_proxies(self, url):
        try:
            # Download proxies from the specified URL
            response = requests.get(url)
            time.sleep(1)
            response.raise_for_status()  # Raise an exception for non-200 status codes
            return response.text.strip().split('\n')
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download proxies from {url}: {e}")
            return []

    def check_proxy(self, proxy, target_url, protocol_selection):
        retries = self.retries
        delay = self.delay
        timeout = self.timeout

        # Parse and validate the target URL
        try:
            parsed_url = urllib.parse.urlparse(target_url)
        except ValueError:
            logger.error(f"Invalid target URL: {target_url}")
            return False, "Invalid URL", None

        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid target URL: {target_url}")
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
                    logger.error(
                        f"Error occurred while checking proxy {proxy}: {e}")
                    return False, str(e), None
            except requests.exceptions.Timeout:
                logger.error(f"Error occurred while checking proxy {proxy}: {e}")
                return False, str(e), None

    def save_proxies(self, proxies, filename):
        valid_proxies = []
        for proxy in proxies:
            if self.is_valid_proxy(proxy):
                valid_proxies.append(proxy)

        with open(filename, 'w') as file:
            # Clear the file by writing an empty string
            file.write('')

        with open(filename, 'a') as file:
            file.write('\n'.join(valid_proxies))

        print(f"Saved {len(valid_proxies)} valid proxies to {filename}")

    def is_valid_proxy(self, proxy):
        proxy_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+'

        # Check if the proxy matches the pattern
        return re.match(proxy_pattern, proxy) is not None

    def gather_proxies(self, protocol_selection):
        self.clear_screen()
        print(Fore.RED +
              f"Gathering proxies for {protocol_selection} protocol" + Style.RESET_ALL)
        proxies = []

        if protocol_selection in self.config['proxy_sources']:
            sources = self.config['proxy_sources'][protocol_selection]

            for source in sources:
                # Download proxies from each source
                source_proxies = self.download_proxies(source)
                proxies.extend(source_proxies)

        return proxies

    def process_proxy(self, proxy, target_urls, protocol_selection):
        formatted_proxy = proxy.strip()
        results = []

        for target_url in target_urls:
            # Check the proxy for each target URL
            result = self.check_proxy(formatted_proxy, target_url, protocol_selection)
            results.append(result)

        # Check if all results are good
        is_good = all(result[0] for result in results)

        for result, target_url in zip(results, target_urls):
            _, status_code, response_time = result

            if is_good:
                # Print information for a good proxy
                logger.info("Good proxy for %s: %s | Status code: %d | Response time: %.2f seconds",
                            target_url, formatted_proxy, status_code, response_time)
                print(Fore.GREEN + formatted_proxy + Style.RESET_ALL + " | " +
                      Fore.GREEN + str(status_code) + Style.RESET_ALL + " | " +
                      Fore.CYAN + target_url + Style.RESET_ALL +
                      " | " + Fore.BLUE + f"{response_time:.2f} s" + Style.RESET_ALL)
            else:
                # Print information for a bad proxy
                logger.info("Bad proxy for %s: %s | Status code: %s |Response time: N/A",
                            target_url, formatted_proxy, status_code)
                print(Fore.RED + formatted_proxy + Style.RESET_ALL + " | " +
                      Fore.RED + str(status_code) + Style.RESET_ALL + " | " +
                      Fore.CYAN + target_url + Style.RESET_ALL +
                      " | " + Fore.BLUE + "N/A" + Style.RESET_ALL)

        return formatted_proxy if is_good else None

    def setup_logging(self, log_file):
        logger.handlers = []  # Clear any existing handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def prompt_protocol_selection(self):
        # Prompt user to select protocol
        protocols = self.config['protocols']
        for key, value in protocols.items():
            print(f"{Fore.RED}{key}. {value.capitalize()}{Style.RESET_ALL}")
        print(Fore.RED + "Select a protocol:" + Style.RESET_ALL)
        protocol_selection = input()
        selected_protocol = protocols.get(protocol_selection)
        if not selected_protocol:
            print("Invalid selection.")
            return None
        return selected_protocol

    def prompt_num_threads(self):
        num_threads = self.config.get("threads", 10)
        return num_threads

    def test_proxies(self, proxies, selected_protocol, num_threads):
        self.clear_screen()

        # Test proxies
        good_proxies = []
        bad_proxies = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for proxy in proxies:
                future = executor.submit(
                    self.process_proxy, proxy, self.config['target_urls'], selected_protocol)
                futures.append(future)

            for future in futures:
                result = future.result()
                if result:
                    good_proxies.append(result)
                else:
                    bad_proxies.append(result)

        return good_proxies, bad_proxies

    def display_results(self, good_proxies, bad_proxies):
        self.clear_screen()

        # Validate proxies
        valid_good_proxies = []
        valid_bad_proxies = []

        for proxy in good_proxies:
            if self.is_valid_proxy(proxy):
                valid_good_proxies.append(proxy)

        for proxy in bad_proxies:
            if self.is_valid_proxy(proxy):
                valid_bad_proxies.append(proxy)

    # Display results
        print("\nProxy Testing Summary:")
        print("----------------------")
        table_data = [
        [Fore.GREEN + "Good Proxies" + Style.RESET_ALL, len(valid_good_proxies)],
        [Fore.RED + "Bad Proxies" + Style.RESET_ALL, len(valid_bad_proxies)],
    ]
        print(tabulate(table_data, headers=["Result", "Count"], tablefmt="fancy_grid"))

    def main(self):
        start_time = time.time()

        # Initialize logging
        self.setup_logging(self.config['log_file'])

        print(Fore.RED + r"""
 ____  ____   __   _  _   __   ____  ____ 
(  _ \(  _ \ /  \ ( \/ ) (  ) (  __)/ ___)
 ) __/ )   /(  O ) )  (   )(   ) _) \___ \
(__)  (__\_) \__/ (_/\_) (__) (____)(____/
  """ + Style.RESET_ALL)

        # Prompt user to select protocol
        selected_protocol = self.prompt_protocol_selection()
        if not selected_protocol:
            return

        self.clear_screen()

        # Gather proxies
        proxies = self.gather_proxies(selected_protocol)
        if not proxies:
            print("No proxies were downloaded. Exiting.")
            return

        self.clear_screen()

        # Configure testing
        num_threads = self.prompt_num_threads()

        self.clear_screen()

        # Test proxies
        good_proxies, bad_proxies = self.test_proxies(proxies, selected_protocol, num_threads)

        # Save good proxies to a file
        self.save_proxies(good_proxies, self.config['output_filename'])

        # Calculate script execution time
        end_time = time.time()
        execution_time = end_time - start_time

        self.clear_screen()

        # Display results
        self.display_results(good_proxies, bad_proxies)
        print(Fore.BLUE + "Script Execution Time" + Style.RESET_ALL, "{:.2f} seconds".format(execution_time))


if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    proxy_checker = ProxyChecker(config)
    proxy_checker.main()
