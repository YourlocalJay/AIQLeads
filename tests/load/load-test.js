import { check, sleep } from 'k6';
import http from 'k6/http';
import { Rate } from 'k6/metrics';

// Custom metrics
const errors = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at peak
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    errors: ['rate<0.1'],             // Error rate must be less than 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Main test scenario
export default function() {
  // AI Recommendation testing
  const recommendationCheck = http.get(`${BASE_URL}/api/v1/recommendations`);
  check(recommendationCheck, {
    'recommendations_status_2xx': (r) => r.status >= 200 && r.status < 300,
    'recommendations_response_time': (r) => r.timings.duration < 500,
  });
  sleep(1);

  // Cart management testing
  const cartData = {
    user_id: 'test_user',
    items: [
      { id: 'item1', quantity: 1 },
      { id: 'item2', quantity: 2 },
    ],
  };
  const cartCheck = http.post(`${BASE_URL}/api/v1/cart`, JSON.stringify(cartData), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(cartCheck, {
    'cart_status_2xx': (r) => r.status >= 200 && r.status < 300,
    'cart_response_time': (r) => r.timings.duration < 200,
  });
  sleep(1);

  // Market insights testing
  const marketCheck = http.get(`${BASE_URL}/api/v1/market/insights`);
  check(marketCheck, {
    'market_status_2xx': (r) => r.status >= 200 && r.status < 300,
    'market_response_time': (r) => r.timings.duration < 300,
  });
  sleep(1);

  // Geospatial component testing
  const geoData = {
    latitude: 40.7128,
    longitude: -74.0060,
    radius: 5000,
  };
  const geoCheck = http.post(`${BASE_URL}/api/v1/geo/search`, JSON.stringify(geoData), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(geoCheck, {
    'geo_status_2xx': (r) => r.status >= 200 && r.status < 300,
    'geo_response_time': (r) => r.timings.duration < 400,
  });
  sleep(1);

  // WebSocket connection test
  const ws = new WebSocket(`${BASE_URL.replace('http', 'ws')}/ws`);
  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'subscribe', channel: 'market_updates' }));
  };
  ws.onmessage = (e) => {
    check(e, {
      'ws_message_received': () => true,
    });
  };
  sleep(5);
  ws.close();
}

// Lifecycle hooks
export function setup() {
  // Initialize test data
  const setupData = {
    testUser: 'performance_test_user',
    timestamp: new Date().toISOString(),
  };
  return setupData;
}

export function teardown(data) {
  // Cleanup test data
  http.del(`${BASE_URL}/api/v1/test-data/${data.testUser}`);
}