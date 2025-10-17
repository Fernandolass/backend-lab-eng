from rest_framework.permissions import BasePermission, SAFE_METHODS

def role(user):
    return (getattr(user, "cargo", "") or "").lower()

class IsAuthenticatedReadOnly(BasePermission):
    """Leitura para autenticados; nenhuma escrita."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.method in SAFE_METHODS

class AllowCreateForBasicButNoEdit(BasePermission):
    """
    - Atendente: pode CREATE; não pode UPDATE/DELETE
    - Gerente/Superadmin: podem tudo (o ViewSet ainda pode restringir delete)
    - Leitura: qualquer autenticado
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        r = role(request.user)
        if request.method in SAFE_METHODS:
            return True
        if request.method == "POST":
            return role(request.user) in {"atendente", "gerente", "superadmin", "admin"}
        return role(request.user) in {"gerente", "superadmin", "admin"}

class AllowWriteForManagerUp(BasePermission):
    """Somente gerente/superadmin podem escrever; leitura liberada a autenticados."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return role(request.user) in {"gerente", "superadmin", "admin"}

class OnlySuperadminDelete(BasePermission):
    """Para usar especificamente na ação destroy (delete)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and role(request.user) == "superadmin"