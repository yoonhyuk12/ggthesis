# 수정한 hwpx를 한글 COM으로 실제 개방해 판정하는 검증 게이트.
#
# 판정 기준은 .claude/rules/hwpx-output-verification.md 1번 항목이다.
#   RegisterModule('FilePathCheckDLL','FilePathCheckerModule') 후
#   Open(path,'HWPX','forceopen:true') 가 True 여야 완료다.
# ZIP·XML 검증을 전부 통과하고도 Open=False 인 파일이 실제로 나왔다(2026-09-11,
# 문단 텍스트를 줄인 뒤 <hp:linesegarray> 의 textpos 가 본문 길이를 넘긴 경우).
#
# 종료 코드
#   0  Open=True      (정상 개방. -PdfPath 를 줬으면 PDF 저장까지 성공)
#   1  ERROR          (파일 없음 / COM 생성 실패 / PDF 저장 실패 등)
#   2  Open=False     (한글이 열지 못함 — 산출물 불량)
#   3  Open=TIMEOUT   (-TimeoutSec 내에 COM 구간이 끝나지 않음)
#
# 이 스크립트는 입력 hwpx 에 아무것도 쓰지 않는다(Open 만, SaveAs 는 PdfPath 로만).
# 실행 전후 SHA256 을 찍어 불변을 증명한다.
# 또한 이 스크립트가 띄우지 않은 한글 프로세스는 절대 종료하지 않는다.
param(
    [Parameter(Mandatory = $true)][string]$HwpxPath,
    [string]$PdfPath,                       # 지정하면 Open=True 일 때만 COM으로 PDF 저장
    [int]$TimeoutSec = 300,                 # COM 구간 전체 제한 시간. 학위논문 본문(2.5MB·157쪽)은
                                            # 한가할 때 13초지만 다른 작업과 CPU를 나눠 쓰면 130초까지
                                            # 걸린다(실측). 짧게 잡으면 멀쩡한 파일이 TIMEOUT으로 오탐된다.
    [int]$WarmupTimeoutSec = 30,            # 워밍업에서 한글이 뜨기를 기다리는 최대 시간
    [switch]$SkipWarmup,
    [string]$HwpExe                         # 미지정이면 설치된 한글을 자동 탐지
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- 입력 점검
if (-not (Test-Path -LiteralPath $HwpxPath)) {
    Write-Output "RESULT: ERROR (대상 hwpx 없음: $HwpxPath)"
    exit 1
}
$HwpxPath = (Resolve-Path -LiteralPath $HwpxPath).Path

if ($PdfPath) {
    # 상대경로를 COM 에 넘기면 한글의 작업 디렉토리 기준으로 해석되므로 절대경로로 고정한다
    if (-not [System.IO.Path]::IsPathRooted($PdfPath)) {
        $PdfPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PdfPath))
    }
    $pdfDir = [System.IO.Path]::GetDirectoryName($PdfPath)
    if ($pdfDir -and -not (Test-Path -LiteralPath $pdfDir)) {
        Write-Output "RESULT: ERROR (PDF 출력 디렉토리 없음: $pdfDir)"
        exit 1
    }
}

if (-not $HwpExe) {
    $HwpExe = Get-ChildItem -Path "C:\Program Files (x86)\Hnc", "C:\Program Files\Hnc" `
        -Filter "Hwp.exe" -Recurse -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $SkipWarmup -and (-not $HwpExe -or -not (Test-Path -LiteralPath $HwpExe))) {
    Write-Output "WARN: 한글 실행파일을 찾지 못해 워밍업을 건너뜁니다 (-HwpExe 로 지정 가능)"
    $SkipWarmup = $true
}

Write-Output "대상: $HwpxPath"
if ($HwpExe) { Write-Output "한글: $HwpExe" }

$sha0 = (Get-FileHash -LiteralPath $HwpxPath -Algorithm SHA256).Hash
Write-Output "SHA256(before): $sha0"

# ------------------------------------------------- 기존 한글 프로세스 보호
# 여기 담긴 PID 는 사용자의 것이다. 무슨 일이 있어도 건드리지 않는다.
$preExistingPids = @(Get-Process -Name Hwp -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
if ($preExistingPids.Count -gt 0) {
    Write-Output "기존 한글 PID (보호 대상, 종료하지 않음): $($preExistingPids -join ', ')"
} else {
    Write-Output "기존 한글 PID: 없음"
}

function Get-NewHwpPid {
    @(Get-Process -Name Hwp -ErrorAction SilentlyContinue |
        Where-Object { $preExistingPids -notcontains $_.Id } |
        Select-Object -ExpandProperty Id)
}

function Stop-NewHwp {
    param([string]$Context)
    $targets = Get-NewHwpPid
    if ($targets.Count -eq 0) { return }
    Write-Output "정리($Context): 이 스크립트가 띄운 한글 PID $($targets -join ', ') 종료"
    # 강제 종료만 하면 한글이 "비정상 종료"로 기록해 다음 실행에서 문서 복구 대화상자를
    # 띄우고, 그 대화상자가 다음 COM Open 을 통째로 멈춘다(실측: 5.1에서 120초 타임아웃 1회).
    # 그래서 먼저 창을 정상적으로 닫아 보고, 남는 것만 강제 종료한다.
    foreach ($procId in $targets) {
        if ($preExistingPids -contains $procId) { continue }   # 이중 방어
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) { try { [void]$proc.CloseMainWindow() } catch { } }
    }
    for ($k = 0; $k -lt 5; $k++) {
        Start-Sleep -Seconds 1
        if ((Get-NewHwpPid).Count -eq 0) { return }
    }
    foreach ($procId in (Get-NewHwpPid)) {
        if ($preExistingPids -contains $procId) { continue }   # 이중 방어
        Write-Output "  PID $procId 정상 종료 실패 — 강제 종료"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

# --------------------------------------------------------------- 1) 워밍업
# 세션 첫 실행은 기동이 느려 멀쩡한 파일도 실패로 오탐된다(MEMORY.md [LEARN:hwpx]).
# 고정 대기가 아니라 폴링이라는 점이 핵심이다.
if ($SkipWarmup) {
    Write-Output "[1/2] 워밍업 생략"
} elseif ($preExistingPids.Count -gt 0) {
    Write-Output "[1/2] 워밍업 생략 (한글이 이미 떠 있어 콜드스타트가 아님)"
} else {
    Write-Output "[1/2] 워밍업"
    Start-Process -FilePath $HwpExe | Out-Null
    $warmed = $false
    for ($i = 0; $i -lt $WarmupTimeoutSec; $i++) {
        Start-Sleep -Seconds 1
        if ((Get-NewHwpPid).Count -gt 0) { $warmed = $true; break }
    }
    if ($warmed) { Write-Output "  기동 확인 ($($i + 1)초)" }
    else { Write-Output "  WARN: ${WarmupTimeoutSec}초 내 기동 미확인 — 그대로 진행" }
    Stop-NewHwp -Context "워밍업"
}

# ------------------------------------------------------- 2) COM 개방 판정
Write-Output "[2/2] COM 개방 판정 (제한 ${TimeoutSec}초)"

$comBlock = {
    param($Path, $Pdf)

    $r = [pscustomobject]@{
        Registered    = $null
        RegisterError = $null
        Open          = $null
        Error         = $null
        PdfSaved      = $null
        PdfError      = $null
    }
    $hwp = $null
    try {
        $hwp = New-Object -ComObject HWPFrame.HwpObject
        try { $hwp.XHwpWindows.Item(0).Visible = $false } catch { }

        # 보안 승인 모듈. 등록에 실패하면 한글이 파일 접근 대화상자를 띄워
        # Open 이 응답 없이 멈출 수 있으므로, 실패 사실을 보고에 남긴다.
        try {
            $r.Registered = [bool]$hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        } catch {
            $r.Registered = $false
            $r.RegisterError = $_.Exception.Message
        }

        # Open 이 COM 예외를 던지는 것도 "한글이 못 열었다"와 같은 뜻이므로 False 로 접는다.
        try {
            $r.Open = [bool]$hwp.Open($Path, "HWPX", "forceopen:true")
        } catch {
            $r.Open = $false
            $r.Error = "Open threw: $($_.Exception.Message)"
        }

        if ($r.Open -and $Pdf) {
            try {
                $hwp.SaveAs($Pdf, "PDF", "") | Out-Null
                $r.PdfSaved = $true
            } catch {
                $r.PdfSaved = $false
                $r.PdfError = $_.Exception.Message
            }
        }
    } catch {
        $r.Error = $_.Exception.Message
    } finally {
        if ($null -ne $hwp) {
            try { $hwp.Clear(1) } catch { }
            try { $hwp.Quit() } catch { }
            try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($hwp) } catch { }
        }
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
    }
    $r
}

$job = Start-Job -ScriptBlock $comBlock -ArgumentList $HwpxPath, $PdfPath
$finished = Wait-Job -Job $job -Timeout $TimeoutSec

if (-not $finished) {
    # 순서가 중요하다. COM 호출에 붙들린 잡에 Stop-Job 을 먼저 걸면 그 호출이 풀릴 때까지
    # 블록되어 2분 넘게 더 매달린다(실측). 한글을 먼저 정리해 COM 호출을 실패시킨다.
    Stop-NewHwp -Context "타임아웃"
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    $sha1 = (Get-FileHash -LiteralPath $HwpxPath -Algorithm SHA256).Hash
    Write-Output "SHA256(after):  $sha1"
    Write-Output "SHA256 UNCHANGED: $($sha0 -eq $sha1)"
    Write-Output "Open=TIMEOUT"
    Write-Output "RESULT: TIMEOUT (${TimeoutSec}초 내 COM 구간 미완료 — 한글 대화상자(문서 복구·보안 경고)가 떠 있을 수 있습니다)"
    exit 3
}

$res = Receive-Job -Job $job -ErrorAction SilentlyContinue
Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
Stop-NewHwp -Context "COM 종료 후"

$sha1 = (Get-FileHash -LiteralPath $HwpxPath -Algorithm SHA256).Hash
Write-Output "SHA256(after):  $sha1"
Write-Output "SHA256 UNCHANGED: $($sha0 -eq $sha1)"

if ($null -eq $res) {
    Write-Output "RESULT: ERROR (COM 잡이 결과를 돌려주지 않음)"
    exit 1
}

if ($null -eq $res.Registered) {
    Write-Output "RegisterModule=UNKNOWN"
} else {
    Write-Output "RegisterModule=$($res.Registered)"
}
if ($res.Registered -eq $false) {
    Write-Output "  WARN: FilePathCheckDLL 등록 실패 — 한글 보안 대화상자가 떴을 수 있습니다. $($res.RegisterError)"
}

if ($null -eq $res.Open) {
    Write-Output "Open=ERROR"
    Write-Output "RESULT: ERROR ($($res.Error))"
    exit 1
}

Write-Output "Open=$($res.Open)"
if (-not $res.Open) {
    if ($res.Error) { Write-Output "  detail: $($res.Error)" }
    Write-Output "RESULT: OPEN FAILED (한글이 파일을 열지 못했습니다 — linesegarray textpos 초과 등을 점검하세요)"
    exit 2
}

if ($PdfPath) {
    if ($res.PdfSaved -and (Test-Path -LiteralPath $PdfPath)) {
        Write-Output "PDF OK: $PdfPath ($((Get-Item -LiteralPath $PdfPath).Length) bytes)"
    } else {
        Write-Output "PDF FAILED: $($res.PdfError)"
        Write-Output "RESULT: ERROR (PDF 저장 실패)"
        exit 1
    }
}

Write-Output "RESULT: OK"
exit 0
