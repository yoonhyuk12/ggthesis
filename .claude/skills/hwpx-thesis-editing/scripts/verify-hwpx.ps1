# 수정한 hwpx가 한글에서 조용히 죽지 않는지 판정하고, 선택적으로 PDF까지 뽑는 검증 게이트
param(
    [Parameter(Mandatory = $true)][string]$HwpxPath,
    [string]$PdfPath,                       # 지정하면 COM으로 PDF 변환까지 수행
    [int]$AppearTimeoutSec = 60,            # 프로세스가 뜨기를 기다리는 최대 시간
    [int]$SettleSec = 8                     # 뜬 뒤 계속 살아있는지 확인하는 시간
)

$HwpExe = "C:\Program Files (x86)\Hnc\Office 2020\HOffice110\Bin\Hwp.exe"
if (-not (Test-Path $HwpExe)) { throw "한글 실행파일 없음: $HwpExe" }
if (-not (Test-Path $HwpxPath)) { throw "대상 hwpx 없음: $HwpxPath" }
$HwpxPath = (Resolve-Path $HwpxPath).Path

function Kill-Hwp {
    Get-Process Hwp -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# 1) 워밍업 — 세션 첫 실행은 기동이 느려 멀쩡한 파일도 CRASHED로 오탐된다
Write-Output "[1/3] 워밍업"
Kill-Hwp
Start-Process $HwpExe | Out-Null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Get-Process Hwp -ErrorAction SilentlyContinue) { break }
}
Kill-Hwp

# 2) 크래시 게이트 — 떴다가 조용히 사라지면 파일이 깨진 것이다
Write-Output "[2/3] 크래시 게이트: $([System.IO.Path]::GetFileName($HwpxPath))"
Start-Process $HwpExe -ArgumentList "`"$HwpxPath`"" | Out-Null
$appeared = $false
for ($i = 0; $i -lt $AppearTimeoutSec; $i++) {
    Start-Sleep -Seconds 1
    if (Get-Process Hwp -ErrorAction SilentlyContinue) { $appeared = $true; break }
}
if (-not $appeared) {
    Kill-Hwp
    Write-Output "RESULT: CRASHED (${AppearTimeoutSec}초 내 프로세스 미출현)"
    exit 1
}
Start-Sleep -Seconds $SettleSec
if (-not (Get-Process Hwp -ErrorAction SilentlyContinue)) {
    Write-Output "RESULT: CRASHED (기동 후 ${SettleSec}초 내 조용히 종료)"
    exit 1
}
Write-Output "RESULT: ALIVE"
Kill-Hwp

# 3) PDF 변환 (선택) — 육안 검증용. render-pdf.ps1로 PNG를 뽑아 확인한다
if ($PdfPath) {
    Write-Output "[3/3] PDF 변환"
    $h = New-Object -ComObject HWPFrame.HwpObject
    $h.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule") | Out-Null
    $h.Open($HwpxPath, "HWPX", "") | Out-Null
    $h.SaveAs($PdfPath, "PDF", "") | Out-Null
    $h.Quit()
    if (Test-Path $PdfPath) { Write-Output "PDF OK: $PdfPath ($((Get-Item $PdfPath).Length) bytes)" }
    else { Write-Output "PDF FAILED"; exit 1 }
}
else { Write-Output "[3/3] PDF 변환 생략 (-PdfPath 미지정)" }
