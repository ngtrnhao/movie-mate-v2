from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.management import call_command
from django.conf import settings
import os

# Create your views here.

class RunMigrationsView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # Check for secret key in headers
        secret_key = request.headers.get('X-Migration-Secret')
        if not secret_key or secret_key != settings.MIGRATION_SECRET_KEY:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Run migrations
            call_command('run_migrations')
            return Response(
                {"message": "Migrations completed successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
