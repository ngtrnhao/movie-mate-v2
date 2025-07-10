# User Limits Implementation Guide

## Overview

This document describes the implementation of user limits for the Movie Recommendation System. The system enforces limits on various features based on user subscription tiers.

## Features with Limits

### 1. Favorites (Save Favorites)

- **Member**: 100 movies
- **Premium Basic**: 500 movies
- **Premium Standard**: 2000 movies
- **Premium VIP**: Unlimited

### 2. Watchlists (Create Personal Lists)

- **Member**: 3 lists
- **Premium Basic**: 10 lists
- **Premium Standard**: 50 lists
- **Premium VIP**: Unlimited

### 3. Reviews (Rate & Review Movies)

- **Member**: 20 reviews per day
- **Premium Basic**: 100 reviews per day
- **Premium Standard**: 200 reviews per day
- **Premium VIP**: Unlimited

### 4. Moods (Mood-based Preferences)

- **Member**: 5 moods
- **Premium Basic**: 15 moods
- **Premium Standard**: 30 moods
- **Premium VIP**: Unlimited

## Backend Implementation

### 1. User Limits Service (`backend/apps/users/services/user_limits_service.py`)

The service provides methods to validate user limits:

```python
from apps.users.services.user_limits_service import UserLimitsService

# Validate favorites limit
can_add, limit_info = UserLimitsService.validate_favorites_limit(user)

# Validate lists limit
can_create, limit_info = UserLimitsService.validate_lists_limit(user)

# Validate reviews limit
can_review, limit_info = UserLimitsService.validate_reviews_limit(user)

# Get comprehensive usage stats
usage_stats = UserLimitsService.get_user_usage_stats(user)
```

### 2. Serializer Validation

All relevant serializers include limit validation:

- `UserFavoriteMovieSerializer`: Validates favorites limit
- `UserWatchlistSerializer`: Validates lists limit
- `MovieReviewSerializer`: Validates reviews per day limit

### 3. API Endpoints

- `GET /api/auth/usage-stats/`: Get current usage statistics
- All create endpoints include limit validation

## Frontend Implementation

### 1. User Limits Hook (`frontend/src/hooks/useUserLimits.js`)

```javascript
import { useUserLimits } from "../hooks/useUserLimits";

const { usageStats, canPerformAction, getUpgradeMessage, shouldShowUpgrade } =
  useUserLimits();

// Check if user can add favorites
const canAddFavorite = canPerformAction("add_favorite");

// Get upgrade message
const message = getUpgradeMessage("favorites");

// Check if should show upgrade prompt
const showUpgrade = shouldShowUpgrade("add_favorite");
```

### 2. Components

#### UserLimitsDisplay

Shows current usage and limits:

```jsx
import UserLimitsDisplay from '../components/common/UserLimitsDisplay';

// Compact view
<UserLimitsDisplay />

// Detailed view with progress bars
<UserLimitsDisplay showDetails={true} />
```

#### UpgradePrompt

Shows upgrade prompts when limits are reached:

```jsx
import UpgradePrompt from '../components/common/UpgradePrompt';

// Inline prompt
<UpgradePrompt feature="add_favorite" />

// Banner prompt
<UpgradePrompt feature="create_list" variant="banner" />

// Modal prompt
<UpgradePrompt feature="write_review" variant="modal" />
```

### 3. Integration Examples

#### Favorite Button with Limits

```jsx
const FavoriteButton = ({ movie }) => {
  const { canPerformAction, getUpgradeMessage } = useUserLimits();

  const handleToggle = async () => {
    if (!canPerformAction("add_favorite")) {
      toast.error(getUpgradeMessage("favorites"));
      return;
    }
    // ... toggle logic
  };
};
```

#### Watchlist Creation with Limits

```jsx
const CreateWatchlistModal = () => {
  const { canPerformAction, getUpgradeMessage } = useUserLimits();

  const handleCreate = async (name) => {
    if (!canPerformAction("create_list")) {
      toast.error(getUpgradeMessage("lists"));
      return;
    }
    // ... creation logic
  };
};
```

## Error Handling

### Backend Errors

When limits are exceeded, the API returns:

```json
{
  "limit_exceeded": "You have reached your limit of 100 favorite movies. Please upgrade your plan to add more favorites.",
  "current": 100,
  "max": 100
}
```

### Frontend Error Handling

```javascript
try {
  const result = await addToFavorites(movieId);
  if (!result.success && result.error?.limit_exceeded) {
    toast.error(result.error.limit_exceeded);
  }
} catch (error) {
  // Handle other errors
}
```

## Usage Statistics

The system tracks real-time usage:

```javascript
const usageStats = {
  favorites: {
    current: 85,
    max: 100,
    remaining: 15,
    is_unlimited: false,
  },
  lists: {
    current: 2,
    max: 3,
    remaining: 1,
    is_unlimited: false,
  },
  reviews_today: {
    current: 15,
    max: 20,
    remaining: 5,
    is_unlimited: false,
  },
  moods: {
    current: 3,
    max: 5,
    remaining: 2,
    is_unlimited: false,
  },
};
```

## Testing

### Backend Tests

```python
def test_favorites_limit():
    user = create_user(user_type='member')

    # Add 100 favorites (should work)
    for i in range(100):
        add_favorite(user, movie)

    # Try to add 101st (should fail)
    with pytest.raises(ValidationError):
        add_favorite(user, movie)
```

### Frontend Tests

```javascript
test("shows upgrade prompt when limit reached", () => {
  const { getByText } = render(<FavoriteButton movie={movie} />);

  // Mock usage stats to show limit reached
  mockUsageStats({ favorites: { current: 100, max: 100 } });

  fireEvent.click(getByText("Favorite"));
  expect(getByText(/upgrade/i)).toBeInTheDocument();
});
```

## Configuration

### Updating Limits

Edit `frontend/src/utils/userPermissions.js`:

```javascript
export const USER_LIMITS = {
  [USER_TYPES.MEMBER]: {
    favorites: 100, // Change this value
    lists: 3,
    reviews_per_day: 20,
    moods: 5,
  },
  // ... other tiers
};
```

### Backend Limits

Edit `backend/apps/users/services/user_limits_service.py`:

```python
USER_LIMITS = {
    'member': {
        'favorites': 100,  # Change this value
        'lists': 3,
        'reviews_per_day': 20,
        'moods': 5,
    },
    # ... other tiers
}
```

## Monitoring

### Usage Analytics

Track limit usage patterns:

- Most common limit reached
- User upgrade conversion rates
- Feature usage by tier

### Performance

Monitor API response times for limit validation:

- Database query optimization
- Caching strategies
- Rate limiting considerations

## Future Enhancements

1. **Dynamic Limits**: Adjust limits based on user behavior
2. **Grace Periods**: Allow temporary overages
3. **Limit Notifications**: Proactive warnings before limits
4. **Usage Analytics**: Detailed usage reports
5. **Limit History**: Track limit changes over time
