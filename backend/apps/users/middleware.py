import logging
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Middleware to handle JWT authentication errors"""

    def process_request(self, request):
        # Log authentication attempts for debugging
        if request.path.startswith('/api/auth/') and request.method != 'OPTIONS':
            logger.info(f"Auth request: {request.method} {request.path}")
        return None

    def process_exception(self, request, exception):
        # Handle JWT token errors
        if isinstance(exception, (InvalidToken, TokenError)):
            logger.warning(f"JWT token error: {str(exception)}")
            return None
        return None
