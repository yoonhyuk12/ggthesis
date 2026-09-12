param([string]$InputName='candidate.hwpx',[string]$OutputName='reflowed.hwpx',[string]$PdfName='reflowed.pdf')
$ErrorActionPreference='Stop'
$figureHwp=New-Object -ComObject HWPFrame.HwpObject
try {
 $figureHwp.XHwpWindows.Item(0).Visible=$true
 $registered=$figureHwp.RegisterModule('FilePathCheckDLL','FilePathCheckerModule')
 Write-Output "Registered=$registered"
 if (-not $figureHwp.Open((Join-Path $PSScriptRoot $InputName),'HWPX','forceopen:true')) {throw 'Open=False'}
 Write-Output 'Open=True'
 if (-not $figureHwp.SaveAs((Join-Path $PSScriptRoot $OutputName),'HWPX','')) {throw 'SaveAs=False'}
 $figureHwp.Clear(1)
 if (-not $figureHwp.Open((Join-Path $PSScriptRoot $OutputName),'HWPX','forceopen:true')) {throw 'Reopen=False'}
 Write-Output 'Reopen=True'
 if (-not $figureHwp.SaveAs((Join-Path $PSScriptRoot $PdfName),'PDF','')) {throw 'PDF=False'}
 Write-Output 'PDF=True'
} finally { $figureHwp.Clear(1); $figureHwp.Quit() }
