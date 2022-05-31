echo_cmd ""
echo_cmd "Price"
echo_cmd ""

token_addrs="0x85f138bfEE4ef8e540890CFb48F620571d67Eda3
0xD31a59c85aE9D8edEFeC411D448f90841571b89c
0xB8c77482e45F1F44dE1745F52C74426C631bDD52
0x2260fac5e5542a773aa44fbcfedf7c193bc2c599
0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
0xD31a59c85aE9D8edEFeC411D448f90841571b89c
0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E
0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5
0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5
0xc7283b66Eb1EB5FB86327f08e1B5816b0720212B"

for token_addr in $token_addrs; do
    test_model 0 chainlink.price-usd '{"address": "'${token_addr}'"}' __all__
    test_model 0 price.oracle-chainlink '{"base": "'${token_addr}'", "quote": "USD"}' __all__
    test_model 0 price.oracle-chainlink '{"base": "'${token_addr}'", "quote": "JPY"}' __all__
    test_model 0 price.oracle-chainlink '{"base": "'${token_addr}'", "quote": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c"}' __all__
done