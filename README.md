# Cryptocurrency trading simulator
#### Description:
This program is a cryptocurrency trading simulator. It works via the command-line. You can set a specific amount of USD for you portfolio and then use it to buy different cryptocurrencies which you can later sell. You can also check your portfolio balance and deposit extra USD to invest if you want. Read the Command-line arguments and instructions for more info on how to use it.

This is the second version of this project. It has been updated to use an SQL database instead of a csv file. It was built using the argparse, requests, sqlite3, sys and tabulate libraries. It uses the coincap v3 API, since the coincap V2 API got deprecated (This new version of the coincap API requires an API Key).


## Command-line Arguments
- **"-h" "--help" :** Prints the list of arguments used in the program
- **"--set":** Sets the initial account balance (in USD). (Re-starts the portfolio if you already have one)
- **"-c" "--crypto"  Cryptocurrency code: e.g. "btc" | Cryptocurrency name: e.g. "bitcoin" :**  To show the price of the cryptocurrency. Gives you the option to buy it.
- **"-b" "--balance" :** prints the account balance. (As a table, using tabulate)
- **"-d" "--deposit" :** option to deposit more USD to your portfolio
- **"-s" "--sell" Cryptocurrency code: e.g. "btc" | Cryptocurrency name: e.g. "bitcoin" :** gives you the option to sell the specified cryptocurrency (to USD).

## Instructions
1. Set an initial amount of USD for your portfolio using:
`python project.py --set` This will also restart your portfolio and any previous operations will be erased. If you want to add more USD to your portfolio without erasing your previous operations you should use `python project.py -s {name of the cryptocurrency}` or `python project.py --sell {name of the cryptocurrency}`. Only use `--set` the first time you use the program or if you want to restart your portfolio.
2. If you want to deposit additional USD for your portfolio you can use: `python project.py -d` or `python project.py --deposit` at any moment.
3. To check the price on any specific cryptocurrency use (using etheruem as an example):`python project.py -c eth` or `python project.py --crypto eth`. After that you will be prompted to input the specific amount that you want to buy/check. You will then see the current price and decide whether to buy it or not.
4. You can repeat step 3 any number of times, as long as you have a sufficient amount of USD, otherwise if you don't have enough USD to buy the specified amount of cryptocurrency, the operation will be cancelled and the following text will appear "*Insufficient funds. Operation cancelled"*.
5. If you want to sell any of the cryptocurrencies you have bought you can use (using bitcoin as an example):`python project.py -s bitcoin` or `python project.py --sell bitcoin`
6. Finally, if you want to visualize the current balance of your portfolio, you can use: `python project.py -b` or `python project.py --balance`
This will output your current portfolio balance as a table.

### Notes:
- This program currently supports the following cryptocurrencies: bitcoin, ethereum, dogecoin, ripple.
- The coincap v3 API may eventually be deprecated. If that happens, the program will need to be updated to use a different API.
