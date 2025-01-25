# AIQLeads API Reference

This document provides a detailed reference for all API endpoints implemented in the AIQLeads MVP. Each endpoint includes its purpose, request/response details, and examples.

---

## Authentication

### 1. **Login**
- **Endpoint:** `POST /api/auth/login`
- **Description:** Authenticates a user and returns a JWT token.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response:**
  - **200 OK:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
      "token_type": "bearer"
    }
    ```
  - **401 Unauthorized:** Invalid credentials.

### 2. **Register**
- **Endpoint:** `POST /api/auth/register`
- **Description:** Registers a new user.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword",
    "subscription_tier": "Basic"
  }
  ```
- **Response:**
  - **201 Created:**
    ```json
    {
      "id": 1,
      "email": "user@example.com",
      "subscription_tier": "Basic",
      "credits": 100
    }
    ```
  - **400 Bad Request:** Missing or invalid fields.

---

## Lead Marketplace

### 1. **Search Leads**
- **Endpoint:** `GET /api/leads/search`
- **Description:** Searches leads based on filters.
- **Query Parameters:**
  | Parameter      | Type     | Description                     |
  |----------------|----------|---------------------------------|
  | `location`     | `string` | City or zip code (e.g., "Austin"). |
  | `radius`       | `number` | Radius in miles.                |
  | `min_price`    | `number` | Minimum price filter.           |
  | `max_price`    | `number` | Maximum price filter.           |
  | `property_type`| `string` | Type of property (e.g., "condo"). |

- **Response:**
  - **200 OK:**
    ```json
    [
      {
        "id": 101,
        "title": "3-Bedroom House",
        "price": 350000,
        "location": "Austin, TX",
        "quality_score": 85,
        "fraud_score": 5,
        "source": "Craigslist"
      }
    ]
    ```
  - **400 Bad Request:** Invalid query parameters.

### 2. **Get Lead Details**
- **Endpoint:** `GET /api/leads/{lead_id}`
- **Description:** Fetches detailed information about a specific lead.
- **Path Parameters:**
  | Parameter  | Type     | Description              |
  |------------|----------|--------------------------|
  | `lead_id`  | `integer`| Unique identifier of lead|

- **Response:**
  - **200 OK:**
    ```json
    {
      "id": 101,
      "title": "3-Bedroom House",
      "description": "Spacious house with a pool.",
      "price": 350000,
      "location": {
        "lat": 30.2672,
        "lng": -97.7431
      },
      "quality_score": 85,
      "fraud_score": 5,
      "source": "Craigslist",
      "metadata": {
        "posting_date": "2025-01-01T10:00:00Z",
        "property_type": "single-family"
      }
    }
    ```
  - **404 Not Found:** Lead not found.

---

## Cart Management

### 1. **Add to Cart**
- **Endpoint:** `POST /api/cart`
- **Description:** Adds a lead to the user’s cart.
- **Request Body:**
  ```json
  {
    "lead_id": 101
  }
  ```
- **Response:**
  - **200 OK:**
    ```json
    {
      "message": "Lead added to cart.",
      "cart": [
        {
          "lead_id": 101,
          "expires_at": "2025-01-01T15:00:00Z"
        }
      ]
    }
    ```
  - **400 Bad Request:** Lead already in cart.

### 2. **View Cart**
- **Endpoint:** `GET /api/cart`
- **Description:** Retrieves the user’s active cart.
- **Response:**
  - **200 OK:**
    ```json
    [
      {
        "lead_id": 101,
        "expires_at": "2025-01-01T15:00:00Z"
      }
    ]
    ```

---

## Dynamic Pricing

### 1. **Get Dynamic Pricing**
- **Endpoint:** `GET /api/pricing/{lead_id}`
- **Description:** Fetches the dynamic price of a lead.
- **Response:**
  - **200 OK:**
    ```json
    {
      "lead_id": 101,
      "dynamic_price": 340000,
      "discount": 10000,
      "tier": "Pro"
    }
    ```

---

## Recommendations

### 1. **Get Recommendations**
- **Endpoint:** `GET /api/recommendations`
- **Description:** Provides personalized lead recommendations for the user.
- **Response:**
  - **200 OK:**
    ```json
    [
      {
        "id": 102,
        "title": "Modern Condo",
        "price": 250000,
        "location": "Dallas, TX",
        "quality_score": 90,
        "source": "Zillow"
      }
    ]
    ```

---

## Testing and Mocking APIs
- Use tools like Postman, Swagger UI, or HTTPie for testing API endpoints.
- Mock API responses for integration tests.

---

This **API Reference** will continue to evolve as new endpoints and features are added to AIQLeads. Ensure that all additions are documented in this file.
