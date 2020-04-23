from decimal import Decimal
from time import time
from datetime import datetime, timedelta

from web3 import Web3

from zero_ex.contract_wrappers.exchange.types import Order
from zero_ex.order_utils import generate_order_hash_hex
from zero_ex.order_utils.asset_data_utils import encode_erc20

from eth_account.messages import encode_defunct

from brownie import accounts
from brownie.network.account import LocalAccount
from brownie.network.contract import ContractContainer

CHAIN_ID = 1337
ZERO_UINT256 = '0x0000000000000000000000000000000000000000'
TEST_IP = "http://localhost:8545"
TEST_PROVIDER = Web3.HTTPProvider(TEST_IP)
TEST_NODE = Web3(TEST_PROVIDER)

class ZXAccount:

    _default_address = Web3.toChecksumAddress(ZERO_UINT256)
    _default_zx_order_expiry = round(
        (datetime.utcnow() + timedelta(days=1)).timestamp()
    )
    _default_asset_data = ((0).to_bytes(1, byteorder='big') * 20)
    _default_salt = int(time()*1000)
    _chain_id = CHAIN_ID
    _node = TEST_NODE
    account = None

    def __init__(self, account: LocalAccount, zx_exchange: ContractContainer):
        self.account = account
        self.zx_exchange = zx_exchange

    def sign(self, msg=None, node=_node):
        if isinstance(msg, bytes):
            message = encode_defunct(msg)
        elif isinstance(msg, str):
            message = encode_defunct(hexstr=msg)
        else:
            raise Exception("Only string or bytes are signable.")
        return node.eth.account.sign_message(message, private_key=self.account.private_key)

    def _is_valid_signature(self, hash_str: str, sig: bytes):
        data = bytes.fromhex(hash_str.replace("0x", ""))
        return self.zx_exchange.isValidHashSignature(data, self.account.address, sig)

    def pad_int(self, num: int):
        return num.to_bytes(32, byteorder="big")

    def _sign_order_hash(self, hash_str: str):
        sig = self.sign(msg=hash_str)
        if sig.v == 0 or sig.v == 1:
            sig.v += 27
        vrs_sig = (
            sig.v.to_bytes(1, byteorder="big") +
            self.pad_int(sig.r) +
            self.pad_int(sig.s) +
            b"\x03"
        )
        vrs_valid = self._is_valid_signature(hash_str, vrs_sig)
        if vrs_valid is True:
            return vrs_sig
        else:
            raise Exception("Invalid ZeroEx Exchange Signature")

    def zx_order(self,
                 maker_asset_contract,
                 maker_asset_amount: Decimal,
                 taker_asset_contract,
                 taker_asset_amount: Decimal,
                 taker_address: str = _default_address,
                 sender_address: str = _default_address,
                 fee_recipient_address: str = _default_address,
                 salt=_default_salt,
                 maker_fee=0,
                 taker_fee=0,
                 expiration_time=_default_zx_order_expiry,
                 maker_fee_asset_data=_default_asset_data,
                 taker_fee_asset_data=_default_asset_data):
        order = Order(
            makerAddress=self.account.address,
            takerAddress=taker_address,
            senderAddress=sender_address,
            feeRecipientAddress=fee_recipient_address,
            makerAssetData=encode_erc20(maker_asset_contract.address),
            takerAssetData=encode_erc20(taker_asset_contract.address),
            salt=salt,
            makerFee=maker_fee,
            takerFee=taker_fee,
            makerAssetAmount=Web3.toWei(maker_asset_amount, 'ether'),
            takerAssetAmount=Web3.toWei(taker_asset_amount, 'ether'),
            expirationTimeSeconds=expiration_time,
            makerFeeAssetData=maker_fee_asset_data,
            takerFeeAssetData=taker_fee_asset_data
        )
        order_hash = generate_order_hash_hex(order, self.zx_exchange.address, self._chain_id)
        # TODO: make compatible with 0x-order-utils
        # order_sig = sign_hash(TEST_PROVIDER, self.account.address, order_hash)
        order_sig = self._sign_order_hash(order_hash)
        return order, order_sig

    def zx_order_struct(self, order: Order):
        canonical_keys = [
            'makerAddress', 'takerAddress', 'feeRecipientAddress',
            'senderAddress', 'makerAssetAmount', 'takerAssetAmount',
            'makerFee', 'takerFee', 'expirationTimeSeconds', 'salt',
            'makerAssetData', 'takerAssetData', 'makerFeeAssetData',
            'takerFeeAssetData'
        ]
        return [order[key] for key in canonical_keys]
