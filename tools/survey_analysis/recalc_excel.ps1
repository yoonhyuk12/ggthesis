# Excel COM으로 통합문서의 모든 수식을 다시 계산(CalculateFullRebuild)한 뒤 같은 경로에 저장한다.
# 사용: powershell -NoProfile -ExecutionPolicy Bypass -File tools/survey_analysis/recalc_excel.ps1 -Path <xlsx>
param([Parameter(Mandatory = $true)][string]$Path)

$ErrorActionPreference = 'Stop'
$full = (Resolve-Path -LiteralPath $Path).Path
$excel = $null
$wb = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $wb = $excel.Workbooks.Open($full)
    $excel.CalculateFullRebuild()
    $wb.Save()
    $wb.Close($false)
    Write-Output "recalc ok (Excel $($excel.Version)): $full"
}
finally {
    if ($wb) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wb) }
    if ($excel) {
        $excel.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
