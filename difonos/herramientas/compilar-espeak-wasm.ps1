$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$sdk = Join-Path $root 'emsdk'
$source = Join-Path $root 'vendor/espeak-ng'
$cmake = Join-Path $sdk 'cmake/4.2.0-rc3_64bit/bin/cmake.exe'
$emscripten = Join-Path $sdk 'upstream/emscripten'
$toolchain = Join-Path $emscripten 'cmake/Modules/Platform/Emscripten.cmake'

foreach ($path in @($sdk, $source, $cmake, $toolchain)) {
  if (-not (Test-Path $path)) { throw "Falta $path. Consulta vendor/espeak-ng-wasm/README.md." }
}

$build = Join-Path $root 'build/espeak-wasm'
$temp = Join-Path $root 'build/emscripten-tmp'
New-Item -ItemType Directory -Force -Path $temp | Out-Null
$env:EM_CONFIG = Join-Path $sdk '.emscripten'
$env:TEMP = $temp
$env:TMP = $temp
$env:TMPDIR = $temp
$env:PATH = "$emscripten;$(Split-Path -Parent $cmake);$env:PATH"

& $cmake -S (Join-Path $root 'wasm') -B $build -DCMAKE_BUILD_TYPE=Release "-DCMAKE_TOOLCHAIN_FILE=$toolchain"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo configurar la compilación WASM.' }
& $cmake --build $build --parallel
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el módulo eSpeak.' }
Write-Output (Join-Path $root 'runtime/espeak-wasm')
