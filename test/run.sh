#!/bin/bash

if [ "`which realpath`" == '' ]
then
   FULL_PATH_TO_SCRIPT="${BASH_SOURCE[0]}"
else
   FULL_PATH_TO_SCRIPT="$(realpath "${BASH_SOURCE[-1]}")"
fi

SCRIPT_DIRECTORY="$(dirname "$FULL_PATH_TO_SCRIPT")"

source $SCRIPT_DIRECTORY/test_common.sh

${cmk_dev} list | awk -v script_dir=$SCRIPT_DIRECTORY -v test_scripts=examples,account_token,cmk,aave,compound,uniswap,sushiswap,curve,finance 'BEGIN {
        split(test_scripts,test_files,",")
        for (i in test_files) {
            test_files[i] = script_dir "/" "test_" test_files[i] ".sh"
        }
        total_test_files=length(test_files)
    }
    {
    print $0
    if ($0 ~ / - /) {
        m=substr($2, 0, length($2)-1)
        res=""
        for (i in test_files) {
            command = ("grep " m " " test_files[i])
            ( command | getline res )
            if (res != "") {
                break
            } else {
                if (i == total_test_files) {
                    print "(Test check) No test for " m
                }
            }
        }
        close(command)
    }
}'

if [ $gen_mode -eq 1 ]; then
    echo "${cmk_dev} list" >> $cmd_file
fi

source $SCRIPT_DIRECTORY/test_examples.sh
source $SCRIPT_DIRECTORY/test_account_token.sh
source $SCRIPT_DIRECTORY/test_cmk.sh
source $SCRIPT_DIRECTORY/test_aave.sh
source $SCRIPT_DIRECTORY/test_compound.sh
source $SCRIPT_DIRECTORY/test_uniswap.sh
source $SCRIPT_DIRECTORY/test_sushiswap.sh
source $SCRIPT_DIRECTORY/test_curve.sh
source $SCRIPT_DIRECTORY/test_finance.sh
