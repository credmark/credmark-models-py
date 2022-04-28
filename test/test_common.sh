#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ]
then
    echo -e "\nRun model tests\n"
    echo "Usage: $0 [test] [gen]"
    echo ""
    echo -e "In normal mode it uses the credmark-dev script and the gateway api.\n"
    echo 'In "test" mode it uses test/test.py and a local model-runner-api.'
    echo ""
    echo "If \"gen\" is specified, the tests will not run and the ${SCRIPT_DIRECTORY}/run_all_examples[_test].sh file will be generated instead."
    echo ""
    exit 0
fi

other_opts=' --format_json'

# echo "${@: -1: 1} | ${@: -2: 1} $#"

# test/run.sh test 10 gen
# test/run.sh 10 gen
# test/run.sh gen
# test/run.sh test gen

# test/run.sh
# test/run.sh test
# test/run.sh 0
# test/run.sh test 0


if [ "${@: -1: 1}" == 'gen' ]
then
    gen_mode=1
    if [ $# -eq 1 ]; then
        start_n=0
        test_mode='prod'
    elif [ "${@: -2: 1}" == "test" ]; then
        start_n=0
        test_mode='test'
    else
        start_n=${@: -2: 1}
        if [ $# -eq 3 ] && [ "$1" -eq "test" ]; then
            test_mode='test'
        else
            test_mode='prod'
        fi
    fi
else
    gen_mode=0
    if [ $# -eq 0 ]; then
        start_n=0
        test_mode='prod'
    elif [ "${@: -1: 1}" == "test" ]; then
        start_n=0
        test_mode='test'
    else
        start_n=${@: -1: 1}
        if [ $# -eq 2 ] && [ "$1" == "test" ]; then
            test_mode='test'
        else
            test_mode='prod'
        fi
    fi
fi

start_n=`expr $start_n + 1 - 1`
echo Start from: $start_n


if [ "${test_mode}" == 'test' ]; then
    cmk_dev='python test/test.py'
    # Use prod for test:
    # api_url=' --api_url=http://localhost:8700'
    api_url=''
    cmd_file=$SCRIPT_DIRECTORY/run_all_examples_test.sh
    echo In test mode, using ${cmk_dev} and ${api_url}
elif [ "${test_mode}" == 'prod' ];
then
    cmk_dev='credmark-dev'
    api_url=''  # no api url param uses the gateway api
    cmd_file=$SCRIPT_DIRECTORY/run_all_examples.sh
    echo Using installed credmark-dev and gateway api.
else
    exit
fi

block_number='-b 14234904'

if [ $gen_mode -eq 1 ]; then
    echo "Sending commands to ${cmd_file}"
    echo -e "#!/bin/bash\n" > $cmd_file
    if [ `which chmod` != '' ]
    then
        chmod u+x $cmd_file
    fi
fi

set +x

count_pass=0

run_model () {
    model=$1
    input=$2
    local_models=$3

    if [ $# -eq 2 ]; then
        if [ $gen_mode -eq 1 ]; then
            echo "${cmk_dev} run ${model} --input '${input}' ${block_number}${api_url}${other_opts}" >> $cmd_file
        else
            echo "Running ($count_pass): ${cmk_dev} run ${model} --input '${input}' ${block_number}${api_url}${other_opts}"
            ${cmk_dev} run ${model} --input "${input}" ${block_number}${api_url}${other_opts}
        fi
    elif [ $# -eq 3 ]; then
        if [ "$3" == 'print-command' ]; then
            echo "${cmk_dev} run ${model} --input '${input}' ${block_number}${api_url}${other_opts}"
        else
            if [ $gen_mode -eq 1 ]; then
                echo "${cmk_dev} run ${model} --input '${input}' -l ${local_models} ${block_number}${api_url}${other_opts}" >> $cmd_file
            else
                echo "Running ($count_pass): ${cmk_dev} run ${model} --input '${input}' -l ${local_models} ${block_number}${api_url}${other_opts}"
                ${cmk_dev} run ${model} --input "${input}" -l ${local_models} ${block_number}${api_url}${other_opts}
            fi
        fi
    elif [ $# -eq 4 ]; then
        if [ "$4" == 'print-command' ]; then
            echo "${cmk_dev} run ${model} --input '${input}' -l ${local_models} ${block_number}${api_url}${other_opts}"
        else
            echo "Got unexpected test arguments=$*"
            exit
        fi
    else
        echo "Got unexpected test arguments=$*"
        exit
    fi
}

test_model () {
    expected=$1
    model=$2
    input=$3

    count_pass=`expr $count_pass + 1`
    # echo $start_n $count_pass
    if [ $start_n -gt 0 ];
    then
        if [ $start_n -eq $count_pass ];
        then
            echo "Start test from case ${start_n}"
        elif [ $start_n -gt $count_pass ];
        then
            echo "Skip test($count_pass) till ${start_n}"
            return
        fi
    fi

    if [ $# -eq 3 ]; then
        local_models=
    elif [ $# -eq 4 ]; then
        local_models=$4
    else
        echo "Test(${count_pass}) got unexpected test arguments=$*"
        exit
    fi

    cmd="$(run_model $model "$input" $local_models print-command)"

    if [ $expected -ne 0 ] && [ $expected -ne 1 ] && [ $expected -ne 2 ] && [ $expected -ne 3 ]
    then
        echo "Test(${count_pass}) got unexpected expected=${expected} for ${cmd}"
        exit
    fi

    run_model $model "$input" $local_models
    exit_code=$?

    if [ $gen_mode -eq 0 ];
    then
        if [ $exit_code -ne $expected ];
        then
            echo Failed test with $cmd
            echo "Test(${count_pass}) stopped with unexpected exit code: $exit_code != $expected."
            exit
        else
            echo "Passed test(${count_pass}) with $cmd"
        fi
    else
        echo "Test(${count_pass}) sent $cmd to $cmd_file"
    fi
}

echo_cmd () {
    echo $1
    if [ $gen_mode -eq 1 ]; then
        echo "echo \"$1\"" >> $cmd_file
    fi
}


token_price_deps='token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price'
var_deps=finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,${token_price_deps}