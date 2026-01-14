// Test script for Panchanga and Transit endpoints
const axios = require('axios');

const BASE_URL = 'http://localhost:8080';

async function testPanchangaEndpoints() {
    console.log('🧪 Testing Panchanga & Transit Endpoints\n');

    try {
        // Step 1: Create a horoscope to get request_id
        console.log('1️⃣ Creating horoscope...');
        const horoscopeResponse = await axios.post(`${BASE_URL}/api/horoscope`, {
            birthDateTime: '2001-03-07T16:20:00',
            location: {
                place: 'Delhi',
                latitude: 28.6139,
                longitude: 77.2090,
                tzOffset: 5.5
            }
        });

        const requestId = horoscopeResponse.data.requestId;
        console.log(`✅ Horoscope created with requestId: ${requestId}\n`);

        // Step 2: Test /api/panchanga
        console.log('2️⃣ Testing /api/panchanga...');
        const panchangaResponse = await axios.get(`${BASE_URL}/api/panchanga`, {
            params: { request_id: requestId }
        });
        console.log('✅ Panchanga endpoint works!');
        console.log('Response keys:', Object.keys(panchangaResponse.data));
        console.log();

        // Step 3: Test /api/panchanga/transit
        console.log('3️⃣ Testing /api/panchanga/transit...');
        const transitPanchangaResponse = await axios.get(`${BASE_URL}/api/panchanga/transit`, {
            params: {
                request_id: requestId,
                dateTime: '2024-11-29T14:00:00'
            }
        });
        console.log('✅ Panchanga/transit endpoint works!');
        console.log('Sample data:', JSON.stringify(transitPanchangaResponse.data, null, 2).substring(0, 500));
        console.log();

        // Step 4: Test /api/transit
        console.log('4️⃣ Testing /api/transit...');
        const transitResponse = await axios.get(`${BASE_URL}/api/transit`, {
            params: { request_id: requestId }
        });
        console.log('✅ Transit endpoint works!');
        console.log(`Found ${transitResponse.data.planets?.length || 0} planets`);
        console.log();

        console.log('🎉 All endpoints working successfully!');

    } catch (error) {
        console.error('❌ Error:', error.response?.data || error.message);
        process.exit(1);
    }
}

testPanchangaEndpoints();
