# AIQLeads - Schema Documentation

This document provides an exhaustive overview of the database schemas used in the AIQLeads MVP. It outlines the core models, their fields, relationships, constraints, and key features. Each schema has been optimized for scalability, geospatial queries, and integration with the dynamic pricing and recommendation systems.

---

## Core Schemas

### 1. **User Schema**
The `User` model stores all user-related information, including subscription details, account settings, and authentication data.

#### Fields
| Field                 | Type           | Constraints            | Description                                      |
|-----------------------|----------------|------------------------|--------------------------------------------------|
| `id`                 | Integer        | Primary Key           | Unique identifier for the user.                 |
| `email`              | String         | Unique, Not Null      | Email address of the user.                      |
| `password_hash`      | String         | Not Null              | Hashed password for secure authentication.      |
| `subscription_tier`  | Enum           | Not Null, Default: `Basic` | Subscription level (Basic, Pro, Enterprise). |
| `credits`            | Float          | Default: 0.0          | Available credits for purchasing leads.         |
| `created_at`         | DateTime       | Default: `NOW()`      | Account creation timestamp.                     |
| `updated_at`         | DateTime       | Auto-updated          | Last account update timestamp.                  |

#### Relationships
- **One-to-Many:** Users can own multiple transactions and subscriptions.

---

### 2. **Lead Schema**
The `Lead` model stores real estate lead data, including geospatial location and quality metrics.

#### Fields
| Field                 | Type            | Constraints            | Description                                      |
|-----------------------|-----------------|------------------------|--------------------------------------------------|
| `id`                 | Integer         | Primary Key           | Unique identifier for the lead.                 |
| `title`              | String          | Not Null              | Title of the listing.                           |
| `description`        | Text            | Nullable              | Detailed description of the property.           |
| `price`              | Float           | Not Null              | Listing price of the property.                  |
| `location`           | Geography(Point)| Not Null              | Geospatial point for property location.         |
| `fraud_score`        | Float           | Default: 0.0          | AI-determined fraud likelihood.                 |
| `quality_score`      | Float           | Default: 0.0          | AI-determined lead quality score.               |
| `created_at`         | DateTime        | Default: `NOW()`      | Lead creation timestamp.                        |
| `updated_at`         | DateTime        | Auto-updated          | Last lead update timestamp.                     |

#### Relationships
- **Many-to-One:** Leads can belong to a single `Transaction` or be sold to a user.
- **Indexes:** Spatial index on the `location` field for fast geospatial queries.

---

### 3. **Transaction Schema**
The `Transaction` model tracks purchases and interactions with leads.

#### Fields
| Field                 | Type           | Constraints            | Description                                      |
|-----------------------|----------------|------------------------|--------------------------------------------------|
| `id`                 | Integer        | Primary Key           | Unique identifier for the transaction.          |
| `user_id`            | Foreign Key    | References `User(id)` | The user who performed the transaction.         |
| `lead_id`            | Foreign Key    | References `Lead(id)` | The purchased lead.                             |
| `price`              | Float          | Not Null              | Final price of the transaction.                 |
| `created_at`         | DateTime       | Default: `NOW()`      | Transaction timestamp.                          |
| `updated_at`         | DateTime       | Auto-updated          | Last update timestamp for this transaction.     |

#### Relationships
- **One-to-Many:** Transactions reference both users and leads.
- **Constraints:**
  - Ensure no lead is sold to more than one user (one-to-one relationship).

---

### 4. **Subscription Schema**
The `Subscription` model tracks user subscriptions and billing cycles.

#### Fields
| Field                 | Type           | Constraints            | Description                                      |
|-----------------------|----------------|------------------------|--------------------------------------------------|
| `id`                 | Integer        | Primary Key           | Unique identifier for the subscription.         |
| `user_id`            | Foreign Key    | References `User(id)` | The user who owns the subscription.             |
| `tier`               | Enum           | Not Null              | Subscription level (Basic, Pro, Enterprise).    |
| `start_date`         | DateTime       | Not Null              | Subscription start date.                        |
| `end_date`           | DateTime       | Nullable              | Subscription expiration date.                   |
| `auto_renew`         | Boolean        | Default: `True`       | Indicates whether the subscription auto-renews. |

#### Relationships
- **One-to-One:** Each user can have one active subscription.

---

### 5. **Market Insights Schema**
The `MarketInsight` model stores aggregated analytics data for specific regions.

#### Fields
| Field                 | Type            | Constraints            | Description                                      |
|-----------------------|-----------------|------------------------|--------------------------------------------------|
| `id`                 | Integer         | Primary Key           | Unique identifier for the insight.              |
| `region_name`        | String          | Not Null              | Name of the region (e.g., city, zip code).      |
| `median_price`       | Float           | Nullable              | Median property price in the region.            |
| `avg_price`          | Float           | Nullable              | Average property price in the region.           |
| `property_type_distribution` | JSON | Nullable | Distribution of property types (e.g., condos vs. rentals). |
| `price_trends`       | JSON            | Nullable              | Historical price trends.                        |
| `demand_metrics`     | JSON            | Nullable              | Metrics such as views, inquiries, and offers.   |
| `analysis_period`    | String          | Not Null              | Time period covered by the insight.             |

#### Relationships
- **Indexes:** Ensure fast queries by region name.

---

## Schema Relationships

```plaintext
User
├── Transaction
│   ├── Lead
├── Subscription

MarketInsight
```

---

## Best Practices & Notes

- **Normalization:** Ensure that frequently queried fields (e.g., `price`, `location`) are indexed.
- **Geospatial Queries:** Use PostGIS for efficient spatial queries (e.g., radius-based searches).
- **Fraud Prevention:** Include `fraud_score` and related validations for cleaner data.
- **Optimized Updates:** Use triggers or event-based pipelines to update Elasticsearch or Redis upon database changes.

---

## Future Additions
- **User Activity Logs:** Add tables for user searches, cart interactions, and lead purchases.
- **Advanced Metrics:** Extend the `MarketInsights` schema to include rental yield and demographic trends.

---
