from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count, Prefetch
from django.core.mail import send_mail
from django.conf import settings

from django.shortcuts import get_object_or_404

from .models import Usuario, Projeto, Ambiente, Log, ModeloDocumento, MaterialSpec, TipoAmbiente, Marca, DescricaoMarca
from .serializers import (
    UsuarioSerializer, ProjetoSerializer, ProjetoListSerializer, AmbienteSerializer,
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

    @action(detail=True, methods=['post'], url_path='resetar-senha')
    def resetar_senha(self, request, pk=None):
        usuario = self.get_object()
        nova_senha = Usuario.objects.make_random_password()
        usuario.set_password(nova_senha)
        usuario.save()

        # envia o e-mail automaticamente usando a função do signals
        notificar_redefinicao_senha(usuario, nova_senha)

        return Response(    
            {"detail": f"Senha redefinida e enviada para {usuario.email}."},
            status=200
        )

# ---------------- PROJETOS ----------------
class ProjetoViewSet(viewsets.ModelViewSet):
    serializer_class = ProjetoSerializer

    def get_serializer_class(self):
        # quando for listagem, usa o serializer mais leve
        if self.action == "list":
            return ProjetoListSerializer
        return ProjetoSerializer

    def get_queryset(self):
        qs = (Projeto.objects
              .all()
              .select_related("responsavel")  # evita query extra para usuário
              .prefetch_related(
                  "ambientes",
                  Prefetch(
                      "materiais",
                      queryset=(MaterialSpec.objects
                                .select_related("ambiente", "marca", "aprovador")
                                .order_by("ambiente_id", "item"))
                  )
              )
              .order_by("-data_criacao"))

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status__iexact=status_param)

        return qs

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        if self.action == "create":
            return [AllowCreateForBasicButNoEdit()]
        if self.action in ["update", "partial_update"]:
            return [AllowWriteForManagerUp()]
        if self.action in ["aprovar", "reprovar"]:
            return [AllowWriteForManagerUp()]
        if self.action == "destroy":
            return [OnlySuperadminDelete()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        projeto = serializer.save(responsavel=self.request.user)
        Log.objects.create(usuario=self.request.user, acao="CRIACAO", projeto=projeto)

        # copiar materiais globais para cada ambiente do projeto
        for ambiente in projeto.ambientes.all():
            materiais_base = MaterialSpec.objects.filter(
                projeto__isnull=True,
                ambiente=ambiente
            )
            for base in materiais_base:
                MaterialSpec.objects.get_or_create(
                    projeto=projeto,
                    ambiente=ambiente,
                    item=base.item,
                    defaults={
                        'descricao': base.descricao,
                        'status': 'PENDENTE',
                        'marca': None
                    }
                )

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
        qs = super().get_queryset()
        material = self.request.query_params.get("material")
        if material:
            qs = qs.filter(material__iexact=material)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'salvar']:
            return [AllowWriteForManagerUp()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["post"], url_path="salvar")
    def salvar(self, request):
        """
        POST /api/marcas-descricao/salvar/
        body:
        {
          "material": "piso",
          "marcas": ["Portobello", "Pisolar"]
        }

        Regras:
        - se material existir: mescla marcas novas (sem duplicar, case-insensitive)
        - se não existir: cria com as marcas enviadas
        """
        from .serializers import DescricaoMarcaSalvarSerializer, DescricaoMarcaSerializer

        s = DescricaoMarcaSalvarSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = s.save()

        return Response(DescricaoMarcaSerializer(obj).data, status=status.HTTP_201_CREATED)


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
    queryset = ModeloDocumento.objects.all().order_by("-id")
    serializer_class = ModeloDocumentoSerializer
    # opcional: aplique a mesma permissão que você usa para alterar/criar
    # permission_classes = [AllowWriteForManagerUp]

    def get_queryset(self):
        qs = super().get_queryset()
        projeto_id = self.request.query_params.get("projeto")
        if projeto_id:
            qs = qs.filter(projeto_id=projeto_id)
        return qs

    @action(detail=False, methods=["post"], url_path="definir")
    def definir_modelo(self, request):
        """
        Recebe {"projeto_id": 123, "nome": "opc.", "descricao": "opc."}
        - exige que o projeto esteja APROVADO
        - cria (ou atualiza) um ModeloDocumento vinculado ao projeto
        """
        projeto_id = request.data.get("projeto_id")
        nome = request.data.get("nome")
        descricao = request.data.get("descricao", "")

        if not projeto_id:
            return Response({"detail": "projeto_id é obrigatório."}, status=400)

        projeto = get_object_or_404(Projeto, pk=projeto_id)

        # só permite para projeto APROVADO
        if projeto.status != "APROVADO":
            return Response({"detail": "Projeto precisa estar APROVADO."}, status=400)

        # nome padrão = nome do projeto
        if not nome:
            nome = projeto.nome_do_projeto

        # Se quiser 1 modelo por projeto, use get_or_create / update_or_create:
        # obj, created = ModeloDocumento.objects.update_or_create(
        #     projeto=projeto, defaults={"nome": nome, "descricao": descricao}
        # )

        # Se pode ter vários modelos por projeto, apenas crie:
        obj = ModeloDocumento.objects.create(
            projeto=projeto,
            nome=nome,
            descricao=descricao
        )

        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED)


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

        # Novo filtro cobre tanto MaterialSpec com projeto_id
        # quanto os que só estão ligados via ambiente__projetos
        if projeto_id and ambiente_id:
            queryset = queryset.filter(
                projeto_id=projeto_id,
                ambiente_id=ambiente_id
            )
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
            motivo=f'Item {m.item} aprovado'
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
            motivo=f'Item {m.item} reprovado: {motivo}'
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

@api_view(['POST'])
@permission_classes([AllowWriteForManagerUp])  # somente gerente+ cria
def add_material_item(request, projeto_id=None, ambiente_id=None):
    """
    POST /api/projetos/<projeto_id>/ambientes/<ambiente_id>/add-item/
    Body:
    {
       "item": "Piso",
       "descricao": "Porcelanato 60x60",
       "marca": 3
    }
    """
    from .models import Projeto, Ambiente, MaterialSpec, Marca

    projeto = get_object_or_404(Projeto, pk=projeto_id)
    ambiente = get_object_or_404(Ambiente, pk=ambiente_id)

    item = request.data.get("item")
    descricao = request.data.get("descricao", "")
    marca_id = request.data.get("marca")

    if not item:
        return Response({"detail": "Campo 'item' é obrigatório."}, status=400)

    marca_obj = None
    if marca_id:
        marca_obj = Marca.objects.filter(id=marca_id).first()

    material = MaterialSpec.objects.create(
        projeto=projeto,
        ambiente=ambiente,
        item=item,
        descricao=descricao,
        marca=marca_obj,
        status="PENDENTE"
    )

    return Response(
        {
            "id": material.id,
            "detail": "Item criado com sucesso.",
            "status": material.status
        },
        status=201
    )


@api_view(['POST'])
@permission_classes([AllowWriteForManagerUp])
def add_material_simple(request):
    """
    POST /api/materials/add/
    {
       "projeto": 1,
       "ambiente": 10,
       "item": "Algo",
       "descricao": "",
       "marca": null
    }
    """
    projeto_id = request.data.get("projeto")
    ambiente_id = request.data.get("ambiente")

    if not projeto_id or not ambiente_id:
        return Response({"detail": "projeto e ambiente são obrigatórios."}, status=400)

    return add_material_item(request, projeto_id, ambiente_id)

# ---------------- JWT ----------------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer