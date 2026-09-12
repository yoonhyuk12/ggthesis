$ErrorActionPreference='Stop'
$figureDir=$PSScriptRoot
$figureImage=(Resolve-Path (Join-Path $figureDir '../../analysis/extracted/BinData/image1.bmp')).Path
$figureHwp=New-Object -ComObject HWPFrame.HwpObject
try {
 $figureHwp.XHwpWindows.Item(0).Visible=$false
 $registered=$figureHwp.RegisterModule('FilePathCheckDLL','FilePathCheckerModule')
 Write-Output "Registered=$registered"
 $ctrl=$figureHwp.InsertPicture($figureImage,$true,1,$false,$false,0,150,60)
 if ($null -eq $ctrl) { throw 'InsertPicture returned null' }
 $saved=$figureHwp.SaveAs((Join-Path $figureDir 'picture_template.hwpx'),'HWPX','')
 Write-Output "Saved=$saved"
} finally { $figureHwp.Clear(1); $figureHwp.Quit() }
