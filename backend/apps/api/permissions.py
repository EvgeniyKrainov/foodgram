from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет только автору объекта редактировать его.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешаем чтение для всех (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешаем запись только автору
        return obj.author == request.user
