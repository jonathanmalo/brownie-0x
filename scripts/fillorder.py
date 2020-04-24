from decimal import Decimal, getcontext
from datetime import datetime, timedelta

from web3 import Web3

import zx_utils

faucet = accounts[0]
exchange = faucet.deploy(Exchange, zx_utils.CHAIN_ID)

accounts.add()
accounts.add()
maker = zx_utils.ZXAccount(accounts[-1], exchange)
taker = zx_utils.ZXAccount(accounts[-2], exchange)

cap = 10 ** 18
faucet.transfer(maker.account, cap)
faucet.transfer(taker.account, cap)

erc20proxy = faucet.deploy(ERC20Proxy)
weth = faucet.deploy(WETH9)
zrx = faucet.deploy(ZRXToken)

allowance = 2 ** 256 - 1
weth.approve(erc20proxy, allowance, {'from': taker.account})
zrx.approve(erc20proxy, allowance, {'from': maker.account})

deposit = taker.account.balance()
weth.deposit({'from': taker.account, 'value': deposit})
amount = 10 ** 21
zrx.transfer(maker.account, amount, {'from': faucet})

order_dict, sig = maker.zx_order(zrx, 801, weth, 1)
order = maker.zx_order_struct(order_dict)
getcontext().prec = 23
fill_amt = Decimal(20)/Decimal(182.76)
fill = Web3.toWei(fill_amt, 'ether')
tx = exchange.fillOrder(order, fill, sig, {'from': taker.account})
