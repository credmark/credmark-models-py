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

if [ $# -ge 1 ] && [ $1 == 'test' ]
then
    test_mode='test'
    cmk_dev='python test/test.py'
    # Use prod for test:
    # api_url=' --api_url=http://localhost:8700'
    api_url=''
    block_number='-b 14234904'
    cmd_file=$SCRIPT_DIRECTORY/run_all_examples_test.sh
    echo In test mode, using ${cmk_dev} and ${api_url}
else
    test_mode='prod'
    cmk_dev='credmark-dev'
    api_url=''  # no api url param uses the gateway api
    block_number='-b 14234904'
    cmd_file=$SCRIPT_DIRECTORY/run_all_examples.sh
    echo Using installed credmark-dev and gateway api.
fi

if ([ $# -eq 2 ] && [ $2 == 'gen' ]) || ([ $# -eq 1 ] && [ $1 == 'gen' ])
then
    gen_cmd=1
else
    gen_cmd=0
fi

if [ $gen_cmd -eq 1 ]; then
    echo "Sending commands to ${cmd_file}"
    echo -e "#!/bin/bash\n" > $cmd_file
    if [ `which chmod` != '' ]
    then
        chmod u+x $cmd_file
    fi
fi

set +x

run_model () {
    model=$1
    input=$2
    if [ $# -eq 3 ] && [ $3 == 'print-command' ]
    then
        echo "${cmk_dev} run ${model} --input '${input}' ${block_number}${api_url}"
    else
        if [ $gen_cmd -eq 1 ]; then
            echo "${cmk_dev} run ${model} --input '${input}' ${block_number}${api_url}" >> $cmd_file
        else
            echo "Running: ${cmk_dev} run ${model} --input '${input}' ${block_number}${api_url}"
            ${cmk_dev} run ${model} --input "${input}" ${block_number}${api_url}
        fi
    fi
}

test_model () {
    expected=$1
    model=$2
    input=$3
    cmd="$(run_model $model "$input" print-command)"

    if [ $expected -ne 0 ] && [ $expected -ne 1 ]
    then
        echo "Got unexpected expected=${expected} for ${cmd}"
        exit
    fi

    run_model $model "$input"
    exit_code=$?

    if [ $gen_cmd -eq 0 ]
    then
        if [ $exit_code -ne $expected ]
        then
            echo Failed test with $cmd
            echo "Stopped with unexpected exit code: $exit_code != $expected."
            exit
        else
            echo Passed test with $cmd
        fi
    else
        echo Sent $cmd to $cmd_file
    fi
}

echo_cmd () {
    echo $1
    if [ $gen_cmd -eq 1 ]; then
        echo "echo \"$1\"" >> $cmd_file
    fi
}
