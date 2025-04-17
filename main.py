# Import libraries
import argparse
import requests
import sqlite3
import sys
import os
from tabulate import tabulate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
COINCAP_API_KEY = os.environ.get("COINCAP_API_KEY")
if not COINCAP_API_KEY:
    sys.exit("COINCAP_API_KEY environment variable not set. Please set it before running the script.")
# New Base URL
COINCAP_API_BASE_URL = "https://rest.coincap.io/v3"
# ---------------------

# Database initialization
def init_db():
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            currency TEXT PRIMARY KEY,
            amount REAL
        )
    ''')
    conn.commit()
    conn.close()

# Define main
def main():
    # Initialize the database
    init_db()

    # Create the parser
    parser = argparse.ArgumentParser(description='Cryptocurrency information tool')

    # Add the arguments
    parser.add_argument("-c", "--crypto", type=str, help="Cryptocurrency code or name (bitcoin/btc, ethereum/eth, dogecoin/doge...)")
    parser.add_argument("--set", action="store_true", help="Sets initial USD amount for the simulation. This will wipe out all previous data and restart the simulation")
    parser.add_argument("-b", "--balance", action="store_true", help="Show the current balance as a table")
    parser.add_argument("-d", "--deposit", action="store_true", help="Deposit additional USD to your portfolio. Without deleting previous data")
    parser.add_argument("-s","--sell", type=str, help="Code or name of the cryptocurrency you want to sell")

    # Parse the arguments
    args = parser.parse_args()

    # When used with "--set"
    if args.set:
        # Prompt the user to set starting USD amount for the crypto simulation
        amount = set_usd_amount()
        update_portfolio("USD" , amount, mode = "restart")
        print(f"USD amount set to ${amount:,.2f} in the portfolio.")


    # When used with "-c" or "--cc"
    elif args.crypto:
        try:
            # Convert to lowercase for case-insensitive comparison
            crypto = args.crypto.lower().strip()

            # Call a function to return the crypto id
            crypto_id = get_crypto_id(crypto)

            # Check if the crypto_id is valid before calling API
            if not crypto_id:
                sys.exit(f"Error: Unsupported or invalid cryptocurrency '{args.crypto}'. Supported: btc/bitcoin, eth/ethereum, doge/dogecoin, xrp/ripple.")

            # Prepare for v3 API call using search parameter
            api_url = f"{COINCAP_API_BASE_URL}/assets"
            headers = {"Authorization": f"Bearer {COINCAP_API_KEY}"}
            params = {"search": crypto_id}  # Use search parameter

            # Call the v3 api and get the response
            response = requests.get(api_url, headers=headers, params=params)

            # Check for successful response status
            if response.status_code != 200:
                 sys.exit(f"Error: API request failed for '{crypto_id}' at {api_url} with status code {response.status_code}. Check API key, crypto ID, or try again later. Response: {response.text}")

            try:
                response_data = response.json()
                # Validate the structure - search likely returns a list in 'data' key
                if "data" not in response_data or not isinstance(response_data["data"], list) or len(response_data["data"]) == 0:
                    sys.exit(f"Error: No asset found for search term '{crypto_id}' or unexpected API response structure. Response: {response_data}")

                # Assume the first result is the correct one for a specific ID search
                asset_data = response_data["data"][0]

                if "priceUsd" not in asset_data:
                     sys.exit(f"Error: 'priceUsd' not found in the asset data for '{crypto_id}'. Response: {asset_data}")

                price_str = asset_data.get("priceUsd")

                if price_str is None:
                     sys.exit(f"Error: API v3 returned null price for '{crypto_id}'. Asset data: {asset_data}")

                price = float(price_str)

            except (ValueError, TypeError, IndexError) as e:
                 sys.exit(f"Error: Could not parse price from API v3 response for '{crypto_id}'. Error: {e}. Response: {response_data}")
            except requests.exceptions.JSONDecodeError:
                 sys.exit(f"Error: Could not decode API v3 response into JSON for '{crypto_id}'. Response text: {response.text}")

            # Get the quantity
            q = quantity()
            total_price = round(q * price, 4)
            # Print the price
            print(f"The price of {q} {crypto_id.lower()} is ${(total_price):,.4f}")

            answer = buy()

            # If the user inputs that they want to buy that amount of crypto,
            # subtract it from the USD value and add it to the crypto mentioned in the database
            if answer:
                # Check if the user has sufficient USD funds
                conn = sqlite3.connect('portfolio.db')
                cursor = conn.cursor()
                cursor.execute("SELECT amount FROM portfolio WHERE currency = ?", ("USD",))
                result = cursor.fetchone()
                conn.close()

                sufficient_funds = False
                required_usd = q * price
                if result:
                    current_usd = result[0]
                    if current_usd >= required_usd:
                        sufficient_funds = True

                if sufficient_funds:
                    update_portfolio("USD", required_usd, "subtract")
                    update_portfolio(crypto_id, q, "update") # Use crypto_id directly
                    print(f"You have just bought {q} {crypto_id}")
                else:
                    sys.exit("Insufficient USD funds. Operation cancelled")
            else:
                sys.exit()
        except requests.exceptions.ConnectionError:
            # More specific error message
            sys.exit(f"Error: Could not connect to the API endpoint ({api_url}). Please check your network connection, firewall settings, or if the API service is available.")
        except requests.exceptions.Timeout:
            sys.exit(f"Error: The request to {api_url} timed out. Please try again later.")
        except (KeyError, ValueError):
            sys.exit(f"Error: Invalid response from the API.")


    # When used with "-b" or "--balance"
    elif args.balance:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute("SELECT currency, amount FROM portfolio ORDER BY currency")
        results = cursor.fetchall()
        conn.close()

        if results:
            # Format the amount column to have commas and 4 decimal places for non-USD, 2 for USD
            formatted_results = []
            for currency, amount in results:
                if currency == "USD":
                    formatted_amount = f"${amount:,.2f}"
                else:
                    formatted_amount = f"{amount:,.4f}" # Keep 4 decimals for crypto
                formatted_results.append([currency, formatted_amount])

            headers = ["Currency/Crypto", "Amount"]
            print(tabulate(formatted_results, headers=headers, tablefmt="grid"))
        else:
            print("Portfolio is empty.")

    # When used with "-d" or "--deposit"
    elif args.deposit:
        # Prompt the user to enter USD amount they want to deposit
        while True:
            try:
                amount = float(input("Enter USD amount you want to deposit: "))
                if amount < 0:
                    print("Please enter a positive number.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")

        update_portfolio("USD", amount, "update")
        print(f"You have succesfully deposited ${amount:,.2f} to your account")

    # When used with "-s" or "--sell"
    elif args.sell:
        try:
            # Convert to lowercase for case-insensitive comparison
            crypto = args.sell.lower().strip()
            # Call a function to return the crypto id
            crypto_id = get_crypto_id(crypto)

            # Check if the crypto_id is valid before calling API
            if not crypto_id:
                # Note: Using args.sell here as args.crypto would be None in this block
                sys.exit(f"Error: Unsupported or invalid cryptocurrency '{args.sell}'. Supported: btc/bitcoin, eth/ethereum, doge/dogecoin, xrp/ripple.")

            # Prepare for v3 API call using search parameter
            api_url = f"{COINCAP_API_BASE_URL}/assets"  # Use the base assets endpoint
            headers = {"Authorization": f"Bearer {COINCAP_API_KEY}"}
            params = {"search": crypto_id}  # Use search parameter

            # Call the v3 api and get the response
            response = requests.get(api_url, headers=headers, params=params)

            # Check for successful response status
            if response.status_code != 200:
                 sys.exit(f"Error: API request failed for '{crypto_id}' at {api_url} with status code {response.status_code}. Check API key, crypto ID, or try again later. Response: {response.text}")

            try:
                response_data = response.json()
                # Validate the structure - search likely returns a list in 'data' key
                if "data" not in response_data or not isinstance(response_data["data"], list) or len(response_data["data"]) == 0:
                    sys.exit(f"Error: No asset found for search term '{crypto_id}' or unexpected API response structure. Response: {response_data}")

                # Assume the first result is the correct one for a specific ID search
                asset_data = response_data["data"][0]

                if "priceUsd" not in asset_data:
                     sys.exit(f"Error: 'priceUsd' not found in the asset data for '{crypto_id}'. Response: {asset_data}")

                price_str = asset_data.get("priceUsd")

                if price_str is None:
                     sys.exit(f"Error: API v3 returned null price for '{crypto_id}'. Asset data: {asset_data}")

                price = float(price_str)

            except (ValueError, TypeError, IndexError) as e:
                 sys.exit(f"Error: Could not parse price from API v3 response for '{crypto_id}'. Error: {e}. Response: {response_data}")
            except requests.exceptions.JSONDecodeError:
                 sys.exit(f"Error: Could not decode API v3 response into JSON for '{crypto_id}'. Response text: {response.text}")

            # Get the quantity
            q = quantity()
            total_price = round(q * price, 4)
            # Print the price
            print(f"The price of {q} {crypto_id.lower()} is ${total_price:,.4f}")
            # Ask if the user wants to sell
            answer = sell()

            # If they want to sell, subtract it from the crypto value and add it to the USD amount in the database
            if answer:
                # Check if the user has sufficient crypto funds
                conn = sqlite3.connect('portfolio.db')
                cursor = conn.cursor()
                cursor.execute("SELECT amount FROM portfolio WHERE currency = ?", (crypto_id,))
                result = cursor.fetchone()
                conn.close()

                sufficient_funds = False
                if result:
                    current_amount = result[0]
                    if current_amount >= q:
                        sufficient_funds = True

                if sufficient_funds:
                    update_portfolio(crypto_id, q, "subtract") # Use crypto_id directly
                    update_portfolio("USD", q * price, "update")
                    print(f"You have just sold {q} {crypto_id}")
                else:
                    sys.exit(f"Insufficient {crypto_id} funds. Operation cancelled")
            else:
                sys.exit()
        # Handle the exceptions
        except requests.exceptions.ConnectionError:
             # More specific error message
            sys.exit(f"Error: Could not connect to the API endpoint ({api_url}). Please check your network connection, firewall settings, or if the API service is available.")
        except requests.exceptions.Timeout:
            sys.exit(f"Error: The request to {api_url} timed out. Please try again later.")
        except (KeyError, ValueError):
            sys.exit(f"Error: Invalid response from the API.")

    # In case no command-line arguments are given
    else:
        sys.exit("Please use command line arguments. If you need more information about how this program works, read the instructions provided on the README.md file")


# Define the get crypto id function
def get_crypto_id(input):
    crypto_mapping = {
        "btc": "bitcoin",
        "bitcoin": "bitcoin",
        "eth": "ethereum",
        "ethereum": "ethereum",
        "doge": "dogecoin",
        "dogecoin": "dogecoin",
        "xrp": "xrp",
        "ripple": "xrp",
    }
    return crypto_mapping.get(input)


# Define the quantity function
def quantity():
    while True:
        try:
            quantity = float(input("How much cryptocurrency? ").strip().replace(" ",""))
            return quantity
        except ValueError:
            pass


# Define the buy function
def buy():
    while True:
        answer = input("Do you want to buy this amount? (yes/no | y/n) ").strip()
        if answer.lower() == "yes" or answer.lower() == "y":
            return True
        elif answer.lower() == "no" or answer.lower() == "n":
            return False
        else:
            print("Please input valid answer(yes/no or y/n)")
            pass


# Define the sell function
def sell():
    while True:
        answer = input("Do you want to sell this amount? (yes/no | y/n) ").strip()
        if answer.lower() == "yes" or answer.lower() == "y":
            return True
        elif answer.lower() == "no" or answer.lower() == "n":
            return False
        else:
            print("Please input valid answer(yes/no or y/n)")
            pass


# Define the set_usd_amount function
def set_usd_amount():
    while True:
        try:
            amount = float(input("Enter inital USD amount to set for the simulation: ").strip().replace(" ",""))
            if amount < 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    # Return the amount
    return amount


# Write the update_portfolio function using SQLite
def update_portfolio(currency, amount, mode):
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()

    if mode == "restart":
        # Clear the table and insert the initial amount
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("INSERT INTO portfolio (currency, amount) VALUES (?, ?)", (currency, amount))
    elif mode == "update":
        # Check if currency exists
        cursor.execute("SELECT amount FROM portfolio WHERE currency = ?", (currency,))
        result = cursor.fetchone()

        if result:
            # Update existing amount
            new_amount = result[0] + amount
            cursor.execute("UPDATE portfolio SET amount = ? WHERE currency = ?", (new_amount, currency))
        else:
            # Insert new currency
            cursor.execute("INSERT INTO portfolio (currency, amount) VALUES (?, ?)", (currency, round(amount, 6)))
    elif mode == "subtract":
        # Check if currency exists
        cursor.execute("SELECT amount FROM portfolio WHERE currency = ?", (currency,))
        result = cursor.fetchone()

        if result:
            current_amount = result[0]
            # Ensure sufficient funds before subtracting (although primary check is done earlier)
            if current_amount >= amount:
                new_amount = current_amount - amount
                # Update the amount. Consider deleting if amount becomes zero.
                if new_amount > 0.00001: # Use a small threshold for floating point comparison
                     cursor.execute("UPDATE portfolio SET amount = ? WHERE currency = ?", (new_amount, currency))
                else:
                     cursor.execute("DELETE FROM portfolio WHERE currency = ?", (currency,)) # Remove if balance is effectively zero
            else:
                # This case should ideally be handled before calling update_portfolio
                print(f"Error: Insufficient {currency} balance for subtraction (this check should be earlier).")
        else:
            # This case should also ideally be handled before calling update_portfolio
            print(f"Error: {currency} not found in portfolio for subtraction.")

    conn.commit()
    conn.close()


# Call the main function
if __name__ == "__main__":
    main()
