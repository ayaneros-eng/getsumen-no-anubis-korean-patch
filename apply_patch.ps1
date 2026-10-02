param(
  [Parameter(Mandatory=$true)][string]$SourceRom,
  [string]$OutputRom
)
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
$packageDir=Split-Path -Parent $PSCommandPath
$manifest=Get-Content -LiteralPath (Join-Path $packageDir 'patch_manifest.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$sourcePath=(Resolve-Path -LiteralPath $SourceRom).Path
$source=[System.IO.File]::ReadAllBytes($sourcePath)
$sourceHash=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
$entry=@($manifest.patches | Where-Object {$_.source_sha256 -eq $sourceHash})
if($entry.Count -ne 1){throw 'Unsupported source ROM hash. Use the specified headerless Japanese ROM, exact v1.10, or previous punctuation release.'}
$patchPath=Join-Path $packageDir $entry[0].file
if((Get-FileHash -LiteralPath $patchPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry[0].patch_sha256){throw 'Patch hash mismatch'}
$patch=[System.IO.File]::ReadAllBytes($patchPath)
if([System.Text.Encoding]::ASCII.GetString($patch,0,5) -ne 'PATCH'){throw 'Invalid IPS header'}
$bytes=[System.Collections.Generic.List[byte]]::new()
$bytes.AddRange($source)
$offset=5
while([System.Text.Encoding]::ASCII.GetString($patch,$offset,3) -ne 'EOF'){
  $at=($patch[$offset]*65536)+($patch[$offset+1]*256)+$patch[$offset+2]
  $count=($patch[$offset+3]*256)+$patch[$offset+4]
  $offset+=5
  if($count -eq 0){
    $count=($patch[$offset]*256)+$patch[$offset+1]
    $value=$patch[$offset+2];$offset+=3
    while($bytes.Count -lt $at+$count){$bytes.Add(0)}
    for($j=0;$j -lt $count;$j++){$bytes[$at+$j]=$value}
  }else{
    while($bytes.Count -lt $at+$count){$bytes.Add(0)}
    for($j=0;$j -lt $count;$j++){$bytes[$at+$j]=$patch[$offset+$j]}
    $offset+=$count
  }
}
$offset+=3
if($patch.Length-$offset -eq 3){
  $size=($patch[$offset]*65536)+($patch[$offset+1]*256)+$patch[$offset+2]
  if($bytes.Count -gt $size){$bytes.RemoveRange($size,$bytes.Count-$size)}
  while($bytes.Count -lt $size){$bytes.Add(0)}
}
$sha=[System.Security.Cryptography.SHA256]::Create()
$targetBytes=$bytes.ToArray()
$targetHash=([BitConverter]::ToString($sha.ComputeHash($targetBytes))).Replace('-','').ToLowerInvariant()
$sha.Dispose()
if($targetHash -ne $manifest.target_sha256){throw 'Rebuilt ROM hash mismatch'}
if(!$OutputRom){$OutputRom=Join-Path (Split-Path -Parent $sourcePath) 'Anubis_KR_refined.sfc'}
$outputPath=[System.IO.Path]::GetFullPath($OutputRom)
if($outputPath -eq $sourcePath){throw 'Output must differ from source ROM'}
if(Test-Path -LiteralPath $outputPath){throw 'Output already exists; choose a different output path'}
[System.IO.File]::WriteAllBytes($outputPath,$targetBytes)
Write-Output "Verified output: $outputPath"
Write-Output "SHA-256: $targetHash"
