#!/bin/bash

if [[ ! -d "0x-monorepo" ]]
then
    git clone git@github.com:0xProject/0x-monorepo.git
fi

WORKDIR=$PWD

if [[ -d "zx" ]]
then    
    rm -rf zx
fi

GIT_ZX=0x-monorepo/contracts
LOC_ZX=zx/contracts/exchange
mkdir zx && cd zx
brownie init
cd ../

mkdir $LOC_ZX

# Exchange dependencies
cp -r $GIT_ZX/exchange/contracts/src/* $LOC_ZX
cp -r $GIT_ZX/asset-proxy   $LOC_ZX/contracts-asset-proxy
cp -r $GIT_ZX/erc20         $LOC_ZX/contracts-erc20
cp -r $GIT_ZX/exchange-libs $LOC_ZX/contracts-exchange-libs
cp -r $GIT_ZX/staking       $LOC_ZX/contracts-staking
cp -r $GIT_ZX/utils         $LOC_ZX/contracts-utils

# ERC20Proxy dependencies
cp -r $GIT_ZX/erc1155 $LOC_ZX/contracts-erc1155
cp MANIFEST $LOC_ZX
cd $LOC_ZX

# erase files not in dependency manifest
[[ "$PWD" =~ "$WORKDIR/$LOC_ZX" ]] && \
    (find ./ -type f -printf "%P\n"; cat MANIFEST MANIFEST; echo MANIFEST) |
	sort | uniq -u | xargs -r rm && \
	    echo "0x files deleted"

cd ../../
cp ../_brownie-config.yaml ./brownie-config.yaml

# exclude asset-proxy tests from compilation
ERC20_TESTS=contracts/exchange/contracts-asset-proxy/contracts/
mv $ERC20_TESTS/test $ERC20_TESTS/_test
cd ../

# patches to prevent namespace conflicts, either by using one 
# version of a contract or by changing the name of a contract
patch -u $LOC_ZX/MixinSignatureValidator.sol -i patches/MixinSignatureValidator.patch
patch -u $LOC_ZX/contracts-asset-proxy/contracts/src/MultiAssetProxy.sol -i patches/MultiAssetProxy.patch
patch -u $LOC_ZX/contracts-asset-proxy/contracts/archive/Ownable.sol -i patches/Ownable.patch
patch -u $LOC_ZX/contracts-asset-proxy/contracts/archive/MixinAssetProxyDispatcher.sol -i patches/MixinAssetProxyDispatcher_AssetProxy.patch
patch -u $LOC_ZX/MixinAssetProxyDispatcher.sol -i patches/MixinAssetProxyDispatcher_Exchange.patch
patch -u $LOC_ZX/contracts-asset-proxy/contracts/archive/MixinAuthorizable.sol -i patches/MixinAuthorizable.patch

cd zx
brownie compile
