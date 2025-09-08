# XGet Analytics Service API Documentation

## Overview

The XGet Analytics Service provides comprehensive analytics and statistics for the XGet platform, including account monitoring, proxy performance analysis, task execution metrics, and data collection results analysis.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Health Check

### Get Service Health

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "analytics"
}
```

## Account Analytics

### Get Real-time Account Statistics

```http
GET /analytics/accounts/realtime
```

**Response:**
```json
{
  "success": true,
  "message": "Account realtime analytics retrieved successfully",
  "data": {
    "total_accounts": 100,
    "active_accounts": 85,
    "login_success_rate": 95.5,
    "error_accounts": 5
  }
}
```

### Get Historical Account Trends

```http
GET /analytics/accounts/history?time_range=24h&dimensions=status,type
```

**Query Parameters:**
- `time_range` (optional): Time range for analysis (1h, 24h, 7d, 30d). Default: 24h
- `dimensions` (optional): List of dimensions to group by (status, type)

**Response:**
```json
{
  "success": true,
  "message": "Account history analytics retrieved successfully",
  "data": {
    "time_range": "24h",
    "trends": [
      {
        "timestamp": "2025-09-01T12:00:00",
        "active_accounts": 80
      },
      {
        "timestamp": "2025-09-01T18:00:00", 
        "active_accounts": 82
      }
    ]
  }
}
```

## Proxy Analytics

### Get Real-time Proxy Statistics

```http
GET /analytics/proxies/realtime
```

**Response:**
```json
{
  "success": true,
  "message": "Proxy realtime analytics retrieved successfully",
  "data": {
    "total_proxies": 50,
    "active_proxies": 45,
    "avg_latency": 150.2,
    "success_rate": 92.8
  }
}
```

### Get Historical Proxy Performance

```http
GET /analytics/proxies/history?time_range=24h&country=US&isp=Comcast
```

**Query Parameters:**
- `time_range` (optional): Time range for analysis (1h, 24h, 7d, 30d). Default: 24h
- `country` (optional): Filter by country code
- `isp` (optional): Filter by ISP name

**Response:**
```json
{
  "success": true,
  "message": "Proxy history analytics retrieved successfully",
  "data": {
    "time_range": "24h",
    "performance_trends": [
      {
        "timestamp": "2025-09-01T12:00:00",
        "avg_latency": 160,
        "success_rate": 90
      },
      {
        "timestamp": "2025-09-01T18:00:00",
        "avg_latency": 155, 
        "success_rate": 91
      }
    ]
  }
}
```

## Task Analytics

### Get Real-time Task Statistics

```http
GET /analytics/tasks/realtime
```

**Response:**
```json
{
  "success": true,
  "message": "Task realtime analytics retrieved successfully",
  "data": {
    "total_tasks": 1000,
    "completed_tasks": 850,
    "failed_tasks": 50,
    "avg_completion_time": 120.5
  }
}
```

### Get Historical Task Efficiency

```http
GET /analytics/tasks/history?time_range=24h&task_type=scraping&status=completed
```

**Query Parameters:**
- `time_range` (optional): Time range for analysis (1h, 24h, 7d, 30d). Default: 24h
- `task_type` (optional): Filter by task type
- `status` (optional): Filter by task status

**Response:**
```json
{
  "success": true,
  "message": "Task history analytics retrieved successfully",
  "data": {
    "time_range": "24h",
    "efficiency_trends": [
      {
        "timestamp": "2025-09-01T12:00:00",
        "completed_tasks": 400,
        "avg_time": 130
      },
      {
        "timestamp": "2025-09-01T18:00:00",
        "completed_tasks": 450,
        "avg_time": 125
      }
    ]
  }
}
```

### Get Task Efficiency Metrics

```http
GET /analytics/tasks/efficiency
```

**Response:**
```json
{
  "success": true,
  "message": "Task efficiency analytics retrieved successfully",
  "data": {
    "overall_efficiency": 85.0,
    "success_rate": 92.5,
    "avg_processing_time": 118.3,
    "peak_performance_hours": [14, 15, 16]
  }
}
```

## Result Analytics

### Get Real-time Result Statistics

```http
GET /analytics/results/realtime
```

**Response:**
```json
{
  "success": true,
  "message": "Result realtime analytics retrieved successfully",
  "data": {
    "total_documents": 50000,
    "valid_documents": 48500,
    "invalid_documents": 1500,
    "data_quality_score": 97.0
  }
}
```

### Get Historical Collection Trends

```http
GET /analytics/results/history?time_range=24h&data_type=twitter
```

**Query Parameters:**
- `time_range` (optional): Time range for analysis (1h, 24h, 7d, 30d). Default: 24h
- `data_type` (optional): Filter by data type

**Response:**
```json
{
  "success": true,
  "message": "Result history analytics retrieved successfully",
  "data": {
    "time_range": "24h",
    "collection_trends": [
      {
        "timestamp": "2025-09-01T12:00:00",
        "collected": 20000,
        "valid": 19400
      },
      {
        "timestamp": "2025-09-01T18:00:00",
        "collected": 25000,
        "valid": 24300
      }
    ]
  }
}
```

### Get Data Quality Analysis

```http
GET /analytics/results/quality
```

**Response:**
```json
{
  "success": true,
  "message": "Result quality analytics retrieved successfully",
  "data": {
    "quality_score": 96.8,
    "completeness_rate": 98.2,
    "accuracy_score": 95.4,
    "validation_metrics": {
      "schema_validation": 99.1,
      "content_validation": 94.7,
      "consistency_check": 97.3
    }
  }
}
```

## Metrics Management

### Get All Metrics

```http
GET /analytics/metrics
```

**Response:**
```json
{
  "success": true,
  "message": "Metrics retrieved successfully",
  "data": [
    {
      "id": "uuid",
      "name": "account_active_count",
      "category": "ACCOUNT",
      "calculation_type": "COUNT",
      "data_source": "account_db",
      "dimensions": ["status", "type"],
      "filters": {},
      "refresh_interval": 3600,
      "is_active": true,
      "created_at": "2025-09-01T00:00:00",
      "updated_at": "2025-09-01T00:00:00"
    }
  ]
}
```

### Create New Metric

```http
POST /analytics/metrics
```

**Request Body:**
```json
{
  "name": "account_active_count",
  "category": "ACCOUNT",
  "calculation_type": "COUNT",
  "data_source": "account_db",
  "dimensions": ["status", "type"],
  "filters": {},
  "refresh_interval": 3600,
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Metric created successfully",
  "data": {
    "id": "uuid",
    "name": "account_active_count",
    "category": "ACCOUNT",
    "calculation_type": "COUNT",
    "data_source": "account_db",
    "dimensions": ["status", "type"],
    "filters": {},
    "refresh_interval": 3600,
    "is_active": true,
    "created_at": "2025-09-01T00:00:00",
    "updated_at": "2025-09-01T00:00:00"
  }
}
```

### Get Metric by ID

```http
GET /analytics/metrics/{metric_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Metric retrieved successfully",
  "data": {
    "id": "uuid",
    "name": "account_active_count",
    "category": "ACCOUNT",
    "calculation_type": "COUNT",
    "data_source": "account_db",
    "dimensions": ["status", "type"],
    "filters": {},
    "refresh_interval": 3600,
    "is_active": true,
    "created_at": "2025-09-01T00:00:00",
    "updated_at": "2025-09-01T00:00:00"
  }
}
```

### Update Metric

```http
PUT /analytics/metrics/{metric_id}
```

**Request Body:**
```json
{
  "name": "updated_metric_name",
  "refresh_interval": 1800,
  "is_active": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Metric {metric_id} updated successfully",
  "data": {
    "id": "uuid",
    "name": "updated_metric_name",
    "category": "ACCOUNT",
    "calculation_type": "COUNT",
    "data_source": "account_db",
    "dimensions": ["status", "type"],
    "filters": {},
    "refresh_interval": 1800,
    "is_active": false,
    "created_at": "2025-09-01T00:00:00",
    "updated_at": "2025-09-02T00:00:00"
  }
}
```

### Delete Metric

```http
DELETE /analytics/metrics/{metric_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Metric {metric_id} deleted successfully",
  "data": null
}
```

## Job Management

### Get All Jobs

```http
GET /analytics/jobs
```

**Response:**
```json
{
  "success": true,
  "message": "Jobs retrieved successfully",
  "data": [
    {
      "id": "uuid",
      "name": "daily_account_stats",
      "job_type": "REALTIME",
      "metric_id": "metric_uuid",
      "schedule": "0 0 * * *",
      "parameters": {},
      "max_retries": 3,
      "is_active": true,
      "status": "PENDING",
      "last_run": null,
      "next_run": "2025-09-02T00:00:00",
      "error_message": null,
      "retry_count": 0,
      "created_at": "2025-09-01T00:00:00",
      "updated_at": "2025-09-01T00:00:00"
    }
  ]
}
```

### Create New Job

```http
POST /analytics/jobs
```

**Request Body:**
```json
{
  "name": "daily_account_stats",
  "job_type": "REALTIME",
  "metric_id": "metric_uuid",
  "schedule": "0 0 * * *",
  "parameters": {},
  "max_retries": 3,
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job created successfully",
  "data": {
    "id": "uuid",
    "name": "daily_account_stats",
    "job_type": "REALTIME",
    "metric_id": "metric_uuid",
    "schedule": "0 0 * * *",
    "parameters": {},
    "max_retries": 3,
    "is_active": true,
    "status": "PENDING",
    "last_run": null,
    "next_run": "2025-09-02T00:00:00",
    "error_message": null,
    "retry_count": 0,
    "created_at": "2025-09-01T00:00:00",
    "updated_at": "2025-09-01T00:00:00"
  }
}
```

### Get Job by ID

```http
GET /analytics/jobs/{job_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Job retrieved successfully",
  "data": {
    "id": "uuid",
    "name": "daily_account_stats",
    "job_type": "REALTIME",
    "metric_id": "metric_uuid",
    "schedule": "0 0 * * *",
    "parameters": {},
    "max_retries": 3,
    "is_active": true,
    "status": "PENDING",
    "last_run": null,
    "next_run": "2025-09-02T00:00:00",
    "error_message": null,
    "retry_count": 0,
    "created_at": "2025-09-01T00:00:00",
    "updated_at": "2025-09-01T00:00:00"
  }
}
```

### Update Job

```http
PUT /analytics/jobs/{job_id}
```

**Request Body:**
```json
{
  "name": "updated_job_name",
  "schedule": "0 12 * * *",
  "is_active": false,
  "status": "COMPLETED"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job {job_id} updated successfully",
  "data": {
    "id": "uuid",
    "name": "updated_job_name",
    "job_type": "REALTIME",
    "metric_id": "metric_uuid",
    "schedule": "0 12 * * *",
    "parameters": {},
    "max_retries": 3,
    "is_active": false,
    "status": "COMPLETED",
    "last_run": "2025-09-01T12:00:00",
    "next_run": null,
    "error_message": null,
    "retry_count": 0,
    "created_at": "2025-09-01T00:00:00",
    "updated_at": "2025-09-02T00:00:00"
  }
}
```

### Start Job

```http
POST /analytics/jobs/{job_id}/start
```

**Response:**
```json
{
  "success": true,
  "message": "Job {job_id} started successfully",
  "data": null
}
```

### Stop Job

```http
POST /analytics/jobs/{job_id}/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Job {job_id} stopped successfully",
  "data": null
}
```

### Delete Job

```http
DELETE /analytics/jobs/{job_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Job {job_id} deleted successfully",
  "data": null
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

## Rate Limiting

- 100 requests per minute per IP address
- 1000 requests per hour per user
- Contact administrator for higher limits

## Data Formats

### Timestamps
All timestamps are in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`

### UUIDs
All resource IDs are UUID v4 strings

### Enumerations
- **Job Status**: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`
- **Job Type**: `REALTIME`, `HISTORICAL`, `AGGREGATION`, `CLEANUP`
- **Metric Category**: `ACCOUNT`, `PROXY`, `TASK`, `RESULT`
- **Calculation Type**: `COUNT`, `SUM`, `AVG`, `MAX`, `MIN`, `CUSTOM`

## Examples

### Curl Examples

**Get account analytics:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/accounts/realtime" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Create new metric:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/metrics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "account_active_count",
    "category": "ACCOUNT",
    "calculation_type": "COUNT",
    "data_source": "account_db",
    "dimensions": ["status", "type"],
    "refresh_interval": 3600,
    "is_active": true
  }'
```

**Get historical proxy data:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/proxies/history?time_range=7d&country=US" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Support

For API support and questions, contact:
- Email: support@xget.com
- Documentation: https://docs.xget.com/api/analytics
- Issue Tracker: https://github.com/xget/analytics-service/issues