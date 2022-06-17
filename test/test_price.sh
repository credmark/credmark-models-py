echo_cmd ""
echo_cmd "Price"
echo_cmd ""

token_addrs="0xFEEf77d3f69374f66429C91d732A244f074bdf74
0x6c3f90f043a72fa612cbac8115ee7e52bde6e490"

for token_addr in $token_addrs; do
    test_model 0 price.dex-curve-fi '{"address":"'${token_addr}'"}'
    test_model 0 price.quote '{"base": {"address":"'${token_addr}'"}}'
done


echo_cmd ""
echo_cmd "Chainlink Oracle Price"
echo_cmd ""

# 0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E ilv
# 0x383518188C0C6d7730D91b2c03a03C837814a899 ohm-eth.data.eth
# 0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5 ohmv2-eth.data.eth
# 0xc7283b66Eb1EB5FB86327f08e1B5816b0720212B tribe-eth.data.eth
# 0xFEEf77d3f69374f66429C91d732A244f074bdf74 price-curve

tokens="
BTC
USD
ETH
CNY
USDC
GBP
0x85f138bfEE4ef8e540890CFb48F620571d67Eda3
0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750
0xD31a59c85aE9D8edEFeC411D448f90841571b89c
0xB8c77482e45F1F44dE1745F52C74426C631bDD52
0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
0xD31a59c85aE9D8edEFeC411D448f90841571b89c
0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E
0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5
0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5
0xc7283b66Eb1EB5FB86327f08e1B5816b0720212B
0x2260fac5e5542a773aa44fbcfedf7c193bc2c599
0x383518188C0C6d7730D91b2c03a03C837814a899
"

block_number_backup=${block_number}
block_number='-b 14878712'

models="price.quote price.oracle-chainlink"

for price_model in $models; do
    for token_addr in $tokens; do
        if [[ "$token_addr" =~ ^0x ]]; then
            token_addr_ext='{"address":"'${token_addr}'"}'
        else
            token_addr_ext='{"symbol":"'${token_addr}'"}'
        fi

        test_model 0 $price_model '{"base": '${token_addr_ext}', "quote": {"symbol":"USD"}}' __all__
        test_model 0 $price_model '{"quote": '${token_addr_ext}', "base": {"symbol":"USD"}}' __all__
        test_model 0 $price_model '{"base": '${token_addr_ext}', "quote": {"symbol":"JPY"}}' __all__
        test_model 0 $price_model '{"quote": '${token_addr_ext}', "base": {"symbol":"JPY"}}' __all__
        test_model 0 $price_model '{"base": '${token_addr_ext}', "quote": {"symbol":"GBP"}}' __all__
        test_model 0 $price_model '{"quote": '${token_addr_ext}', "base": {"symbol":"GBP"}}' __all__
        test_model 0 $price_model '{"base": '${token_addr_ext}', "quote": {"address":"0xD31a59c85aE9D8edEFeC411D448f90841571b89c"}}' __all__
        test_model 0 $price_model '{"quote": '${token_addr_ext}', "base": {"address":"0xD31a59c85aE9D8edEFeC411D448f90841571b89c"}}' __all__
    done
done

tokens="0xFEEf77d3f69374f66429C91d732A244f074bdf74"

models="price.quote price.dex-curve-fi"

for price_model in $models; do
    for token_addr in $tokens; do
        if [[ "$token_addr" =~ ^0x ]]; then
            token_addr_ext='{"address":"'${token_addr}'"}'
        else
            token_addr_ext='{"symbol":"'${token_addr}'"}'
        fi

        test_model 0 $price_model '{"base": '${token_addr_ext}', "quote": {"symbol":"USD"}}' __all__
        test_model 0 $price_model '{"quote": '${token_addr_ext}', "base": {"symbol":"USD"}}' __all__
    done
done

exit


echo_cmd ""
echo_cmd "Price2"
echo_cmd ""

# ALGO BYTOM NEAR
# CAKE: 0x7c8161545717a334f3196e765d9713f8042EF338 Wormhole
for tok in "0x111111111117dC0aa78b770fA6A738034120C302 0" \
"0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9 0" \
"0xEd04915c23f00A313a544955524EB7DBD823143d 0" \
"0xADE00C28244d5CE17D72E40330B1c318cD12B7c3 0" \
"0x8Ab7404063Ec4DBcfd4598215992DC3F8EC853d7 0" \
"0x00a8b738E453fFd858a7edf03bcCfe20412f0Eb0 0" \
"0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF 0" \
"0xa1faa113cbE53436Df28FF0aEe54275c13B40975 0" \
"0xfF20817765cB7f73d4bde2e66e067E58D11095C2 0" \
"0xd46ba6d942050d489dbd938a2c909a5d5039a161 0" \
"0x8290333cef9e6d528dd5618fb97a76f268f3edd4 0" \
"0xa117000000f279d81a1d3cc75430faa017fa5a2e 0" \
"0x4d224452801aced8b2f0aebe155379bb5d594381 0" \
"0xA9B1Eb5908CfC3cdf91F9B8B3a74108598009096 0" \
"0x18aAA7115705e8be94bfFEBDE57Af9BFc265B998 0" \
"0xbb0e17ef65f82ab018d8edd776e8dd940327b28b 0" \
"0x3472a5a71965499acd81997a54bba8d852c6e53d 0" \
"0xba100000625a3754423978a60c9317c58a424e3d 0" \
"0xba11d00c5f74255f56a5e366f4f77f5a186d7f55 0" \
"0x0d8775f648430679a709e98d2b0cb6250d2887ef 0" \
"0xf17e65822b568b3903685a7c9f496cf7656cc6c2 0" \
"0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5 0" \
"0xb8c77482e45f1f44de1745f52c74426c631bdd52 0" \
"0xb8c77482e45f1f44de1745f52c74426c631bdd52 0" \
"0x1f573d6fb3f13d689ff844b4ce37794d79a7ff1c 0" \
"0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750 0" \
"0x4fabb145d64652a948d72533023f6e7a623c7c53 0" \
"0xaaaebe6fe48e54f431b0c390cfaf0b017d09d42d 0" \
"0x4f9254c83eb525f9fcf346490bbb3ed28a81c667 0" \
"0xc00e94cb662c3520282e6f5717214004a7f26888 0" \
"0x2ba592f78db6436527729929aaf6c908497cb200 0" \
"0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b 0" \
"0xd533a949740bb3306d119cc777fa900ba034cd52 0" \
"0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b 0" \
"0x6b175474e89094c44da98b954eedeac495271d0f 0" \
"0x0abdace70d3790235af448c88547603b945604ea 0" \
"0x43dfc4159d86f3a37a5a4b3d4580b888ad7d4ddd 0" \
"0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b 0" \
"0x92d6c1e31e14520e676a687f0a93788b716beff5 0" \
"0xf629cbd94d3791c9250152bd8dfbdf380e2a3b9c 0" \
"0xc18360217d8f7ab5e7c516566761ea12ce7f9d72 0" \
"0xa0246c9032bc3a600820415ae600c6388619a14d 0" \
"0x956f47f50a910163d8bf957cf5846d573e7f87ca 0" \
"0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85 0" \
"0xc770eefad204b5180df6a14ee197d99d808ee52d 0" \
"0x853d955acef822db058eb8505911ed77f175b99e 0" \
"0x4e15361fd6b4bb609fa63c81a2be19d873717870 0" \
"0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9 0" \
"0x3432b6a60d23ca0dfca7761b7ab56459d9c964d0 0" \
"0x6810e776880c02933d47db1b9fc05908e5386b96 0" \
"0xc944e90c64b2c07662a292be6244bdf05cda44a7 0" \
"0xc944e90c64b2c07662a292be6244bdf05cda44a7 0" \
"0xde30da39c46104798bb5aa3fe8b9e0e1f348163f 0" \
"0x056fd409e1d7a124bd7017459dfea2f387b6d5cd 0" \
"0x584bc13c7d411c00c01a62e8019472de68768430 0" \
"0x6f259637dcd74c767781e37bc6133cd6a68aa161 0" \
"0xdf574c24545e5ffecb9a659c229253d4111d87e1 0" \
"0x767fe9edc9e0df98e07454847909b5e959d7ca0e 0" \
"0xfa1a856cfa3409cfa145fa4e20eb270df3eb21ab 0" \
"0xdd974d5c2e2928dea5f71b9825b8b646686bd200 0" \
"0x1ceb5cb57c4d4e2b2433641b95dd330a33185a44 0" \
"0x5a98fcbea516cf06857215779fd812ca3bef1b32 0" \
"0x514910771af9ca656af840dff83e8264ecf986ca 0" \
"0xbbbbca6a901c926f240b89eacb641d8aec7aeafd 0" \
"0x5f98805a4e8be255a32880fdec7f6728c6568ba0 0" \
"0x0f5d2fb29fb7d3cfee444a200298f468908cc942 0" \
"0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0 0" \
"0x99d8a9c45b2eca8864373a26d1459e3dff1e17f3 0" \
"0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 0" \
"0xec67005c4e498ec7f55e092bd1d35cbc47c91892 0" \
"0x1776e1f26f98b1a5df9cd347953a26dd3cb46671 0" \
"0x967da4048cd07ab37855c090aaf366e4ce1b9f48 0" \
"0x64aa3364f17a4d01c6f1751fd97c2bd3d7e7f1d5 0" \
"0x75231f58b43240c9718dd58b4967c5114342a86c 0" \
"0xd26114cd6ee289accf82350c8d8487fedb8a0c07 0" \
"0xd26114cd6ee289accf82350c8d8487fedb8a0c07 0" \
"0x8e870d67f660d95d5be530380d0ec0bd388289e1 0" \
"0x45804880de22913dafe09f4980848ece6ecbaf78 0" \
"0xbc396689893d065f41bc2c6ecbee5e0085233447 0" \
"0x03ab458634910aad20ef5f1c8ee96f1d6ac54919 0" \
"0xfca59cd816ab1ead66534d82bc21e7515ce441cf 0" \
"0x408e41876cccdc0f92210600ef50372656052a38 0" \
"0x221657776846890989a759BA2973e427DfF5C9bB 0" \
"0x8f8221afbb33998d8584a2b05749ba73c37a938a 0" \
"0x607f4c5bb672230e8672085532f7e901544a7375 0" \
"0x8762db106b2c2a0bccb3a80d1ed41273552616e8 0" \
"0x3845badade8e6dff049820680d1f14bd3903a5d0 0" \
"0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce 0" \
"0xcc8fa225d80b9c7d42f96e9570156c65d6caaa25 0" \
"0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f 0" \
"0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f 0" \
"0x090185f2135308bad17527004364ebcc2d37e5f6 0" \
"0x476c5e26a75bd202a9683ffd34359c0cc15be0ff 0" \
"0x0ae055097c6d159879521c384f1d2123d1f195e6 0" \
"0x57ab1ec28d129707052df4df418d58a2d46d5f51 0" \
"0x6b3595068778dd592e39a122f4f5a5cf09c90fe2 0" \
"0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9 0" \
"0x2e9d63788249371f1dfc918a52f8d799f4a38c94 0" \
"0xc7283b66eb1eb5fb86327f08e1b5816b0720212b 0" \
"0x0000000000085d4780b73119b644ae5ecd22b376 0" \
"0x04fa0d235c4abf4bcf4787af4cf447de572ef828 0" \
"0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 0" \
"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 0" \
"0x674c6ad92fd080e4004b2312b45f796a192d27a0 0" \
"0xdac17f958d2ee523a2206206994597c13d831ec7 0" \
"0x2260fac5e5542a773aa44fbcfedf7c193bc2c599 0" \
"0x4691937a7508860f876c9c0a2a617e7d9e945d4b 0" \
"0x8798249c2e607446efb7ad49ec89dd1865ff4272 0" \
"0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e 0" \
"0x25f8087ead173b73d6e8b84329989a8eea16cf73 0" \
"0xe41d2489571d322189246dafa5ebde1f4699f498 0" \
"0xe41d2489571d322189246dafa5ebde1f4699f498 0" \
"0x57ab1ec28d129707052df4df418d58a2d46d5f51 0" \
"0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE 0" \
"0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB 0" \
"0x0000000000000000000000000000000000000348 0" \
"0xa1d0E215a23d7030842FC67cE582a6aFa3CCaB83 0" \
"0xBe1a001FE942f96Eea22bA08783140B9Dcc09D28 0" \
"0x0391D2021f89DC339F60Fff84546EA23E337750f 0" \
"0xAE12C5930881c53715B369ceC7606B70d8EB229f 0" \
"0xE452E6Ea2dDeB012e20dB73bf5d3863A3Ac8d77a 0" \
"0x491604c0FDF08347Dd1fa4Ee062a822A5DD06B5D 0" \

do
    set -- $tok
    test_model $2 price.oracle-chainlink '{"base": "'$1'", "quote": "USD"}'
done

block_number=${block_number_backup}

exit
