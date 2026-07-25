# hwpx를 변환한 PDF의 지정 페이지를 PNG로 렌더링해 육안 검증에 쓰는 스크립트 (Windows PowerShell 5.1 전용)
param(
    [Parameter(Mandatory = $true)][string]$PdfPath,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Pages = "1-3",
    [int]$Width = 1000
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
function AwaitAction($WinRtAction) {
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
    $netTask = $asTask.Invoke($null, @($WinRtAction))
    $netTask.Wait(-1) | Out-Null
}

# "all" | "5" | "2-7" | "1,4,9-11" 을 1-기반 페이지 번호 배열로 푼다
function Resolve-Pages([string]$spec, [int]$pageCount) {
    if ($spec -eq 'all') { return 1..$pageCount }
    $result = New-Object System.Collections.Generic.List[int]
    foreach ($part in $spec -split ',') {
        $part = $part.Trim()
        if ($part -match '^(\d+)\s*-\s*(\d+)$') {
            [int]$a = $Matches[1]; [int]$b = $Matches[2]
            if ($a -gt $b) { $t = $a; $a = $b; $b = $t }
            $a..$b | ForEach-Object { $result.Add($_) }
        }
        elseif ($part -match '^\d+$') { $result.Add([int]$part) }
        else { throw "페이지 지정이 잘못됨: '$part' (예: all, 5, 2-7, 1,4,9-11)" }
    }
    return $result | Sort-Object -Unique | Where-Object { $_ -ge 1 -and $_ -le $pageCount }
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($PdfPath)) ([Windows.Storage.StorageFile])
$pdf = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
Write-Output "pages: $($pdf.PageCount)"

$targets = Resolve-Pages $Pages $pdf.PageCount
if (-not $targets -or $targets.Count -eq 0) { throw "렌더할 페이지가 없음 (문서 $($pdf.PageCount)쪽, 지정 '$Pages')" }

foreach ($p in $targets) {
    $page = $pdf.GetPage($p - 1)   # WinRT는 0-기반
    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $opts = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $opts.DestinationWidth = $Width
    AwaitAction ($page.RenderToStreamAsync($stream, $opts))
    $netStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream.GetInputStreamAt(0))
    $outPath = Join-Path $OutDir ("pdf-page{0:D3}.png" -f $p)
    $fileStream = [System.IO.File]::Create($outPath)
    $netStream.CopyTo($fileStream)
    $fileStream.Close()
    $stream.Dispose()
    $page.Dispose()
    Write-Output "saved $outPath"
}
