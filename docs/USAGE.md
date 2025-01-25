# Usage Guide for AIQLeads

This document provides a comprehensive guide to setting up, configuring, and using the AIQLeads MVP. Follow these steps to ensure seamless installation and operation.

---

## Prerequisites

Before proceeding, ensure that your development environment meets the following requirements:

- **Python**: Version 3.10 or higher
- **PostgreSQL**: Version 14+ with PostGIS extension enabled
- **Redis**: Version 5.0 or higher
- **Docker**: Installed and configured (optional but recommended)
- **Node.js**: Version 14+ (if running the frontend)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/YourlocalJay/AIQLeads.git
cd AIQLeads
```

### Step 2: Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Copy the `.env.example` file and configure it for your environment:

```bash
cp .env.example .env
```

Update `.env` with your PostgreSQL, Redis, and API keys (e.g., OpenAI, Stripe).

### Step 5: Run Database Migrations

Ensure PostgreSQL and PostGIS are configured. Then run migrations:

```bash
alembic upgrade head
```

### Step 6: Set Up Redis

Start Redis locally or via Docker:

```bash
docker run -d --name redis -p 6379:6379 redis:6
```

---

## Running the Application

### Option 1: Run Locally

#### Start the Backend

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start the Frontend (Optional)

Navigate to the `frontend/` directory and install dependencies:

```bash
cd frontend
yarn install
yarn start
```

### Option 2: Run with Docker

#### Step 1: Build and Start Containers

```bash
docker-compose up --build
```

#### Step 2: Access the Application

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend**: [http://localhost:3000](http://localhost:3000)

---

## Usage

### API Endpoints

1. **Lead Marketplace**:
   - `GET /api/leads/`: Retrieve available leads.
   - `POST /api/leads/purchase`: Purchase selected leads.

2. **Market Insights**:
   - `GET /api/insights/{region}`: Get analytics for a specific region.
   - `GET /api/insights/heatmap`: Retrieve demand heatmap data.

3. **User Management**:
   - `POST /api/users/signup`: Register a new user.
   - `POST /api/users/login`: Authenticate and retrieve a JWT token.

4. **Subscription Management**:
   - `GET /api/subscriptions`: View subscription tiers.
   - `POST /api/subscriptions/upgrade`: Upgrade your subscription.

### Frontend Features

1. **Dashboard**:
   - View your credit balance, cart items, and personalized lead recommendations.

2. **Lead Explorer**:
   - Search leads by filters (price, property type, location radius).
   - Add leads to your cart.

3. **Cart Management**:
   - View leads in your cart with timers indicating expiration.
   - Proceed to checkout and purchase leads using credits.

---

## Testing

### Run Unit Tests

```bash
pytest tests/unit
```

### Run Integration Tests

```bash
pytest tests/integration
```

### Run End-to-End Tests

Ensure all services are running, then execute:

```bash
pytest tests/e2e
```

---

## Monitoring and Logs

1. **Prometheus Metrics**:
   - Visit [http://localhost:9090](http://localhost:9090) to view metrics.

2. **Grafana Dashboards**:
   - Access via [http://localhost:3001](http://localhost:3001) (if configured).

3. **Application Logs**:
   - Logs are available in the `logs/` directory or via Docker logs:

     ```bash
     docker logs aiqleads-backend
     ```

---

## Deployment

1. **Staging Environment**:
   - Configure `.env.staging` with appropriate credentials.
   - Deploy using the CD pipeline or manually via Docker:

     ```bash
     docker-compose -f docker-compose.staging.yml up --build
     ```

2. **Production Deployment**:
   - Use Kubernetes or AWS ECS for scalable deployment.
   - Ensure secrets (e.g., API keys) are securely stored (e.g., AWS Secrets Manager).

---

## Troubleshooting

1. **Database Connection Issues**:
   - Verify PostgreSQL is running and the credentials in `.env` are correct.

2. **Redis Unavailable**:
   - Check Redis is running on port `6379`.

3. **Docker Errors**:
   - Run `docker-compose down` to stop all containers.
   - Rebuild and restart:

     ```bash
     docker-compose up --build
     ```

4. **Testing Failures**:
   - Ensure all migrations are applied and test dependencies are installed.

---

## Contact

For support or inquiries:
- **Owner**: [YourlocalJay](https://github.com/YourlocalJay)
- **Email**: support@aiqleads.com (planned)

Stay updated by reviewing the [CHANGELOG](CHANGELOG.md) and project documentation.
