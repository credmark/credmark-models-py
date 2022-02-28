# Example
# .\test\test-reg.ps1
# .\test\test-reg.ps1 -sel prod
# .\test\test-reg.ps1 -models uniswap-router-price-usd
# python.exe test\cli.py run --input '{\"radius\":3}' var
# python.exe test\cli.py run -i "{}" uniswap-router-price-usd

Param([string]$sel = 'test', [string]$testfrom = "", [string[]]$models = @())

if ($sel -eq 'test') {
	$credmark_dev1 = (Get-Command python).Path
	$credmark_dev2 = ".\test\test.py"
}
else {
	if ($sel -eq 'prod') {
		$credmark_dev1 = "credmark-dev"
		$credmark_dev2 = ""
	}
 else {
		write-error "sel = test or prod to pick the runtime"
		exit
	}
}

write-host "Using [$sel] $credmark_dev1 $credmark_dev2"

Function test-target {
	Param([string]$target, [int]$expected, [String[]]$params = @())

	if ([string]::IsNullOrEmpty($params)) {
		Write-Output "[test-this] Test $target with __no_param__ for $expected"
	}
 else {
		Write-Output "[test-this] Test $target with $params for $expected"
	}

	if ($params.Length -eq 0) {
		$output, $rs, $exit_code = (. $target )
	}
 else {
		if ($params.Length -eq 1) {
			$output, $rs, $exit_code = (. $target $params[0])
		}
		else {
			if ($params.Length -eq 2) {
				$output, $rs, $exit_code = (. $target $params[0] $params[1])
			}
			else {
				if ($params.Length -eq 3) {
					$output, $rs, $exit_code = (. $target $params[0] $params[1] $params[2])
				}
				else {
					write-error "[test-this] Stopped with $target. >2 params ${params}"
					exit
				}
			}
		}
	}

	$result_array = "[test-this] result:", "target=$target", "rs=$rs", "exit_code=$exit_code", "output=$([String]::Join(""`n"",$output))", "expected=$expected"
	$result_joined = [String]::Join("`n", $result_array)
	write-host $result_joined

	if ( $exit_code -ne $expected ) {
		write-error "[test-this] Stopped with $target."
		exit
	}
 else {
		if ( -not $rs ) {
			write-host "[test-this] Good with $target, expected to fail."
		}
		else {
			write-host "[test-this] Good with $target, expected to pass"
		}
	}
}

Function show-models {
	$output = & $credmark_dev1 $credmark_dev2 list-models
	$rs = $?
	if ([string]::IsNullOrEmpty($output)) {
		$output = '__null__'
	}
	# write-host 'show-models:', $output, $rs, $LastExitCode
	return $output, $rs, $LastExitCode
}

Function show-models2 {
	$output = & $credmark_dev1 $credmark_dev2 list-models2
	$rs = $?
	if ([string]::IsNullOrEmpty($output)) {
		$output = '__null__'
	}
	# write-host 'show-models2:', $output, $rs, $LastExitCode
	return $output, $rs, $LastExitCode
}

test-target "show-models"

# test-target "show-models2"

Function test-model {
	Param($par1, $par2, $par3)
	# write-host "[test-model] $credmark_dev1 $credmark_dev2 $par1 $par2 $par3`n"
	$output = & $credmark_dev1 $credmark_dev2 $par1 $par2 "-b 14234904" "--api_url" "http://localhost:8700/v1/models/run" $par3
	$rs = $?
	if ([string]::IsNullOrEmpty($output)) {
		$output = '__null__'
	}
	return $output, $rs, $LastExitCode
}
# test: test-model -model_param "var"

# $models = "var","cmk-circulating-supply","xcmk-total-supply","xcmk-cmk-staked","xcmk-deployment-time","Foo","uniswap-router-price-usd","uniswap-router-price-pair","uniswap-tokens","uniswap-exchange","geometry-circles-area","geometry-circles-circumference","geometry-spheres-area","geometry-spheres-volume","historical-pi","historical-staked-xcmk","pi","run-test"

(& $credmark_dev1 $credmark_dev2 clean)

if ([string]::IsNullOrEmpty($models)) {
	$models = (& $credmark_dev1 $credmark_dev2 list-models | grep '^ - ' | awk '{x = $2; print substr(x, 0, length(x) - 1)}')
	write-host "models=$models"
}

write-host testfrom=$testfrom

foreach ($m in $models) {
	if ($testfrom -ne "") {
		if ($testfrom -ne $m) {
			continue
		}
		else {
			$testfrom = ""
		}
	}
	if ("geometry-spheres-area" -eq $m -or "geometry-spheres-volume" -eq $m -or "geometry-circles-area" -eq $m -or "geometry-circles-circumference" -eq $m) {
		test-target test-model -expected 0 -params run, $m, "-i {""radius"":3}"
	}
	else {
		if ("curve-fi-pool-info" -eq $m) {
			test-target test-model -expected 0 -params run, $m, "-i {""address"":""0x06364f10B501e868329afBc005b3492902d6C763""}"
		}
		else {
			if ("example-contract-name" -eq $m) {
				test-target test-model -expected 0 -params run, $m, "-i {""contractName"":""AToken""}"
			}
			else {
				if ("example-address" -eq $m) {
					test-target test-model -expected 0 -params run, $m, "-i {""address"":""0xd905e2eaebe188fc92179b6350807d8bd91db0D8""}"
				}
				else {
					if ("example-address-transforms" -eq $m) {
						test-target test-model -expected 0 -params run, $m, "-i {""address"":""0xd905e2eaebe188fc92179b6350807d8bd91db0D8""}"
					}
					else {
						if ("example-load-contract-by-name" -eq $m) {
							test-target test-model -expected 0 -params run, $m, "-i {""contractName"":""mutantmfers""}"
						}
						else {
							if ("example-load-contract-by-address" -eq $m) {
								test-target test-model -expected 0 -params run, $m, "-i {""address"":""0xa8f8dd56e2352e726b51738889ef6ee938cca7b6""}"
							}
							else {
								if ("example-30-day-series" -eq $m) {
									test-target test-model -expected 1 -params run, $m, "-i {""slug"":""example-echo"", ""input"":{""message"":""hello world""}}"
								}
								else {
									if ("historical-pi" -eq $m -or
										"historical-staked-xcmk" -eq $m -or
										"run-test-2" -eq $m -or
										"state-of-credmark" -eq $m -or
										"xcmk-deployment-time" -eq $m -or
										"xcmk-deployment-time" -eq $m -or
										"type-test-2" -eq $m) {
										test-target test-model -expected 1 -params run, $m, "-i {}"
									}
									else {
										test-target test-model -expected 0 -params run, $m, "-i {}"
									}
								}
							}
						}
					}
				}
			}
		}
	}
}

Write-Output "All pass!"
