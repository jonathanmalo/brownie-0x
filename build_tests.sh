#!/bin/bash

# get 0x contracts v3.0
if [[ ! -d "0x-monorepo" ]]
then
    git clone git@github.com:0xProject/0x-monorepo.git
    cd 0x-monorepo
    git checkout -b 3.0
    cd ../
fi

# initialize project
if [[ -d "zx" ]]
then    
    rm -rf zx
fi
GIT_ZX=0x-monorepo/contracts
LOC_ZX=zx/contracts/exchange
mkdir zx && cd zx
brownie init
cd ../

# copy contracts from git repo to brownie project
mkdir $LOC_ZX
cp -r $GIT_ZX/exchange/contracts/src/* $LOC_ZX
cp -r $GIT_ZX/asset-proxy   $LOC_ZX/contracts-asset-proxy
cp -r $GIT_ZX/exchange-libs $LOC_ZX/contracts-exchange-libs
cp -r $GIT_ZX/utils         $LOC_ZX/contracts-utils
cp -r $GIT_ZX/erc20         $LOC_ZX/contracts-erc20
cp -r $GIT_ZX/staking       $LOC_ZX/contracts-staking
cp -r $GIT_ZX/erc1155       $LOC_ZX/contracts-erc1155

# delete unnecessary files from 0x repo
# cp MANIFEST $LOC_ZX
cd $LOC_ZX
# WORKDIR=$PWD
# erase files not in dependency manifest
# [[ "$PWD" =~ "$WORKDIR/$LOC_ZX" ]] && \
#     (find ./ -type f -printf "%P\n"; cat MANIFEST MANIFEST; echo MANIFEST) |
# 	sort | uniq -u | xargs -r rm && \
# 	    echo "0x files deleted"

# prevent namespace collisions by refactoring contract names
cd contracts-asset-proxy
egrep -lRZ ' MixinAssetProxyDispatcher' . | xargs -0 -l sed -i -e 's/\sMixinAssetProxyDispatcher/ MixinAssetProxyDispatcher_/g'
egrep -lRZ ' IAssetProxyDispatcher' . | xargs -0 -l sed -i -e 's/\sIAssetProxyDispatcher/ IAssetProxyDispatcher_/g'
egrep -lRZ ' IAssetProxy' . | xargs -0 -l sed -i -e 's/\sIAssetProxy/ IAssetProxy_/g'
egrep -lRZ ' Ownable' . | xargs -0 -l sed -i -e 's/\sOwnable/ Ownable_/g'
egrep -lRZ ' IAuthorizable' . | xargs -0 -l sed -i -e 's/\sIAuthorizable/ IAuthorizable_/g'
cd ../contracts-exchange-libs
egrep -lRZ ' IWallet' . | xargs -0 -l sed -i -e 's/\sIWallet/ IWall/g'
cd ../contracts-erc20
sed -i -e 's/\sERC20Token/ ERC20Token_/g' contracts/src/ZRXToken.sol
cd ../contracts-staking
sed -i -e 's/\sIAssetProxy/ IAssetProxy_/g' contracts/src/ZrxVault.sol

cd ../../../
cp ../tests/* tests
cp ../_brownie-config.yaml ./brownie-config.yaml

# exclude tests and bridges from compilation
ERC20_TESTS=contracts/exchange/contracts-asset-proxy/contracts/
mv $ERC20_TESTS/test $ERC20_TESTS/_test
mv $ERC20_TESTS/src/bridges $ERC20_TESTS/src/_bridges

# change compiler version on ZRXToken
cd ../
patch $LOC_ZX/contracts-erc20/contracts/src/ZRXToken.sol -i patches/ZRXToken.patch

cd zx
brownie networks add Development testzx host=http://localhost:8545 cmd=ganache-cli gas_limit=8000000
brownie test
