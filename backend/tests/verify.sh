#!/bin/bash
echo "Testing Place Search with curl..."
curl -v "http://localhost:8000/calc/api/v1/places/search?q=Bangalore&limit=5&lang=en"
echo -e "\nDone."
