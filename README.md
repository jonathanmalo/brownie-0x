`build_tests.sh` clones and patches, then compiles and tests the fillOrder method on the Exchange contract using brownie:
```
./build_tests.sh
```
Repeatedly executing the script will produce a new brownie project in the `zx` directory. The 0x contracts can be tested by entering this directory and using the `brownie console` command.
