1. Install Brownie using pipx: `pipx install brownie`
2. Inject project dependencies: `pipx inject eth-brownie 0x-order-utils`
3. `build_tests.sh` clones and patches, then compiles the 0x contracts, then tests the fillOrder method on the Exchange contract using brownie:
```
./build_tests.sh
```
Repeatedly executing the script will produce a new brownie project in the `zx` directory. The 0x contracts can be tested by entering this directory and using the `brownie console` command.
