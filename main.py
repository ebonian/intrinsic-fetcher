import requests
import json
import os

stock_symbols = ['AAPL', 'MSFT', 'TSLA', 'V', 'GOOG', 'ASML', 'GFS', 'AMD', 'NET', 'AMZN', 'TSM', 'QCOM', 'NVDA'] 

DATA_DIR = 'data'
FUNCTIONS = ['INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW']
SUMMARY_DIR = os.path.join(DATA_DIR, 'SUMMARY')

API_KEY = os.getenv('API_KEY')
DAILY_LIMIT = 25 // len(FUNCTIONS)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def fetch_data(symbol, function):
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "symbol" in data:
            save_to_file(function, symbol, data)
        else:
            print(f"Error fetching data for {symbol} with function {function}: {data.get('Note', 'No valid data')}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {symbol} with function {function}: {e}")

def save_to_file(function, symbol, data):
    function_dir = os.path.join(DATA_DIR, function)
    if not os.path.exists(function_dir):
        os.makedirs(function_dir)

    file_path = os.path.join(function_dir, f"{symbol}.json")
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data for {symbol} under function {function} saved to {file_path}")

def save_progress(fetched_symbols):
    with open('fetched_symbols.json', 'w') as f:
        json.dump(fetched_symbols, f)

def load_progress():
    if os.path.exists('fetched_symbols.json'):
        with open('fetched_symbols.json', 'r') as f:
            return json.load(f)
    return []

def fetch_from_list(stock_symbols):
    fetched_symbols = load_progress()

    remaining_symbols = [symbol for symbol in stock_symbols if symbol not in fetched_symbols]

    if not remaining_symbols:
        print("All symbols fetched. Starting the list over to ensure up-to-date data.")
        fetched_symbols = []
        remaining_symbols = stock_symbols

    symbols_to_fetch = remaining_symbols[:DAILY_LIMIT]

    for symbol in symbols_to_fetch:
        for function in FUNCTIONS:
            fetch_data(symbol, function)
        fetched_symbols.append(symbol)

    save_progress(fetched_symbols)

    print(f"Fetched {len(symbols_to_fetch)} symbols today. Remaining: {len(remaining_symbols) - len(symbols_to_fetch)}")

def merge_json_files(file_paths):
    merged_data = {"symbol": "", "annualReports": {}, "quarterlyReports": {}}
    
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        if not merged_data["symbol"]:
            merged_data["symbol"] = data["symbol"]
        
        for report in data.get("annualReports", []):
            fiscal_date = report["fiscalDateEnding"]
            if fiscal_date not in merged_data["annualReports"]:
                merged_data["annualReports"][fiscal_date] = {}
            merged_data["annualReports"][fiscal_date].update(report)
        
        for report in data.get("quarterlyReports", []):
            fiscal_date = report["fiscalDateEnding"]
            if fiscal_date not in merged_data["quarterlyReports"]:
                merged_data["quarterlyReports"][fiscal_date] = {}
            merged_data["quarterlyReports"][fiscal_date].update(report)
    
    merged_data["annualReports"] = list(merged_data["annualReports"].values())
    merged_data["quarterlyReports"] = list(merged_data["quarterlyReports"].values())
    
    return merged_data

def merge_and_save_summary(symbol):
    if not os.path.exists(SUMMARY_DIR):
        os.makedirs(SUMMARY_DIR)

    annual_files = [os.path.join(DATA_DIR, 'INCOME_STATEMENT', f"{symbol}.json"),
                    os.path.join(DATA_DIR, 'BALANCE_SHEET', f"{symbol}.json"),
                    os.path.join(DATA_DIR, 'CASH_FLOW', f"{symbol}.json")]

    missing_files = [file for file in annual_files if not os.path.exists(file)]
    if missing_files:
        print(f"Skipping summary generation for {symbol} due to missing files: {missing_files}")
        return

    merged_data = merge_json_files(annual_files)
    summary_file_path = os.path.join(SUMMARY_DIR, f"{symbol}.json")
    
    with open(summary_file_path, 'w') as json_file:
        json.dump(merged_data, json_file, indent=4)
    print(f"Summary data for {symbol} saved to {summary_file_path}")

def generate_summaries(stock_symbols):
    for symbol in stock_symbols:
        merge_and_save_summary(symbol)

if __name__ == "__main__":
    fetch_from_list(stock_symbols)
    generate_summaries(stock_symbols)
