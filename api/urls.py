from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuarios')
router.register(r'usuarios-admin', views.UsuarioAdminViewSet, basename='usuarios-admin')
router.register(r'projetos', views.ProjetoViewSet, basename='projetos')
router.register(r'ambientes', views.AmbienteViewSet, basename='ambientes')
router.register(r'logs', views.LogViewSet, basename='logs')
router.register(r'modelos-documento', views.ModeloDocumentoViewSet, basename='modelos-documento')
router.register(r'materiais', views.MaterialSpecViewSet, basename='materiais')
router.register(r'tipos-ambiente', views.TipoAmbienteViewSet, basename='tipos-ambiente')
router.register(r'marcas', views.MarcaViewSet, basename='marcas')
router.register(r'marcas-descricao', views.DescricaoMarcaViewSet, basename='marcas-descricao')

# grupo de rotas /stats/
stats_patterns = [
    path('dashboard/', views.dashboard_stats, name='dashboard-stats'),
    path('mensais/', views.stats_mensais, name='stats-mensais'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', include(stats_patterns)),  # agrupamento limpo
    path("api/token/", TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name="token_obtain_pair"),
]