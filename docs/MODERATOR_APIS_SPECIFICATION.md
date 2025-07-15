# Moderator Dashboard APIs Specification

This document specifies the required APIs and response formats needed to replace hardcoded/mock data in the Moderator Dashboard system.

## 📋 Overview

The current Moderator Dashboard uses significant amounts of hardcoded data that needs to be replaced with real APIs. This specification covers all required endpoints.

## 🔗 Base URLs

- **Development**: `/api/moderation/`
- **Production**: `https://yourdomain.com/api/moderation/`

## 📊 Dashboard Statistics APIs

### 1. Dashboard Statistics

**GET** `/api/moderation/dashboard/statistics/`

Replaces hardcoded stats in `Dashboard.jsx getDashboardStats()`

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "pending_content": {
      "value": 23,
      "change": "+5",
      "change_type": "increase",
      "description": "Cần xử lý trong ngày"
    },
    "violation_reports": {
      "value": 12,
      "change": "+3",
      "change_type": "increase",
      "description": "Cần ưu tiên xử lý"
    },
    "approved_today": {
      "value": 156,
      "change": "+23",
      "change_type": "increase",
      "description": "Tăng 17% so với hôm qua"
    },
    "avg_processing_time": {
      "value": "2.5h",
      "change": "-0.3h",
      "change_type": "decrease",
      "description": "Cải thiện hiệu suất"
    }
  }
}
```

### 2. Navigation Badge Counts

**GET** `/api/moderation/navigation/badge-counts/`

Replaces hardcoded badges in `Dashboard.jsx getNavigationItems()`

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "overview": {
      "count": 23,
      "color": "yellow",
      "priority": "high"
    },
    "moderation_queue": {
      "count": 15,
      "color": "red",
      "priority": "critical"
    },
    "reports": {
      "count": 8,
      "color": "red",
      "priority": "high"
    },
    "content_review": {
      "count": 12,
      "color": "blue",
      "priority": "medium"
    },
    "content_moderation": {
      "count": 25,
      "color": "red",
      "priority": "high"
    },
    "auto_marked": {
      "count": 18,
      "color": "yellow",
      "priority": "high"
    },
    "user_management": {
      "count": 5,
      "color": "orange",
      "priority": "medium"
    },
    "system_users": {
      "count": 3,
      "color": "purple",
      "priority": "high"
    }
  }
}
```

### 3. Moderation Queue Stats

**GET** `/api/moderation/queue/statistics/`

For view-specific stats in moderation queue section

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "pending": {
      "count": 23,
      "label": "Chờ duyệt"
    },
    "in_progress": {
      "count": 8,
      "label": "Đang xử lý"
    },
    "completed": {
      "count": 156,
      "label": "Hoàn thành"
    },
    "priority_breakdown": {
      "high": 8,
      "medium": 12,
      "low": 15
    }
  }
}
```

## 🏠 Dashboard Overview APIs

### 4. Dashboard Overview

**GET** `/api/moderation/dashboard/overview/`

Replaces all hardcoded data in `DashboardOverview.jsx`

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "stats": [
      {
        "title": "Nội dung chờ duyệt",
        "value": "23",
        "change": "+5",
        "change_type": "increase",
        "color": "yellow"
      },
      {
        "title": "Báo cáo vi phạm",
        "value": "12",
        "change": "+3",
        "change_type": "increase",
        "color": "red"
      },
      {
        "title": "Đã duyệt hôm nay",
        "value": "156",
        "change": "+23",
        "change_type": "increase",
        "color": "green"
      },
      {
        "title": "Thời gian xử lý TB",
        "value": "2.5h",
        "change": "-0.3h",
        "change_type": "decrease",
        "color": "blue"
      }
    ]
  }
}
```

### 5. Recent Moderation Activities

**GET** `/api/moderation/activities/recent/?limit=10`

Replaces hardcoded recentActivities in `DashboardOverview.jsx`

**Response Format:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "content": "Đã duyệt review \"Avengers: Endgame\"",
      "user": "Moderator A",
      "user_id": 123,
      "time": "2 phút trước",
      "timestamp": "2024-01-15T10:30:00Z",
      "action_type": "approve",
      "target_type": "review",
      "target_id": 456
    },
    {
      "id": 2,
      "content": "Từ chối comment vi phạm",
      "user": "Moderator B",
      "user_id": 124,
      "time": "5 phút trước",
      "timestamp": "2024-01-15T10:27:00Z",
      "action_type": "reject",
      "target_type": "comment",
      "target_id": 789
    }
  ]
}
```

### 6. Moderation Performance Metrics

**GET** `/api/moderation/performance/metrics/`

Replaces hardcoded performance metrics in `DashboardOverview.jsx`

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "accuracy_rate": {
      "value": 95,
      "unit": "%",
      "trend": "stable"
    },
    "avg_processing_time": {
      "value": 2.3,
      "unit": "phút",
      "trend": "improving"
    },
    "daily_processed": {
      "value": 156,
      "unit": "nội dung/ngày",
      "trend": "increasing"
    },
    "efficiency_score": {
      "value": 87,
      "unit": "%",
      "trend": "stable"
    }
  }
}
```

## 👥 User Management APIs

### 7. Moderation Users

**GET** `/api/moderation/users/?page=1&page_size=20&status=flagged`

Replaces mock data in `UserManagement.jsx`

**Query Parameters:**

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)
- `status`: Filter by status (`flagged`, `warned`, `suspended`, `banned`, `all`)
- `role`: Filter by role (`user`, `moderator`, `admin`, `all`)
- `search`: Search by username or email

**Response Format:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "user-1",
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "status": "active",
      "moderation_status": "flagged",
      "join_date": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-15T10:30:00Z",
      "violation_count": 2,
      "warning_count": 1,
      "is_banned": false,
      "ban_reason": null,
      "ban_date": null,
      "restrictions": {
        "comment_banned": false,
        "review_banned": false,
        "upload_banned": false
      },
      "recent_violations": [
        {
          "type": "spam_comment",
          "date": "2024-01-14T15:20:00Z",
          "severity": "medium"
        }
      ]
    }
  ],
  "count": 50,
  "total_pages": 3,
  "current_page": 1,
  "has_next": true,
  "has_previous": false
}
```

### 8. User Actions

**POST** `/api/moderation/users/{user_id}/warn/`
**POST** `/api/moderation/users/{user_id}/suspend/`
**POST** `/api/moderation/users/{user_id}/ban/`
**POST** `/api/moderation/users/{user_id}/flag/`
**POST** `/api/moderation/users/{user_id}/remove-restrictions/`

**Request Format (Warn):**

```json
{
  "reason": "Spam comments repeatedly",
  "severity": "medium"
}
```

**Request Format (Suspend):**

```json
{
  "reason": "Harassment",
  "duration_hours": 24
}
```

**Request Format (Ban):**

```json
{
  "reason": "Severe policy violations"
}
```

**Response Format:**

```json
{
  "status": "success",
  "message": "User warned successfully",
  "data": {
    "user_id": "user-1",
    "action": "warn",
    "reason": "Spam comments repeatedly",
    "timestamp": "2024-01-15T10:30:00Z",
    "moderator": "admin_user",
    "expires_at": "2024-01-16T10:30:00Z"
  }
}
```

## ⚙️ System Settings APIs

### 9. System Settings

**GET** `/api/moderation/settings/`
**PUT** `/api/moderation/settings/`

Replaces mock settings in `SystemSettings.jsx`

**Response Format (GET):**

```json
{
  "status": "success",
  "data": {
    "moderation": {
      "auto_approve": false,
      "require_moderation": true,
      "max_reports_before_ban": 5,
      "response_time_limit": 24,
      "enable_auto_moderation": true
    },
    "content": {
      "max_review_length": 1000,
      "allow_anonymous_reviews": false,
      "require_email_verification": true,
      "enable_content_filtering": true
    },
    "system": {
      "maintenance_mode": false,
      "enable_notifications": true,
      "backup_frequency": "daily",
      "log_retention_days": 30
    },
    "security": {
      "enable_two_factor": true,
      "session_timeout": 60,
      "max_login_attempts": 5,
      "enable_rate_limiting": true
    }
  }
}
```

## 🔔 Notifications APIs

### 10. Notifications

**GET** `/api/moderation/notifications/?page=1&limit=20&unread_only=false`

Replaces empty notifications array in `Dashboard.jsx`

**Response Format:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "title": "New violation report",
      "message": "User reported for spam content",
      "type": "violation_report",
      "priority": "high",
      "is_read": false,
      "created_at": "2024-01-15T10:30:00Z",
      "related_object": {
        "type": "review",
        "id": 123,
        "title": "Review of Avengers"
      },
      "action_required": true,
      "action_url": "/moderator/reports/123"
    }
  ],
  "count": 15,
  "unread_count": 8,
  "total_pages": 2
}
```

### 11. Unread Notification Count

**GET** `/api/moderation/notifications/unread-count/`

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "unread_count": 8
  }
}
```

## 📄 Content Management APIs

### 12. Content Items

**GET** `/api/moderation/content/?page=1&page_size=20&type=reviews`

Replaces mock data in `ContentManagement.jsx`

**Query Parameters:**

- `type`: Filter by type (`reviews`, `comments`, `posts`, `media`, `all`)
- `status`: Filter by status (`pending`, `flagged`, `approved`, `rejected`)
- `priority`: Filter by priority (`high`, `medium`, `low`)

**Response Format:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "type": "review",
      "title": "Review: Avengers: Endgame",
      "content": "Một bộ phim tuyệt vời với cốt truyện hoàn hảo...",
      "author": {
        "id": 123,
        "username": "user123",
        "email": "user@example.com"
      },
      "status": "pending",
      "priority": "high",
      "created_at": "2024-01-15T08:30:00Z",
      "reported_at": "2024-01-15T10:30:00Z",
      "report_count": 2,
      "movie": {
        "id": 456,
        "title": "Avengers: Endgame"
      },
      "rating": 5,
      "flags": {
        "potential_spoiler": true,
        "inappropriate_language": false,
        "spam": false
      }
    }
  ],
  "count": 25,
  "total_pages": 3
}
```

## 📊 Real-time Statistics API

### 13. Real-time Stats

**GET** `/api/moderation/realtime/stats/`

For live dashboard updates

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "timestamp": "2024-01-15T10:30:00Z",
    "active_moderators": 5,
    "queue_length": 23,
    "processing_rate": "12/hour",
    "alerts": [
      {
        "type": "high_queue",
        "message": "Queue length exceeds normal threshold",
        "priority": "medium"
      }
    ],
    "system_health": {
      "status": "healthy",
      "uptime": "99.9%",
      "response_time": "150ms"
    }
  }
}
```

## 🔄 Bulk Actions API

### 14. Bulk Actions

**POST** `/api/moderation/bulk-actions/`

Enhanced bulk operations

**Request Format:**

```json
{
  "action": "approve",
  "item_ids": [1, 2, 3, 4, 5],
  "reason": "Bulk approval of clean content",
  "additional_params": {
    "notify_users": true,
    "auto_publish": true
  }
}
```

**Response Format:**

```json
{
  "status": "success",
  "data": {
    "processed": 5,
    "successful": 4,
    "failed": 1,
    "errors": [
      {
        "item_id": 3,
        "error": "Item already processed"
      }
    ],
    "summary": {
      "action": "approve",
      "moderator": "admin_user",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

## 🔍 Error Handling

All APIs should follow consistent error response format:

```json
{
  "status": "error",
  "error": "Validation failed",
  "message": "User-friendly error message",
  "details": {
    "field": ["Specific field error"]
  },
  "code": "VALIDATION_ERROR"
}
```

## 🔐 Authentication & Authorization

- All endpoints require authentication via JWT token
- Admin-only endpoints: user banning, system settings
- Moderator endpoints: content moderation, user warnings
- Role-based access control must be enforced

## 📝 Implementation Priority

1. **High Priority (P0)**: Dashboard statistics, Navigation badges
2. **Medium Priority (P1)**: User management, Content management
3. **Low Priority (P2)**: Real-time stats, Advanced notifications

## 🧪 Testing

- Include comprehensive API tests
- Mock data should match these response formats
- Performance testing for real-time endpoints
- Load testing for bulk operations

---

**Note**: This specification replaces all hardcoded/mock data identified in the Moderator Dashboard codebase. Each API endpoint directly corresponds to specific frontend components that currently use static data.
