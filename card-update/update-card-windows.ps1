# Update the prebuilt cores on a KNULLI SD card from Windows.
# 윈도우에서 KNULLI SD 카드 안의 코어를 새 판으로 바꿔요.
#
#   Double-click update-card-windows.bat (from card-update.zip), or paste into PowerShell:
#   irm https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/card-update/update-card-windows.ps1 | iex
#
# It looks for <drive>:\system\hanbang_cores\ on every drive, reads card-updates.txt (from the folder of
# the .bat when the files are there, as in an offline package; otherwise from the latest release), and replaces only the files whose md5 is a known older build. A file it does not recognise is
# left alone. The new file is written and checked first; the old one is kept in
# <drive>:\system\hanbang_cores\backup\.
#
# Test switches (environment): HB_BASE_URL = where the release files are, HB_CARD_ROOTS = card folders
# to look at (separated by ';'), HB_YES=1 = do not ask.

function Update-HbCard {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'
    try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}
    $base = 'https://github.com/Squirbie/handheld-link-cores/releases/latest/download'
    if ($env:HB_BASE_URL) { $base = $env:HB_BASE_URL }
    $yes = ($env:HB_YES -eq '1')

    # hashes with .NET directly: Get-FileHash lives in a module that may not load (for example when started from PowerShell 7)
    function HashOf($alg, [string]$p) {
        $s = [IO.File]::OpenRead($p)
        try { ([BitConverter]::ToString($alg.ComputeHash($s))).Replace('-', '').ToLower() } finally { $s.Dispose(); $alg.Dispose() }
    }
    function Md5Of([string]$p) { HashOf ([Security.Cryptography.MD5]::Create()) $p }
    function Sha256Of([string]$p) { HashOf ([Security.Cryptography.SHA256]::Create()) $p }
    function Get-Url([string]$url, [string]$out) {
        if ($url -like 'file://*') { Copy-Item -LiteralPath ([Uri]$url).LocalPath -Destination $out -Force }
        else { Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out }
    }
    # files next to the .bat (an offline package) are used before anything is downloaded
    $localDir = $null
    if (-not $env:HB_BASE_URL -and $env:HB_PS1) {
        $d = Split-Path -Parent $env:HB_PS1
        if ((Test-Path -LiteralPath (Join-Path $d 'card-updates.txt')) -and (Test-Path -LiteralPath (Join-Path $d 'SHA256SUMS.txt'))) { $localDir = $d }
    }
    function Get-File([string]$name, [string]$out) {
        if ($localDir -and (Test-Path -LiteralPath (Join-Path $localDir $name))) { Copy-Item -LiteralPath (Join-Path $localDir $name) -Destination $out -Force }
        else { Get-Url "$base/$name" $out }
    }

    Write-Host '== 코어 업데이트 · Core update =='
    if ($localDir) { Write-Host "이 폴더의 파일을 써요 · Using the files in this folder: $localDir" }

    # ---- 1. find the cards
    if ($env:HB_CARD_ROOTS) { $roots = $env:HB_CARD_ROOTS -split ';' | Where-Object { $_ } }
    else { $roots = [IO.DriveInfo]::GetDrives() | Where-Object { $_.IsReady } | ForEach-Object { $_.RootDirectory.FullName } }
    $cards = @($roots | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'system\hanbang_cores') -PathType Container })
    if ($cards.Count -eq 0) {
        Write-Host ''
        Write-Host '!! 카드를 못 찾았어요. 게임 카드(system\hanbang_cores 폴더가 있는 카드)를 PC 에 꽂고 다시 해 주세요.'
        Write-Host '   No card found. Insert the card that has system\hanbang_cores and run this again.'
        return 1
    }

    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('hb-card-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        # ---- 2. what the latest release has
        Write-Host '새 판 목록 읽는 중 · Reading the update list...'
        try {
            Get-File 'card-updates.txt' (Join-Path $tmp 'card-updates.txt')
            Get-File 'SHA256SUMS.txt' (Join-Path $tmp 'SHA256SUMS.txt')
        } catch {
            Write-Host '!! 목록을 못 받았어요(인터넷 연결을 확인해 주세요) · could not download the update list'
            return 1
        }
        $entries = @(Get-Content -LiteralPath (Join-Path $tmp 'card-updates.txt') -Encoding UTF8 |
            Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object {
                $c = $_ -split "`t"
                if ($c.Count -ge 5) { [pscustomobject]@{ File = $c[0]; Olds = $c[1] -split ','; New = $c[2]; Zip = $c[3]; InZip = $c[4] } }
            })
        $sums = @{}
        Get-Content -LiteralPath (Join-Path $tmp 'SHA256SUMS.txt') | ForEach-Object {
            $c = $_ -split '\s+'
            if ($c.Count -ge 2) { $sums[$c[1]] = $c[0].ToLower() }
        }

        # ---- 3. compare every card file with the list
        $plan = @()
        foreach ($card in $cards) {
            Write-Host ''
            Write-Host "카드 · Card: $card"
            foreach ($e in $entries) {
                $f = Join-Path (Join-Path $card 'system\hanbang_cores') $e.File
                if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { continue }
                $cur = Md5Of $f
                if ($cur -eq $e.New) { Write-Host "  이미 새 판 · already new   $($e.File)" }
                elseif ($e.Olds -contains $cur) {
                    Write-Host "  바꿈 · will update          $($e.File) ($($cur.Substring(0, 8)) -> $($e.New.Substring(0, 8)))"
                    $plan += [pscustomobject]@{ Card = $card; File = $f; Name = $e.File; Cur = $cur; New = $e.New; Zip = $e.Zip; InZip = $e.InZip }
                }
                else { Write-Host "  모르는 판이라 그대로 · unknown build, left alone   $($e.File) ($($cur.Substring(0, 8)))" }
            }
        }
        if ($plan.Count -eq 0) {
            Write-Host ''
            Write-Host '바꿀 것이 없어요 · Nothing to update.'
            return 0
        }
        Write-Host ''
        if (-not $yes) {
            $a = Read-Host '바꿀까요? 그냥 Enter = 예 · n = 아니요 · Update now? Enter = yes, n = no'
            if ($a -match '^(n|no|아니)') { Write-Host '그만뒀어요 · Cancelled.'; return 0 }
        }

        # ---- 4. get and check the new files
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $newFiles = @{}
        foreach ($p in $plan) {
            if ($newFiles.ContainsKey($p.Name)) { continue }
            $zip = Join-Path $tmp $p.Zip
            if (-not (Test-Path -LiteralPath $zip)) {
                Write-Host "새 코어 준비 중 · Getting $($p.Zip) ..."
                Get-File $p.Zip $zip
                if (-not $sums.ContainsKey($p.Zip) -or (Sha256Of $zip) -ne $sums[$p.Zip]) { Write-Host "!! $($p.Zip) 지문이 안 맞아요 · checksum mismatch"; return 1 }
            }
            $out = Join-Path $tmp ('new_' + $p.Name)
            $z = [IO.Compression.ZipFile]::OpenRead($zip)
            try {
                $entry = $z.GetEntry($p.InZip)
                if (-not $entry) { Write-Host "!! $($p.Zip) 안에 $($p.InZip) 이 없어요 · not in the zip"; return 1 }
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $out, $true)
            } finally { $z.Dispose() }
            if ((Md5Of $out) -ne $p.New) { Write-Host "!! 새 $($p.Name) 의 지문이 목록과 달라요 · md5 does not match the list"; return 1 }
            $newFiles[$p.Name] = $out
        }

        # ---- 5. replace: write the new file next to the old one, check it, then swap
        $fail = $false
        foreach ($p in $plan) {
            $dir = Split-Path -Parent $p.File
            $hbnew = $p.File + '.hbnew'
            try {
                Copy-Item -LiteralPath $newFiles[$p.Name] -Destination $hbnew -Force
                if ((Md5Of $hbnew) -ne $p.New) { throw 'md5' }
            } catch {
                Remove-Item -LiteralPath $hbnew -Force -ErrorAction SilentlyContinue
                Write-Host "  !! 카드에 쓰지 못했어요(카드가 잠겼거나 꽉 찼나요?) · could not write $($p.Name)"; $fail = $true; continue
            }
            $bakDir = Join-Path $dir 'backup'
            New-Item -ItemType Directory -Path $bakDir -Force | Out-Null
            $bak = Join-Path $bakDir $p.Name
            if ((Test-Path -LiteralPath $bak) -and (Md5Of $bak) -ne $p.Cur) { $bak = Join-Path $bakDir ($p.Name + '.' + $p.Cur.Substring(0, 8)) }
            if (-not (Test-Path -LiteralPath $bak)) {
                try { Move-Item -LiteralPath $p.File -Destination $bak }
                catch {
                    Remove-Item -LiteralPath $hbnew -Force -ErrorAction SilentlyContinue
                    Write-Host "  !! 옛 판을 backup 으로 못 옮겨서 그대로 뒀어요 · could not back up $($p.Name), left as it was"; $fail = $true; continue
                }
            }
            try {
                Move-Item -LiteralPath $hbnew -Destination $p.File -Force
                if ((Md5Of $p.File) -ne $p.New) { throw 'md5' }
                Write-Host "  바꿨어요 · updated   $($p.Name)   (옛 판 · old: system\hanbang_cores\backup\)"
            } catch {
                if (-not (Test-Path -LiteralPath $p.File)) { Copy-Item -LiteralPath $bak -Destination $p.File }
                Write-Host '  !! 바꾸지 못해서 옛 판을 그대로 뒀어요 · failed, the old file is back'; $fail = $true
            }
        }
        Write-Host ''
        if (-not $fail) {
            Write-Host '끝났어요. 작업 표시줄에서 카드를 꺼내고(안전하게 제거) 기기에 다시 꽂으세요. 같이하기는 두 기기 카드를 모두 바꿔야 돼요.'
            Write-Host 'Done. Eject the card (Safely Remove) and put it back in the handheld. For netplay, update both devices'' cards.'
            return 0
        }
        Write-Host '!! 일부를 못 바꿨어요. 위 메시지를 봐 주세요 · Some files were not updated (see above).'
        return 1
    } finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$hbResult = Update-HbCard
if ($env:HB_EXIT_CODE -eq '1') { exit $hbResult }
