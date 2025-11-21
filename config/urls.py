from django.contrib import admin
from django.urls import path, include, re_path 
from api.views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.generic import TemplateView     

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

    # substituir a view padrão pela nossa
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
# Fallback para o React SPA: captura tudo que não for /api ou /admin
urlpatterns += [
    re_path(r"^(?!api/|admin/).*", TemplateView.as_view(template_name="index.html")),
]