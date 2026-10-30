# OCR de imagens PNG com o motor nativo do Windows (Windows.Media.Ocr).
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File ocr_windows.ps1 <lista.txt> <saida.json>
# lista.txt = um caminho de PNG por linha; saida.json = {caminho: texto}
param([string]$lista, [string]$saida)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$res = @{}
foreach ($img in [IO.File]::ReadAllLines($lista)) {
  try {
    $f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($img)) ([Windows.Storage.StorageFile])
    $s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $d = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $b = Await ($d.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $r = Await ($eng.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
    $linhas = @($r.Lines | % { $_.Text })
    $res[$img] = ($linhas -join "`n")
    $s.Dispose()
  } catch { $res[$img] = "" }
}
[IO.File]::WriteAllText($saida, ($res | ConvertTo-Json -Depth 3), [Text.Encoding]::UTF8)
