# Stock Predictor API Reference

## Base URL

```
Production: https://api.stockpredictor.com
Development: http://localhost:8000
```

## Authentication

All requests require an API key or JWT token in the `Authorization` header:

```
Authorization: Bearer {jwt_token}
```

## Response Format

All responses follow a standard format:

### Success Response (2xx)
```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

### Error Response (4xx, 5xx)
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "timestamp": "2026-01-03T10:30:45.123Z",
    "request_id": "req-uuid-1234"
  }
}
```

## Rate Limiting

All API endpoints are rate limited:

- **Search endpoints**: 100 requests/hour
- **Data endpoints**: 200 requests/hour
- **Prediction endpoints**: 150 requests/hour
- **Auth endpoints**: 30 requests/hour

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1672748400
```

## Endpoints

### Stocks

#### Search Stocks
```
GET /api/stocks/search?query={query}&limit={limit}
```

**Parameters:**
- `query` (string, required): Search term (company name or symbol)
- `limit` (integer, optional): Number of results (default: 10, max: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "country": "US"
    }
  ]
}
```

#### Get Stock Details
```
GET /api/stocks/{symbol}
```

**Parameters:**
- `symbol` (string, required): Stock symbol (e.g., "AAPL")

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 150.25,
    "change": 2.50,
    "change_percent": 1.69,
    "market_cap": 2500000000000,
    "pe_ratio": 28.5,
    "eps": 5.25,
    "dividend_yield": 0.42,
    "fifty_two_week_high": 189.95,
    "fifty_two_week_low": 124.17
  }
}
```

#### Get Price History
```
GET /api/stocks/{symbol}/history?period={period}
```

**Parameters:**
- `symbol` (string, required): Stock symbol
- `period` (string, optional): Time period (default: "1y", options: "1mo", "3mo", "6mo", "1y", "5y")

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "prices": [
      {
        "date": "2026-01-02",
        "open": 148.50,
        "high": 152.00,
        "low": 148.25,
        "close": 150.25,
        "volume": 52000000
      }
    ]
  }
}
```

### Predictions

#### Get Stock Prediction
```
GET /api/predictions/{symbol}
```

**Parameters:**
- `symbol` (string, required): Stock symbol

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "predicted_price": 155.75,
    "confidence": 0.85,
    "trend": "upward",
    "prediction_date": "2026-01-03",
    "forecast_date": "2026-01-10",
    "support_levels": [145.00, 140.00],
    "resistance_levels": [160.00, 165.00],
    "model_info": {
      "model_type": "LSTM",
      "accuracy": 0.78,
      "inference_time_ms": 125
    }
  }
}
```

#### Get Multiple Predictions
```
POST /api/predictions/batch
```

**Request Body:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "forecast_days": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "symbol": "AAPL",
        "predicted_price": 155.75,
        "confidence": 0.85
      },
      {
        "symbol": "GOOGL",
        "predicted_price": 98.50,
        "confidence": 0.82
      }
    ],
    "generated_at": "2026-01-03T10:30:45.123Z"
  }
}
```

### Watchlists

#### Create Watchlist
```
POST /api/watchlists
```

**Request Body:**
```json
{
  "name": "My Watchlist",
  "description": "Stocks to monitor",
  "stocks": ["AAPL", "GOOGL"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "My Watchlist",
    "description": "Stocks to monitor",
    "created_at": "2026-01-03T10:30:45.123Z"
  }
}
```

#### Get Watchlists
```
GET /api/watchlists
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "My Watchlist",
      "stock_count": 2,
      "created_at": "2026-01-03T10:30:45.123Z"
    }
  ]
}
```

#### Get Watchlist Details
```
GET /api/watchlists/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "My Watchlist",
    "stocks": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "current_price": 150.25,
        "change_percent": 1.69,
        "predicted_price": 155.75
      }
    ]
  }
}
```

#### Add Stock to Watchlist
```
POST /api/watchlists/{id}/stocks
```

**Request Body:**
```json
{
  "symbol": "NVDA",
  "notes": "AI chip leader"
}
```

#### Remove Stock from Watchlist
```
DELETE /api/watchlists/{id}/stocks/{symbol}
```

#### Delete Watchlist
```
DELETE /api/watchlists/{id}
```

### Analysis

#### Get Historical Analysis
```
GET /api/analysis/{symbol}?period={period}&indicators={indicators}
```

**Parameters:**
- `symbol` (string, required): Stock symbol
- `period` (string, optional): Time period (default: "1y")
- `indicators` (string, optional): Comma-separated indicators (e.g., "RSI,MACD,Bollinger")

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "period": "1y",
    "analysis": {
      "trend": "upward",
      "volatility": 0.25,
      "rsi": 65.5,
      "macd": { "value": 2.5, "signal": 2.0, "histogram": 0.5 },
      "bollinger_bands": {
        "upper": 160.00,
        "middle": 150.00,
        "lower": 140.00
      }
    }
  }
}
```

#### Run Backtest
```
POST /api/analysis/backtest
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "strategy": "buy_low_sell_high",
  "start_date": "2023-01-01",
  "end_date": "2026-01-03",
  "initial_capital": 10000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "strategy": "buy_low_sell_high",
    "total_return": 0.45,
    "annualized_return": 0.15,
    "sharpe_ratio": 1.25,
    "max_drawdown": -0.08,
    "win_rate": 0.65,
    "trades": 25
  }
}
```

### Health & Status

#### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-03T10:30:45.123Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "external_apis": "healthy"
  }
}
```

#### Metrics
```
GET /metrics
```

Returns Prometheus-format metrics for monitoring.

## Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input parameters |
| INVALID_SYMBOL | 400 | Invalid stock symbol |
| AUTHENTICATION_REQUIRED | 401 | Missing or invalid token |
| PERMISSION_DENIED | 403 | User lacks permission |
| NOT_FOUND | 404 | Resource not found |
| DUPLICATE_RESOURCE | 409 | Resource already exists |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| EXTERNAL_API_ERROR | 502 | External API failure |
| DATABASE_ERROR | 500 | Database operation failed |
| INTERNAL_ERROR | 500 | Unexpected server error |

## Examples

### Python
```python
import requests

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/stocks/AAPL",
    headers=headers
)
print(response.json())
```

### JavaScript
```javascript
const response = await fetch('/api/stocks/AAPL', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const data = await response.json();
console.log(data);
```

### cURL
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/stocks/AAPL
```

## Pagination

List endpoints support pagination:

```
GET /api/stocks/search?query=apple&page=1&page_size=10
```

Response includes pagination metadata:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 50,
    "total_pages": 5
  }
}
```

## Filtering & Sorting

Many endpoints support filtering and sorting:

```
GET /api/watchlists?sort=-created_at&status=active
```

## Webhooks (Future)

Subscribe to real-time updates:

```
POST /api/webhooks
```

Receive notifications when:
- Stock price crosses threshold
- Prediction confidence changes
- Watchlist updated
- Analysis completed
