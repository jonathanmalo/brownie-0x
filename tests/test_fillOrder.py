import pytest
from decimal import Decimal, getcontext
from datetime import datetime, timedelta

from web3 import Web3

from brownie import accounts,\
    Exchange,\
    ERC20Proxy,\
    WETH9,\
    ZRXToken

from brownie.network.account import LocalAccount

import zx_utils

@pytest.fixture(scope="module")
def faucet():
    return accounts[0]

@pytest.fixture(scope="module")
def maker(exchange):
    accounts.add()
    assert isinstance(accounts[-1], LocalAccount)
    return zx_utils.ZXAccount(accounts[-1], exchange)

@pytest.fixture(scope="module")
def taker(exchange):
    accounts.add()
    assert isinstance(accounts[-2], LocalAccount)
    return zx_utils.ZXAccount(accounts[-2], exchange)

def test_fund(faucet, maker, taker):
    cap = 10 ** 18
    faucet.transfer(maker.account, cap)
    faucet.transfer(taker.account, 2 * cap)
    assert taker.account.balance() >= cap and \
        maker.account.balance() >= cap

@pytest.fixture(scope="module")
def exchange(faucet):
    return faucet.deploy(Exchange, zx_utils.CHAIN_ID)

@pytest.fixture(scope="module")
def erc20proxy(faucet):
    return faucet.deploy(ERC20Proxy)

def test_bridge_proxy(faucet, exchange, erc20proxy):
    assert exchange.registerAssetProxy(erc20proxy, {'from': faucet})
    assert erc20proxy.addAuthorizedAddress(exchange, {'from': faucet})

@pytest.fixture(scope="module")
def weth(faucet):
    return faucet.deploy(WETH9)

@pytest.fixture(scope="module")
def zrx(faucet):
    return faucet.deploy(ZRXToken)

def test_approve_tokens(maker, taker, weth, zrx, erc20proxy):
    allowance = 2 ** 256 - 1
    weth.approve(erc20proxy, allowance, {'from': taker.account})
    assert weth.allowance(taker.account, erc20proxy) == allowance
    zrx.approve(erc20proxy, allowance, {'from': maker.account})
    assert zrx.allowance(maker.account, erc20proxy) == allowance

def test_deposit_weth(taker, weth):
    deposit = 10 ** 18
    weth.deposit({'from': taker.account, 'value': deposit})
    assert weth.balanceOf(taker.account) == deposit

def test_transfer_zrx(faucet, maker, zrx):
    amount = 10 ** 21
    zrx.transfer(maker.account, amount, {'from': faucet})
    assert zrx.balanceOf(maker.account) == amount

def test_fillOrder(maker, taker, zrx, weth, exchange):
    # make an order selling zrx for weth
    order_dict, sig = maker.zx_order(zrx, 801, weth, 1)
    order = maker.zx_order_struct(order_dict)
    getcontext().prec = 23
    fill_amt = Decimal(20)/Decimal(182.76)
    fill = Web3.toWei(fill_amt, 'ether') # amount of weth taker sells in 1st tx
    fee = 10 ** 9
    exchange.fillOrder(order, fill, sig, {'from': taker.account, 'value': fee})
    assert zrx.balanceOf(taker.account) > 0
