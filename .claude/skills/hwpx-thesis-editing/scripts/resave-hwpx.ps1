# 한글 COM으로 hwpx를 열어 재조판 저장(SaveAs HWPX)하고, 저장본을 다시 열어 PDF를 내보낸다.
# 규칙(.claude/rules/hwpx-output-verification.md): 한글이 재조판 저장한 파일이 산출물이다. PDF는 스크래치에만 둔다.
# 사용: pwsh -File resave-hwpx.ps1 -HwpxIn <조립본> -HwpxOut "00. hwpx/YYMMDD_HHMM_논문명.hwpx" [-PdfOut <스크래치 PDF>]
# 이 스크립트가 띄우지 않은 한글 프로세스(시작 전부터 있던 PID)는 절대 종료하지 않는다.
# 2026-10-08 실측: 재저장본을 다시 열 때 한글이 새 프로세스를 하나 더 띄우고 Quit 뒤에도 남아 산출물 파일을 잠근다
#   → 정리 단계에서 새 PID를 두 번(2초 간격) 확인해 끝내고, 산출물 파일이 잠겨 있지 않은지 확인한다.
param(
    [Parameter(Mandatory = $true)][string]$HwpxIn,
    [Parameter(Mandatory = $true)][string]$HwpxOut,
    [string]$PdfOut
)
$ErrorActionPreference = 'Stop'
$HwpxIn = (Resolve-Path -LiteralPath $HwpxIn).Path
if (-not [System.IO.Path]::IsPathRooted($HwpxOut)) { $HwpxOut = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $HwpxOut)) }
if ($PdfOut -and -not [System.IO.Path]::IsPathRooted($PdfOut)) { $PdfOut = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PdfOut)) }
$pre = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
Write-Output "입력: $HwpxIn"
Write-Output "SHA256(in): $((Get-FileHash -LiteralPath $HwpxIn -Algorithm SHA256).Hash)"
if ($pre.Count -gt 0) { Write-Output "기존 한글 PID (보호): $($pre -join ', ')" }

function Stop-ScriptHwp {
    for ($round = 0; $round -lt 3; $round++) {
        $new = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue | Where-Object { $pre -notcontains $_.Id })
        if ($new.Count -eq 0) { return }
        foreach ($p in $new) { try { [void]$p.CloseMainWindow() } catch { } }
        Start-Sleep -Seconds 2
        foreach ($p in @(Get-Process -Name Hwp -ErrorAction SilentlyContinue | Where-Object { $pre -notcontains $_.Id })) {
            Write-Output "정리: 이 스크립트가 띄운 한글 PID $($p.Id) 종료"
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
}

$hwp = $null
$ok = $false
try {
    $hwp = New-Object -ComObject HWPFrame.HwpObject
    try { $hwp.XHwpWindows.Item(0).Visible = $false } catch { }
    $reg = [bool]$hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    Write-Output "RegisterModule=$reg"
    $opened = [bool]$hwp.Open($HwpxIn, "HWPX", "forceopen:true")
    Write-Output "Open=$opened"
    if (-not $opened) { throw "한글이 입력 파일을 열지 못했다" }
    $saved = [bool]$hwp.SaveAs($HwpxOut, "HWPX", "lock:false;backup:false;fullsave:true;")
    Write-Output "SaveAs(HWPX)=$saved -> $HwpxOut"
    if (-not $saved) { throw "재조판 저장 실패" }
    [void]$hwp.Clear(1)
    $opened2 = [bool]$hwp.Open($HwpxOut, "HWPX", "forceopen:true")
    Write-Output "Reopen(saved)=$opened2"
    if (-not $opened2) { throw "재조판 저장본을 다시 열지 못했다" }
    if ($PdfOut) {
        $pdf = [bool]$hwp.SaveAs($PdfOut, "PDF", "")
        Write-Output "SaveAs(PDF)=$pdf -> $PdfOut"
    }
    $ok = $true
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
} finally {
    if ($null -ne $hwp) {
        try { [void]$hwp.Clear(1) } catch { }
        try { $hwp.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($hwp) } catch { }
    }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    Stop-ScriptHwp
}
if (Test-Path -LiteralPath $HwpxOut) {
    Write-Output "SHA256(out): $((Get-FileHash -LiteralPath $HwpxOut -Algorithm SHA256).Hash)  size=$((Get-Item -LiteralPath $HwpxOut).Length)"
    try { $fs = [System.IO.File]::Open($HwpxOut, 'Open', 'ReadWrite', 'None'); $fs.Close(); Write-Output "산출물 잠금 없음" }
    catch { Write-Output "WARN: 산출물이 아직 잠겨 있다 — 남은 한글 프로세스를 확인하라" }
}
if ($PdfOut -and (Test-Path -LiteralPath $PdfOut)) { Write-Output "PDF size=$((Get-Item -LiteralPath $PdfOut).Length)" }
if ($ok) { Write-Output "RESULT: OK"; exit 0 } else { Write-Output "RESULT: FAIL"; exit 1 }
