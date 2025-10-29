from django.db import models  # para Q nas consultas
from rest_framework import viewsets, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models.functions import TruncMonth  
from django.db.models import Count 

from .models import Usuario, Projeto, Ambiente, Log, ModeloDocumento, MaterialSpec, TipoAmbiente, Marca, DescricaoMarca
from .serializers import (
    UsuarioSerializer, ProjetoSerializer, AmbienteSerializer,
    LogSerializer, ModeloDocumentoSerializer, MyTokenObtainPairSerializer,
    MaterialSpecSerializer, TipoAmbienteSerializer, MarcaSerializer, DescricaoMarcaSerializer
)
from .permissions import (
    AllowCreateForBasicButNoEdit, AllowWriteForManagerUp, OnlySuperadminDelete
)

# ---------------- USUÁRIOS (somente leitura) ----------------
class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]  # apenas logados


# --- CRIAR USUÁRIOS (apenas superadmin) ---
class UsuarioAdminViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by("id")
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        # leitura: gerente+ pode ver
        if self.action in ['list', 'retrieve']:
            return [AllowWriteForManagerUp()]
        # criar/editar/deletar: apenas superadmin
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [OnlySuperadminDelete()]
        return [permissions.IsAuthenticated()]


# ---------------- PROJETOS ----------------
class ProjetoViewSet(viewsets.ModelViewSet):
    queryset = Projeto.objects.all().order_by('-data_criacao')
    serializer_class = ProjetoSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        if self.action == "create":
            # atendente pode criar; gerente/superadmin também
            return [AllowCreateForBasicButNoEdit()]
        if self.action in ["update", "partial_update"]:
            # editar/aprovar/reprovar via PATCH: apenas gerente+ 
            return [AllowWriteForManagerUp()]
        if self.action in ["aprovar", "reprovar"]:
            # actions custom: apenas gerente/superadmin
            return [AllowWriteForManagerUp()]
        if self.action == "destroy":
            # deletar: só superadmin
            return [OnlySuperadminDelete()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Projeto.objects.all().order_by('-data_criacao')
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status__iexact=status_param)

        u = self.request.user
        if not u.is_authenticated:
            return qs.none()

        cargo = (getattr(u, "cargo", "") or "").lower()
        if cargo == "cliente":
            cargo = "atendente"

        # gerente e superadmin veem tudo; atendente também só leitura 
        return qs
    def perform_create(self, serializer):
        projeto = serializer.save(responsavel=self.request.user)
        Log.objects.create(usuario=self.request.user, acao="CRIACAO", projeto=projeto)

        from .models import MaterialSpec, Ambiente

        print(f"🚀 Criando materiais para o projeto: {projeto.nome_do_projeto}")

        # 🔹 para cada ambiente selecionado no projeto
        for ambiente in projeto.ambientes.all():
            print(f"   → Ambiente vinculado: {ambiente.nome_do_ambiente}")

            # 🔍 Busca o ambiente base global (sem projeto)
            ambiente_base = (
                Ambiente.objects.filter(nome_do_ambiente=ambiente.nome_do_ambiente, projetos=None)
                .order_by("id")
                .first()
            )

            if not ambiente_base:
                print(f"⚠️ Nenhum ambiente base encontrado para {ambiente.nome_do_ambiente}")
                continue

            # 🔹 Busca materiais base do ambiente global
            materiais_base = MaterialSpec.objects.filter(projeto__isnull=True, ambiente=ambiente_base)

            # 🔹 Cria materiais no projeto atual (sem duplicar)
            for base in materiais_base:
                MaterialSpec.objects.get_or_create(
                    projeto=projeto,
                    ambiente=ambiente,
                    item=base.item,
                    defaults={
                        "descricao": base.descricao or "",
                        "status": "PENDENTE",
                    },
                )

        print(f"✅ Materiais replicados com sucesso para {projeto.nome_do_projeto}")
    @action(detail=True, methods=["post"], permission_classes=[AllowWriteForManagerUp])
    def aprovar(self, request, pk=None):
        projeto = self.get_object()
        projeto.status = "APROVADO"
        projeto.save(update_fields=["status", "data_atualizacao"])
        Log.objects.create(usuario=request.user, acao="APROVACAO", projeto=projeto)
        return Response({"status": projeto.status}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[AllowWriteForManagerUp])
    def reprovar(self, request, pk=None):
        projeto = self.get_object()
        projeto.status = "REPROVADO"
        projeto.save(update_fields=["status", "data_atualizacao"])
        Log.objects.create(usuario=request.user, acao="REPROVACAO", projeto=projeto)
        return Response({"status": projeto.status}, status=status.HTTP_200_OK)
    
# --- TIPO DE AMBIENTE ---
class TipoAmbienteViewSet(viewsets.ModelViewSet):
    queryset = TipoAmbiente.objects.all().order_by("nome")
    serializer_class = TipoAmbienteSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        # criar/editar/deletar: gerente+
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AllowWriteForManagerUp()]
        return [permissions.IsAuthenticated()]

class DescricaoMarcaViewSet(viewsets.ModelViewSet):
    queryset = DescricaoMarca.objects.all()
    serializer_class = DescricaoMarcaSerializer

    def get_queryset(self):
        queryset = MaterialSpec.objects.select_related(
            "ambiente", "aprovador", "marca", "projeto"
        ).order_by("ambiente_id", "item")

        projeto_id = self.request.query_params.get("projeto")
        ambiente_id = self.request.query_params.get("ambiente")

        # 🔹 Se vier ambos, filtra pelos dois
        if projeto_id and ambiente_id:
            queryset = queryset.filter(projeto_id=projeto_id, ambiente_id=ambiente_id)
        elif projeto_id:
            queryset = queryset.filter(projeto_id=projeto_id)
        elif ambiente_id:
            queryset = queryset.filter(ambiente_id=ambiente_id)

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AllowWriteForManagerUp()]
        return [permissions.IsAuthenticated()]

# ---------------- AMBIENTES ----------------
class AmbienteViewSet(viewsets.ModelViewSet):
    queryset = Ambiente.objects.all()
    serializer_class = AmbienteSerializer

    def get_queryset(self):
        queryset = Ambiente.objects.all().order_by("nome_do_ambiente")
        apenas_disponiveis = self.request.query_params.get("disponiveis")
        if apenas_disponiveis:
            return queryset
        return queryset.order_by("nome_do_ambiente")
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]  # todos logados leem
        if self.action == "create":
            # se quiser que atendente NÃO crie ambientes, troque por AllowWriteForManagerUp()
            return [AllowCreateForBasicButNoEdit()]
        if self.action in ["update", "partial_update"]:
            return [AllowWriteForManagerUp()]
        if self.action == "destroy":
            return [OnlySuperadminDelete()]
        return [permissions.IsAuthenticated()]

# ---------------- LOGS (somente leitura) ----------------
class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all().order_by('-data_hora')
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        if not u.is_authenticated:
            return Log.objects.none()

        r = (getattr(u, "cargo", "") or "").lower()
        if r == "cliente":
            r = "atendente"

        if r == "superadmin":
            # superadmin vê tudo
            return Log.objects.all().order_by('-data_hora')

        if r == "gerente":
            # gerente vê logs dos ATENDENTES + as próprias
            atendentes_ids = Usuario.objects.filter(
                cargo__in=["atendente", "cliente"]
            ).values_list("id", flat=True)
            return Log.objects.filter(
                models.Q(usuario__in=atendentes_ids) | models.Q(usuario=u)
            ).order_by('-data_hora')

        # atendente: só as próprias
        return Log.objects.filter(usuario=u).order_by('-data_hora')

# ---------------- MODELOS DE DOCUMENTO ----------------
class ModeloDocumentoViewSet(viewsets.ModelViewSet):
    queryset = ModeloDocumento.objects.all()
    serializer_class = ModeloDocumentoSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]  # todos logados leem
        if self.action in ["create", "update", "partial_update"]:
            # gerente e superadmin podem criar/editar
            return [AllowWriteForManagerUp()]
        if self.action == "destroy":
            # deletar somente superadmin
            return [OnlySuperadminDelete()]
        return [permissions.IsAuthenticated()]

# ---------------- STATS DO DASHBOARD ----------------
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    total_projetos = Projeto.objects.count()
    aprovados = Projeto.objects.filter(status='APROVADO').count()
    reprovados = Projeto.objects.filter(status='REPROVADO').count()
    pendentes = Projeto.objects.filter(status='PENDENTE').count()

    data = {
        'total_projetos': total_projetos,
        'projetos_aprovados': aprovados,
        'projetos_reprovados': reprovados,
        'projetos_pendentes': pendentes,
    }
    return Response(data)

class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all().order_by("nome")
    serializer_class = MarcaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AllowWriteForManagerUp()]
        return [permissions.IsAuthenticated()]
    
class MaterialSpecViewSet(viewsets.ModelViewSet):
    serializer_class = MaterialSpecSerializer

    def get_queryset(self):
        from django.db.models import Q

        queryset = MaterialSpec.objects.select_related(
            "ambiente", "aprovador", "marca", "projeto"
        ).order_by("ambiente_id", "item")

        projeto_id = self.request.query_params.get("projeto")
        ambiente_id = self.request.query_params.get("ambiente")

        # ✅ Novo filtro robusto — cobre tanto MaterialSpec com projeto_id
        # quanto os que só estão ligados via ambiente__projetos
        if projeto_id and ambiente_id:
            queryset = queryset.filter(
                Q(ambiente_id=ambiente_id) &
                (
                    Q(projeto_id=projeto_id)
                    | Q(ambiente__projetos__id=projeto_id)
                    | Q(projeto__isnull=True)  # ✅ inclui materiais base
                )
            ).distinct()
        elif projeto_id:
            queryset = queryset.filter(
                Q(projeto_id=projeto_id)
                | Q(ambiente__projetos__id=projeto_id)
                | Q(projeto__isnull=True)  # ✅ também inclui base se ambiente não vier
            ).distinct()
        elif ambiente_id:
            queryset = queryset.filter(ambiente_id=ambiente_id)

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AllowWriteForManagerUp()]
        if self.action in ['aprovar', 'reprovar', 'reverter']:
            return [AllowWriteForManagerUp()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.status == 'APROVADO':
            raise PermissionDenied('Item aprovado não pode ser editado. Use reverter.')
        serializer.save()

    #  Aprovar material individual
    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        m = self.get_object()
        m.status = 'APROVADO'
        m.aprovador = request.user
        m.data_aprovacao = timezone.now()
        m.motivo = ''
        m.save(update_fields=['status', 'aprovador', 'data_aprovacao', 'motivo', 'updated_at'])

        # cria log
        projeto = m.ambiente.projetos.first()

        Log.objects.create(
            usuario=request.user,
            acao='APROVACAO',
            projeto=projeto,
            motivo=f'Item {m.get_item_display()} aprovado'
        )

        return Response({'status': m.status}, status=status.HTTP_200_OK)

    # Reprovar material individual
    @action(detail=True, methods=['post'])
    def reprovar(self, request, pk=None):
        m = self.get_object()
        motivo = request.data.get('motivo', '')

        m.status = 'REPROVADO'
        m.aprovador = request.user
        m.data_aprovacao = timezone.now()
        m.motivo = motivo
        m.save(update_fields=['status', 'aprovador', 'data_aprovacao', 'motivo', 'updated_at'])

        Log.objects.create(
            usuario=request.user,
            acao='REPROVACAO',
            projeto=m.projeto,  # AGORA VEM DIRETO DO MATERIAL
            motivo=f'Item {m.get_item_display()} reprovado: {motivo}'
        )

        return Response({'status': m.status}, status=status.HTTP_200_OK)

    # Reverter para pendente
    @action(detail=True, methods=['post'])
    def reverter(self, request, pk=None):
        projeto = self.get_object()
        projeto.status = "PENDENTE"
        projeto.save(update_fields=["status", "data_atualizacao"])

        # reverte todos os materiais do projeto
        from .models import MaterialSpec
        MaterialSpec.objects.filter(ambiente__projetos=projeto).update(
            status="PENDENTE",
            aprovador=None,
            data_aprovacao=None,
            motivo=""
        )

        Log.objects.create(
            usuario=request.user,
            acao="EDICAO",
            projeto=projeto,
            motivo="Projeto revertido para pendente com todos os itens."
        )

        return Response({"status": projeto.status}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def stats_mensais(request):
    qs = Projeto.objects.annotate(mes=TruncMonth('data_criacao')) \
                        .values('mes', 'status') \
                        .annotate(qtd=Count('id')) \
                        .order_by('mes')
    data = {}
    for r in qs:
        key = r['mes'].strftime('%Y-%m')
        data.setdefault(key, {'APROVADO': 0, 'REPROVADO': 0, 'PENDENTE': 0})
        data[key][r['status']] = r['qtd']
    return Response(data)
# ---------------- JWT ----------------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer