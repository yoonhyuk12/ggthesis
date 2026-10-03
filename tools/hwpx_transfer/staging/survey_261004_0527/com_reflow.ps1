param([Parameter(Mandatory=$true)][string]$InputFile,[Parameter(Mandatory=$true)][string]$OutputFile,[Parameter(Mandatory=$true)][string]$PdfFile,[int]$TimeoutSec=300)
$ErrorActionPreference='Stop'
$src=(Resolve-Path -LiteralPath $InputFile).Path
$dst=[IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutputFile))
$pdf=[IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PdfFile))
if ((Test-Path -LiteralPath $dst) -or (Test-Path -LiteralPath $pdf)) { throw 'Choose new output paths.' }
$sha0=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
$job=Start-Job -ArgumentList $src,$dst,$pdf -ScriptBlock {
    param($Source,$Destination,$Pdf)
    $ErrorActionPreference='Stop'
    $hwp=$null
    $r=[ordered]@{registered=$false;opened=$false;saved=$false;reopened=$false;pdf_saved=$false;pages=$null;error=$null}
    try {
        $hwp=New-Object -ComObject HWPFrame.HwpObject
        $hwp.XHwpWindows.Item(0).Visible=$false
        $r.registered=[bool]$hwp.RegisterModule('FilePathCheckDLL','FilePathCheckerModule')
        if (-not $r.registered) { throw 'File access module unavailable.' }
        $r.opened=[bool]$hwp.Open($Source,'HWPX','forceopen:true')
        if (-not $r.opened) { throw 'Hangeul Open=False.' }
        $r.saved=[bool]$hwp.SaveAs($Destination,'HWPX','')
        if (-not $r.saved) { throw 'HWPX SaveAs failed.' }
        $hwp.Clear(1)
        $r.reopened=[bool]$hwp.Open($Destination,'HWPX','forceopen:true')
        if (-not $r.reopened) { throw 'Saved HWPX could not be reopened.' }
        $r.pages=[int]$hwp.PageCount
        $r.pdf_saved=[bool]$hwp.SaveAs($Pdf,'PDF','')
        if (-not $r.pdf_saved) { throw 'PDF SaveAs failed.' }
    } catch { $r.error=$_.Exception.Message }
    finally {
        if ($null -ne $hwp) {
            try { $hwp.Clear(1) } catch {}
            try { $hwp.Quit() } catch {}
            try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($hwp) } catch {}
        }
    }
    [pscustomobject]$r
}
$finished=Wait-Job -Job $job -Timeout $TimeoutSec
if (-not $finished) { Write-Output 'COM_TIMEOUT: inspect owned COM job; no external Hwp process was terminated.'; exit 3 }
$result=Receive-Job -Job $job
Remove-Job -Job $job
$unchanged=$sha0 -eq (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
$result | Select-Object registered,opened,saved,reopened,pdf_saved,pages,error | ConvertTo-Json
Write-Output "INPUT_SHA256_UNCHANGED=$unchanged"
if (-not $unchanged -or $result.error -or -not $result.pdf_saved -or -not (Test-Path -LiteralPath $pdf)) { exit 1 }
