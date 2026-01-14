$body = @{ 
  birthDateTime = '2000-01-01T06:30:00'
  location = @{ place='Chennai,IN'; tzOffset=5.5 }
  language = 'en'
  divisionalFactors = @(1,9)
  sendToAgent = $false
}
$json = $body | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/horoscope -Body $json -ContentType 'application/json' | ConvertTo-Json -Depth 6
