# 새 PC에서 논문작성 템플릿을 초기화하는 스크립트: 스킬 정션 재생성, hwpx MCP 가상환경 생성, .mcp.json 경로 갱신, 전역 CLAUDE.md 설치
# 사용법: 이 폴더에서  powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

Write-Host "== 논문작성 템플릿 초기 설정 시작 =="
Write-Host "프로젝트 루트: $root"
Write-Host ""

# ---------- 1. 스킬 정션 재생성 (.claude\skills) ----------
$skillsDir = Join-Path $root '.claude\skills'
if (-not (Test-Path $skillsDir)) { New-Item -ItemType Directory -Path $skillsDir | Out-Null }

$targets = @()
# Academic Research Skills 4개 (저장소 루트 바로 아래)
foreach ($name in @('academic-paper', 'academic-paper-reviewer', 'academic-pipeline', 'deep-research')) {
    $targets += [pscustomobject]@{ Name = $name; Target = (Join-Path $root "academic-research-skills\$name") }
}
# claude-research 스킬 전부 (shared 폴더는 스킬이 아니므로 제외)
Get-ChildItem (Join-Path $root 'claude-research\skills') -Directory | Where-Object { $_.Name -ne 'shared' } | ForEach-Object {
    $targets += [pscustomobject]@{ Name = $_.Name; Target = $_.FullName }
}

$made = 0; $skipped = 0
foreach ($t in $targets) {
    $link = Join-Path $skillsDir $t.Name
    if (-not (Test-Path $t.Target)) { Write-Warning "정션 대상 없음, 건너뜀: $($t.Target)"; continue }
    if (Test-Path $link) { $skipped++; continue }
    New-Item -ItemType Junction -Path $link -Target $t.Target | Out-Null
    $made++
}
Write-Host "[1/4] 스킬 정션: 생성 ${made}개, 이미 있음 ${skipped}개 (총 대상 $($targets.Count)개)"

# ---------- 2. hwpx MCP 서버용 파이썬 가상환경 ----------
$hwpxDir = Join-Path $root 'hwpx-mcp-simple'
$venvPy = Join-Path $hwpxDir '.venv\Scripts\python.exe'
$serverExe = Join-Path $hwpxDir '.venv\Scripts\hwpx-mcp-server.exe'

$python = $null
foreach ($cand in @('py', 'python')) {
    if (Get-Command $cand -ErrorAction SilentlyContinue) { $python = $cand; break }
}

if (-not $python) {
    Write-Warning "Python을 찾지 못했습니다. https://www.python.org/downloads/ 에서 Python 3.10 이상을 설치하고('Add python.exe to PATH' 반드시 체크) 이 스크립트를 다시 실행하세요."
    Write-Warning "hwpx MCP 설정(2, 3단계)은 건너뜁니다. 스킬 정션(1단계)은 정상 완료됐습니다."
} else {
    if (-not (Test-Path $venvPy)) {
        Write-Host "[2/4] 가상환경 생성 중 ($python 사용)..."
        if ($python -eq 'py') { & py -3 -m venv (Join-Path $hwpxDir '.venv') }
        else { & python -m venv (Join-Path $hwpxDir '.venv') }
    }
    Write-Host "[2/4] hwpx MCP 서버 설치 중 (pip, 1~2분 걸릴 수 있음)..."
    & $venvPy -m pip install --quiet --upgrade pip
    & $venvPy -m pip install --quiet $hwpxDir
    if (Test-Path $serverExe) {
        Write-Host "[2/4] hwpx MCP 서버 설치 완료"
    } else {
        Write-Warning "hwpx-mcp-server.exe가 생성되지 않았습니다. 위 pip 출력을 확인하세요."
    }

    # ---------- 3. .mcp.json 경로를 이 PC 기준으로 갱신 ----------
    $mcp = @{
        mcpServers = @{
            hwpx = @{
                command = $serverExe
                args    = @()
                env     = @{ HWPX_MCP_AUTOBACKUP = '1' }
            }
        }
    }
    $json = $mcp | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText((Join-Path $root '.mcp.json'), $json, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "[3/4] .mcp.json 경로 갱신 완료"
}

# ---------- 4. 전역 CLAUDE.md 설치 (사용자 홈의 .claude 폴더, 이미 있으면 건너뜀) ----------
$globalDir = Join-Path $env:USERPROFILE '.claude'
$globalMd = Join-Path $globalDir 'CLAUDE.md'
$srcMd = Join-Path $root '전역-CLAUDE.md'
if (-not (Test-Path $srcMd)) {
    Write-Warning "전역-CLAUDE.md 원본이 템플릿에 없어 4단계를 건너뜁니다."
} elseif (Test-Path $globalMd) {
    Write-Host "[4/4] 전역 CLAUDE.md가 이미 있어 덮어쓰지 않습니다: $globalMd"
    Write-Host "      템플릿의 전역-CLAUDE.md와 비교해 필요한 내용만 직접 반영하세요."
} else {
    if (-not (Test-Path $globalDir)) { New-Item -ItemType Directory -Path $globalDir | Out-Null }
    Copy-Item $srcMd $globalMd
    Write-Host "[4/4] 전역 CLAUDE.md 설치 완료: $globalMd"
}

Write-Host ""
Write-Host "== 초기 설정 완료 =="
Write-Host "다음 단계: Claude Code를 완전히 종료했다가 이 폴더에서 다시 실행하세요."
Write-Host "재시작하면 hwpx MCP 서버 사용 승인을 묻는데, 승인(approve)을 선택하면 됩니다."
