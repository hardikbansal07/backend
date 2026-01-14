$body = @{ birthDateTime='1990-01-01T12:00:00'; location=@{place='Test'; latitude=13.0827; longitude=80.2707; tzOffset=5.5}; ayanamsaMode='TRUE_CITRA'; calcType='drik' } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Method Post -ContentType 'application/json' -Uri http://127.0.0.1:8080/api/horoscope -Body $body
$r | Get-Member
'---'
$r | ConvertTo-Json -Depth 3
'---'
'keys: ' + ($r.PSObject.Properties.Name -join ', ')
'rid_top: ' + ($r.requestId)
'rid_meta: ' + ($r.meta.requestId)
