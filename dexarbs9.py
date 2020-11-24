from brownie import MyFlashloanContract, accounts, web3
import requests
import json
import pickle
import time
import pprint
import sys

acct = accounts.load("arbAccount")
one_inch_split_abi = json.load(open("scripts/abi/IOneSplitMulti_old.json", "r"))

# 20 ether in wei
loan = "20000000000000000000"
arbMargin = 2.0
altarbMargin = 2.2
parts = 10


AAVE_LENDING_POOL_ADDRESS_PROVIDER = "0x24a42fD28C976A61Df5D00D0599C34c4f90748c8"
OneSplitAddress = "0x50FDA034C0Ce7a8f7EFDAebDA7Aa7cA21CC1267e"

one_inch_split_contract = web3.toChecksumAddress(
    OneSplitAddress
)  # 1 inch split contract

# load our contract
one_inch_join = web3.eth.contract(
    address=one_inch_split_contract, abi=one_inch_split_abi
)

markets = {}
blacklist = []
blacklist.append("CHAI-ETH")
blacklist.append("CHAI-USDT")
blacklist.append("CHAI-DAI")
blacklist.append("CHAI-USDC")


ercAddresses = {}
contracts = {}
priceOfETH = {}

baseAssets = [
    "ETH",
    "DAI",
    "USDC",
    "SUSD",
    "TUSD",
    "USDT",
    "BUSD",
    "BAT",
    "ENJ",
    "KNC",
    "LEND",
    "LINK",
    # 'MANA',
    "MKR",
    "REN",
    # 'REP',
    "SNX",
    "WBTC",
    "YFI",
    "ZRX",
]

gasPrice = 0
prices = {}


def getPrices():
    global prices
    priceData = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=eth"
    )
    pricesInfo = priceData.json()
    for priceItem in pricesInfo:
        sym = priceItem["symbol"].upper()
        if sym in baseAssets:
            prices[sym] = priceItem["current_price"]
    pprint.pprint(prices)


def arb(tokens, _loan, gascost, distribution):
    # add your keystore ID as an argument to this call
    print("Attempting flashloan")
    bal = acct.balance()
    print(bal)
    print(gascost)
    tx = "No tx"
    # hard code gas less than 0.04 ether
    if bal > 4 * gascost and gascost < 50000000000000000 and gasPrice > 0:
        print(tokens)
        print(distribution)
        gas = int(4 * gascost / gasPrice)
        print(gas)
        flashloan = MyFlashloanContract[1]
        tx = flashloan.flashloan(
            tokens, _loan, gascost * 4, distribution, {"from": acct, "gas": gas}
        )
        sys.exit()
    return tx


def arbAlt(tokens, _loan, gascost, distribution):
    # add your keystore ID as an argument to this call
    print("Attempting flashloan")
    bal = acct.balance()
    print(bal)
    print(gascost)
    tx = "No tx"
    # hard code gas less than 0.04 ether
    if bal > 4 * gascost and gascost < 50000000000000000 and gasPrice > 0:
        print(tokens)
        print(distribution)
        gas = int(4 * gascost / gasPrice)
        print(gas)
        flashloan = MyFlashloanContract[1]
        tx = flashloan.flashloan(
            tokens, _loan, 0, distribution, {"from": acct, "gas": gas}
        )
        sys.exit()
    return tx


def getGasPrice():
    global gasPrice
    gasPrice = web3.eth.gasPrice
    print("Gas price: ", gasPrice)


def getGasPrice2():
    # global gasPrice
    return web3.eth.gasPrice


def getMarkets():
    global markets
    markets = pickle.load(open("markets.dat", "rb"))
    # ag = requests.get("https://api-v2.dex.ag/markets")
    # # print(ag.json())
    # marketinfo = ag.json()
    # markets = marketinfo["AG"]
    # pickle.dump(markets, open("markets.dat", "wb"))


def getAddresses():
    global ercAddresses, contracts
    contracts = pickle.load(open("contracts.dat", "rb"))
    # ea = requests.get("https://api.1inch.exchange/v1.1/tokens")
    # ercAddresses = ea.json()
    # pickle.dump(ercAddresses, open("ercAddresses.dat", "wb"))
    # for key, value in ercAddresses.items():
    #     contracts[key] = web3.toChecksumAddress(value['address'])
    # pickle.dump(contracts, open("contracts.dat", "wb"))


def arbcheck():
    # global priceOfETH
    global gasPrice
    getGasPrice()
    getPrices()
    _loan = int(loan)

    for key, value in markets.items():
        marketname = key
        marketvalues = value
        splt = marketname.split("-")
        base = splt[0]
        quote = splt[1]

        process = False
        if base in baseAssets or quote in baseAssets:
            # if base == 'ETH' or quote == 'ETH':
            if marketname not in blacklist:
                if base in contracts.keys() and quote in contracts.keys():
                    process = True
        if process == True:

            # if base in baseAssets:
            if base == "ETH":

                try:
                    baseAddress = contracts[base]
                    quoteAddress = contracts[quote]
                    tokens = [baseAddress, quoteAddress, baseAddress]
                    # make call request to contract on the Ethereum blockchain
                    contract_response = (
                        one_inch_join.functions.getExpectedReturnWithGasMulti(
                            tokens, _loan, [parts, parts], [0, 0], [0, 0]
                        ).call({"from": str(acct)})
                    )

                    retAmount = contract_response[0][-1]
                    if retAmount > _loan:
                        processArb = True
                        estGas = contract_response[1]
                        distribution = contract_response[2]

                        # getGasPrice()
                        gascost = estGas * gasPrice

                        if processArb == True:
                            arb2 = 100 * (retAmount - gascost - _loan) / _loan
                            print(base, quote, arb2)
                            if arb2 > arbMargin:

                                tx = arb(tokens, _loan, gascost, distribution)
                                print(tx)
                    elif (100 * (retAmount - _loan) / _loan) < -90:
                        blacklist.append(marketname)

                except Exception as e:
                    print("An exception occurred", marketname)
                    print(e)
            elif quote == "ETH":

                try:
                    baseAddress = contracts[quote]
                    quoteAddress = contracts[base]
                    tokens = [baseAddress, quoteAddress, baseAddress]
                    # make call request to contract on the Ethereum blockchain
                    contract_response = (
                        one_inch_join.functions.getExpectedReturnWithGasMulti(
                            tokens, _loan, [parts, parts], [0, 0], [0, 0]
                        ).call({"from": str(acct)})
                    )

                    retAmount = contract_response[0][-1]
                    if retAmount > _loan:
                        processArb = True
                        estGas = contract_response[1]
                        distribution = contract_response[2]
                        # getGasPrice()
                        gascost = estGas * gasPrice

                        if processArb == True:
                            arb2 = 100 * (retAmount - gascost - _loan) / _loan
                            print(quote, base, arb2)
                            if arb2 > arbMargin:

                                tx = arb(tokens, _loan, gascost, distribution)
                                print(tx)
                    elif (100 * (retAmount - _loan) / _loan) < -90:
                        blacklist.append(marketname)

                except Exception as e:
                    print("An exception occurred", marketname)
                    print(e)
            else:
                try:
                    # ethcontract = contracts['ETH']
                    _altloan = _loan
                    _mult = 0
                    baseAddress = contracts[base]
                    quoteAddress = contracts[quote]
                    if base in baseAssets:
                        _altloan = int(_loan / prices[base])
                        _mult = 1 / prices[base]

                    else:
                        baseAddress = contracts[quote]
                        quoteAddress = contracts[base]
                        _altloan = int(_loan / prices[quote])
                        _mult = 1 / prices[quote]
                    tokens = [baseAddress, quoteAddress, baseAddress]
                    # make call request to contract on the Ethereum blockchain
                    contract_response = (
                        one_inch_join.functions.getExpectedReturnWithGasMulti(
                            tokens, _altloan, [parts, parts], [0, 0], [0, 0]
                        ).call({"from": str(acct)})
                    )

                    retAmount = contract_response[0][-1]
                    if retAmount > _altloan:
                        estGas = contract_response[1]
                        distribution = contract_response[2]
                        # getGasPrice()
                        gascost = estGas * gasPrice
                        arb2 = (
                            100 * (retAmount - _altloan - (gascost * _mult)) / _altloan
                        )
                        print(base, quote, arb2)
                        if arb2 > altarbMargin:
                            tx = arbAlt(tokens, _altloan, gascost, distribution)
                            print(tx)
                    elif (100 * (retAmount - _altloan) / _altloan) < -90:
                        blacklist.append(marketname)

                except Exception as e:
                    print("An exception occurred", marketname)
                    print(e)


def main():
    # getGasPrice()
    getAddresses()
    getMarkets()
    while 1 == 1:
        arbcheck()
        time.sleep(300)
