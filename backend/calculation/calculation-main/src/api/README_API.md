# PyJHora Web API (Initial Draft)

Run (development):

```
uvicorn api.app:app --reload --port 8080
```

POST /api/horoscope sample body:
```
{
  "birthDateTime": "1990-05-21T10:15:00",
  "location": {"place": "Chennai,IN", "tzOffset": 5.5},
  "language": "en",
  "divisionalFactors": [1,9,10],
  "sendToAgent": false
}
```
