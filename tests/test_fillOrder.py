import pytest
from decimal import Decimal, getcontext
from datetime import datetime, timedelta

from web3 import Web3
# brownie accounts new fund
# <enter private key>
# fund.json generated with: brownie accounts export fund
from brownie import accounts,\
    Exchange,\
    ERC20Proxy,\
    WETH9,\
    ZRXToken

import zx_utils

@pytest.fixture
def faucet():
    return accounts[0]

@pytest.fixture
def exchange(faucet):
    return faucet.deploy(Exchange, zx_utils.CHAIN_ID)

@pytest.fixture
def maker(exchange):
    return zx_utils.ZXAccount(accounts[-1], exchange)

@pytest.fixture
def taker(exchange):
    return zx_utils.ZXAccount(accounts[-2], exchange)

def test_fund(faucet, maker, taker):
    accounts.add()
    accounts.add()
    cap = 10 ** 18
    faucet.transfer(maker.account, cap)
    faucet.transfer(taker.account, cap)
    new_balance = 101000000000000000000
    assert maker.account.balance() == new_balance and \
        taker.account.balance() == new_balance

@pytest.fixture
def erc20proxy(faucet):
    return faucet.deploy(ERC20Proxy)

@pytest.fixture
def weth(faucet):
    return faucet.deploy(WETH9)

@pytest.fixture
def zrx(faucet):
    return faucet.deploy(ZRXToken)

def test_approve_tokens(maker, taker, weth, zrx, erc20proxy):
    allowance = 2 ** 256 - 1
    weth.approve(erc20proxy, allowance, {'from': taker.account})
    assert weth.allowance(taker.account, erc20proxy) == allowance
    zrx.approve(erc20proxy, allowance, {'from': maker.account})
    assert zrx.allowance(maker.account, erc20proxy) == allowance

def test_deposit_weth(taker, maker, weth):
    deposit = taker.account.balance()
    weth.deposit({'from': taker.account, 'value': deposit})
    weth.deposit({'from': maker.account, 'value': deposit})
    assert weth.balanceOf(taker.account) == deposit and \
        weth.balanceOf(maker.account) == deposit

def test_transfer_zrx(faucet, taker, maker, zrx):
    amount = 10 ** 21
    zrx.transfer(taker.account, amount, {'from': faucet})
    zrx.transfer(maker.account, amount, {'from': faucet})
    assert zrx.balanceOf(taker.account) == amount and \
        zrx.balanceOf(maker.account) == amount

def test_fillOrder(maker, taker, zrx, weth, exchange):
    # make an order selling zrx for weth
    order_dict, sig = maker.zx_order(zrx, 801, weth, 1)
    order = maker.zx_order_struct(order_dict)
    getcontext().prec = 23
    fill_amt = Decimal(20)/Decimal(182.76)
    fill = Web3.toWei(fill_amt, 'ether') # amount of weth taker sells in 1st tx
    taker_initial_balance = zrx.balanceOf(taker.account)
    exchange.fillOrder(order, fill, sig, {'from': taker.account})
    assert zrx.balanceOf(taker.account) > taker_initial_balance
