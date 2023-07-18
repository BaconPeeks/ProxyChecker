The Proxy Checker script is a tool that allows you to test and validate a list of proxies for their usability. It checks the proxies by sending requests to specified target URLs and verifies their status codes and response times. The script provides a summary of the testing results, including the count of good and bad proxies.

Usage:
------

1. Configuration:
   - Ensure you have a `config.json` file with the necessary configuration settings.
   - The configuration file should include the following parameters:
     - `output_filename`: The name of the file to save the valid proxies.
     - `log_file`: The name of the log file to store error logs.
     - `target_urls`: A list of URLs to check the proxies against.
     - `proxy_sources`: A dictionary specifying the proxy sources for each protocol (HTTPS, SOCKS4, SOCKS5).
     - `protocols`: A dictionary mapping protocol selection numbers to their respective protocol names.

2. Running the Script:
   - Open a terminal or command prompt.
   - Navigate to the directory containing the script and configuration file.
   - Execute the following command:
     ```
     python proxies.py
     ```

3. Protocol Selection:
   - The script will prompt you to select a protocol for testing.
   - Enter the protocol selection number provided in the console.
   - The available protocols and their corresponding numbers will be displayed.

4. Proxy Gathering:
   - The script will gather proxies from the specified sources for the selected protocol.
   - It will download the proxies and store them in a list.

5. Proxy Testing:
   - The script will test each proxy by sending requests to the target URLs.
   - It will check the status code and response time of each request.
   - The results will be displayed in the console, showing good and bad proxies.

6. Saving Valid Proxies:
   - The script will save the valid proxies to the specified output file.
   - Only the proxies that pass the validation criteria will be saved.

7. Summary and Execution Time:
   - The script will display a summary of the proxy testing results.
   - The count of good and bad proxies will be shown.
   - The execution time of the script will be displayed.

8. Logging:
   - The script logs errors and exceptions encountered during the execution.
   - The log file specified in the configuration will store the error logs.

9. Additional Configuration Options:
   - The configuration file allows additional parameters to be set:
     - `retries`: Maximum number of retries for a failed request (default: 1).
     - `delay`: Initial delay in seconds before retrying a request (default: 1).
     - `timeout`: Timeout for each request in seconds (default: 5).
     - `threads`: Number of threads to use for testing proxies (default: 10).

Note: Make sure you have the required dependencies installed before running the script. You can install the dependencies by executing the following command:

``
pip install -r requirements.txt
``
