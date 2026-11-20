# Publish a Clubhouse update: bump the version, build, zip, checksum, commit, tag, push and create the GitHub release.
# Clubhouse.exe (1.8.0+) checks the latest release on launch and offers it in-app.
#
#   powershell -ExecutionPolicy Bypass -File packaging\release.ps1 -Version 1.8.1
#
# Needs: CHANGELOG.md with a "## <version>" section (it becomes the release notes), git + gh logged in.
param([Parameter(Mandatory = $true)][string]$Version, [switch]$NoPublish)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:Path += ';C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "Version must look like 1.8.1" }
$utf8 = New-Object Text.UTF8Encoding $false
function Set-Text($path, $text) { [IO.File]::WriteAllText((Resolve-Path $path).Path, $text, $utf8) }

# 1. Release notes from CHANGELOG.md
$log = [IO.File]::ReadAllText("$root\CHANGELOG.md")
$m = [regex]::Match($log, "(?ms)^## $([regex]::Escape($Version))\b[^\n]*\n(.*?)(?=^## |\z)")
if (-not $m.Success) { throw "CHANGELOG.md has no '## $Version' section" }
$notes = $m.Groups[1].Value.Trim()

# 2. Version numbers
$v = $Version.Split('.')
Set-Text 'app\version.py' ([regex]::Replace([IO.File]::ReadAllText("$root\app\version.py"), 'VERSION = "[^"]*"', "VERSION = `"$Version`""))
$vi = [IO.File]::ReadAllText("$root\packaging\version_info.txt")
$vi = [regex]::Replace($vi, '\(\d+, \d+, \d+, \d+\)', "($($v[0]), $($v[1]), $($v[2]), 0)")
$vi = [regex]::Replace($vi, "(Version', ')[\d.]+", "`${1}$Version")
Set-Text 'packaging\version_info.txt' $vi
Set-Text 'packaging\README.txt' ([regex]::Replace([IO.File]::ReadAllText("$root\packaging\README.txt"), '^CLUBHOUSE [\d.]+', "CLUBHOUSE $Version"))

# 3. Build (into build\out: a running Clubhouse can lock dist\Clubhouse)
& .venv\Scripts\python.exe packaging\make_icon.py
& .venv\Scripts\python.exe -m PyInstaller packaging\clubhouse.spec --noconfirm --distpath build\out --workpath build\work
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
Copy-Item packaging\README.txt build\out\Clubhouse\README.txt -Force
Copy-Item CHANGELOG.md build\out\Clubhouse\CHANGELOG.md -Force
New-Item -ItemType Directory -Force dist | Out-Null
$zip = "dist\Clubhouse-$Version.zip"
Compress-Archive -Path build\out\Clubhouse -DestinationPath $zip -Force
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
Set-Content -Path "$zip.sha256" -Value "$hash  Clubhouse-$Version.zip" -Encoding ascii -NoNewline
Write-Host "Built $zip ($([math]::Round((Get-Item $zip).Length/1MB,1)) MB) sha256 $hash"
if ($NoPublish) { return }

# 4. Commit, tag, push, release
git add -A
git commit -m "Clubhouse $Version" | Out-Null
git tag -a "v$Version" -m "Clubhouse $Version"
git push origin HEAD --follow-tags
$nf = Join-Path $env:TEMP "clubhouse-notes-$Version.md"
Set-Content -Path $nf -Value $notes -Encoding utf8
gh release create "v$Version" $zip "$zip.sha256" --title "Clubhouse $Version" --notes-file $nf
Write-Host "Published Clubhouse $Version"
