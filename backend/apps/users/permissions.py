from rest_framework import permissions
from django.contrib.auth.models import Group


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users in Administrators group.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Administrators').exists()


class IsModerator(permissions.BasePermission):
    """
    Custom permission to only allow users in Moderators group.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Moderators').exists()


class IsModeratorOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow users in Moderators or Administrators groups.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.groups.filter(name='Moderators').exists() or
            request.user.groups.filter(name='Administrators').exists()
        )


class IsOwnerOrModeratorOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners, moderators, and admins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin and moderator can access everything
        if (request.user.groups.filter(name='Administrators').exists() or
            request.user.groups.filter(name='Moderators').exists()):
            return True

        # Check if user is owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False


# Helper functions for role management
def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.groups.filter(name='Administrators').exists()


def is_moderator(user):
    """Check if user is moderator"""
    return user.is_authenticated and user.groups.filter(name='Moderators').exists()


def is_moderator_or_admin(user):
    """Check if user is moderator or admin"""
    return user.is_authenticated and (
        user.groups.filter(name='Moderators').exists() or
        user.groups.filter(name='Administrators').exists()
    )


def assign_user_role(user, role):
    """
    Assign user to a role group
    """
    if role == 'admin':
        admin_group = Group.objects.get(name='Administrators')
        user.groups.add(admin_group)
        user.is_staff = True
        user.save()
    elif role == 'moderator':
        moderator_group = Group.objects.get(name='Moderators')
        user.groups.add(moderator_group)
        user.save()
    else:
        raise ValueError(f"Invalid role: {role}")


def remove_user_role(user, role):
    """
    Remove user from a role group
    """
    if role == 'admin':
        admin_group = Group.objects.get(name='Administrators')
        user.groups.remove(admin_group)
        user.is_staff = False
        user.save()
    elif role == 'moderator':
        moderator_group = Group.objects.get(name='Moderators')
        user.groups.remove(moderator_group)
        user.save()
    else:
        raise ValueError(f"Invalid role: {role}")


def get_user_roles(user):
    """
    Get all roles for a user
    """
    roles = []
    if user.groups.filter(name='Administrators').exists():
        roles.append('admin')
    if user.groups.filter(name='Moderators').exists():
        roles.append('moderator')
    return roles
