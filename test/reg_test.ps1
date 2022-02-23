# Example
# .\test\test-reg.ps1
# .\test\test-reg.ps1 -sel prod
# .\test\test-reg.ps1 -models uniswap-router-price-usd
# python.exe test\cli.py run --input '{\"radius\":3}' var
# python.exe test\cli.py run -i "{}" uniswap-router-price-usd

Param([string]$sel = 'test', [string[]]$models = @())

if ($sel -eq 'test') {
	$credmark_dev1 = (Get-Command python).Path
	$credmark_dev2 = ".\test\cli.py"
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
	$output = & $credmark_dev1 $credmark_dev2 $par1 $par2 "-b 14000000" $par3
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

foreach ($m in $models) {
	if ("geometry-spheres-area" -eq $m -or "geometry-spheres-volume" -eq $m -or "geometry-circles-area" -eq $m -or "geometry-circles-circumference" -eq $m) {
		test-target test-model -expected 0 -params run, $m, "-i {""radius"":3}"
	}
 else {
		if ("historical-pi" -eq $m -or "historical-staked-xcmk" -eq $m) {
			test-target test-model -expected 1 -params run, $m, "-i {}"
		}
		else {
			test-target test-model -expected 0 -params run, $m, "-i {}"
		}
	}
}

Write-Output "All pass!"
