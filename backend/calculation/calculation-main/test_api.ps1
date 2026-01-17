param(
  [string]$Name="Test",
  [string]$Date="1990-01-01",
  [string]$Time="12:00",
  [int]$TzOffsetMinutes=330,
  [double]$Latitude=13.0827,
  [double]$Longitude=80.2707,
  [int]$Limit=5
)

# Build structured JSON body (avoids legacy conversion path)
$tzHours = [double]$TzOffsetMinutes / 60.0
$birthIso = "$Date" + 'T12:00:00'
Write-Host "Debug: Using fixed birthDateTime '$birthIso' for smoke test" -ForegroundColor DarkGray
$body = @{ 
  birthDateTime = $birthIso;
  location = @{ place=$Name; latitude=$Latitude; longitude=$Longitude; tzOffset=$tzHours };
  ayanamsaMode = 'TRUE_CITRA';
  calcType = 'drik'
} | ConvertTo-Json -Compress

Write-Host "POST /api/horoscope ..." -ForegroundColor Cyan
Write-Host "Request Body: $body" -ForegroundColor DarkGray
$resp = Invoke-RestMethod -Method Post -ContentType 'application/json' -Uri http://127.0.0.1:8080/api/horoscope -Body $body
# Debug dump of POST response to diagnose empty requestId cases
try {
  $respJson = $resp | ConvertTo-Json -Depth 8 -Compress
  Write-Host "POST Response: $respJson" -ForegroundColor DarkGray
} catch {}
# Prefer top-level requestId if present, else fallback to meta.requestId
if ($resp.PSObject.Properties.Name -contains 'requestId' -and $resp.requestId) {
  $rid = $resp.requestId
} else {
  $rid = $resp.meta.requestId
}
Write-Host "RequestId: $rid" -ForegroundColor Green

Write-Host "GET /api/dhasa/vimsottari" -ForegroundColor Cyan
$dhasa = Invoke-RestMethod -Uri ("http://127.0.0.1:8080/api/dhasa/vimsottari?request_id={0}&limit={1}" -f $rid,$Limit)

Write-Host "GET /api/transit" -ForegroundColor Cyan
$transit = Invoke-RestMethod -Uri ("http://127.0.0.1:8080/api/transit?request_id={0}" -f $rid)

Write-Host "GET /api/panchanga" -ForegroundColor Cyan
$panchanga = Invoke-RestMethod -Uri ("http://127.0.0.1:8080/api/panchanga?request_id={0}" -f $rid)

Write-Host "GET /api/panchanga/transit" -ForegroundColor Cyan
$tpanchanga = Invoke-RestMethod -Uri ("http://127.0.0.1:8080/api/panchanga/transit?request_id={0}" -f $rid)

Write-Host "GET /api/horoscope/sslike/view" -ForegroundColor Cyan
$ssUrl = ("http://127.0.0.1:8080/api/horoscope/sslike/view?request_id={0}" -f $rid)
Write-Host "URL: $ssUrl" -ForegroundColor DarkGray
$ss = Invoke-RestMethod -Uri $ssUrl

Write-Host "GET /api/horoscope/sslike/flat (D1)" -ForegroundColor Cyan
$flatUrl = ("http://127.0.0.1:8080/api/horoscope/sslike/flat?request_id={0}&factor=1" -f $rid)
Write-Host "URL: $flatUrl" -ForegroundColor DarkGray
$ssflat = Invoke-RestMethod -Uri $flatUrl
Write-Host "GET /api/horoscope/sslike/flat (D9)" -ForegroundColor Cyan
$flatUrl9 = ("http://127.0.0.1:8080/api/horoscope/sslike/flat?request_id={0}&factor=9" -f $rid)
Write-Host "URL: $flatUrl9" -ForegroundColor DarkGray
$ssflat9 = Invoke-RestMethod -Uri $flatUrl9

# Summarize
$result = [pscustomobject]@{
  RequestId = $rid
  HoroscopeGeneratedAt = $resp.meta.generatedAt
  DhasaCount = ($dhasa.periods | Measure-Object).Count
  TransitPlanets = ($transit.planets | ForEach-Object { $_.name }) -join ', '
  PanchangaKeys = ($panchanga.calendar.Keys | Select-Object -First 10) -join ', '
  TransitPanchangaKeys = ($tpanchanga.calendar.Keys | Select-Object -First 10) -join ', '
  SSLikeAscSign = $ss.ascendantSign
  SSLikeH1 = ($ss.houses | Where-Object { $_.index -eq 1 }).items -join ', '
  SSLikeFirstPlanet = ($ss.planets | Select-Object -First 1).name
  SSLikePanelRows = ($ss.panelRows | Select-Object -First 3 | ConvertTo-Json -Depth 6)
  VargasSummary = (($ss.vargas | ForEach-Object { "D$($_.factor):" + ($_.rows | Measure-Object | Select-Object -Expand Count) }) -join '; ')
  ExtendedPoints = (($ss.extendedPoints | ForEach-Object { $_.name }) | Sort-Object -Unique) -join ', '
  FlatPreview = ($ssflat.rows | Select-Object -First 10 | ConvertTo-Json -Depth 6)
  FlatPreviewD9 = ($ssflat9.rows | Select-Object -First 5 | ConvertTo-Json -Depth 6)
}

$result | Format-List

# Optionally output full JSON detail
#$full = [pscustomobject]@{ meta=$resp.meta; dhasa=$dhasa; transit=$transit; panchanga=$panchanga }
#$full | ConvertTo-Json -Depth 8
