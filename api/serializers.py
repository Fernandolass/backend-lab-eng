from rest_framework import serializers
from .models import Usuario, Projeto, Ambiente, Log, ModeloDocumento, MaterialSpec, TipoAmbiente, Marca, DescricaoMarca
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'  # força login por email

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Email ou senha incorretos")

        data = super().validate(attrs)
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'cargo']


class TipoAmbienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAmbiente
        fields = ['id', 'nome', 'created_at']


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nome', 'created_at']


class DescricaoMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescricaoMarca
        fields = ['id', 'material', 'marcas', 'projeto']


class MaterialSpecSerializer(serializers.ModelSerializer):
    aprovador_email = serializers.EmailField(source='aprovador.email', read_only=True)
    item_label = serializers.CharField(source='get_item_display', read_only=True)
    marca_nome = serializers.CharField(source='marca.nome', read_only=True)
    ambiente_nome = serializers.CharField(source='ambiente.nome_do_ambiente', read_only=True)
    ambiente_categoria = serializers.CharField(source='ambiente.categoria', read_only=True)

    class Meta:
        model = MaterialSpec
        fields = ['id', 'ambiente', 'item', 'item_label', 'descricao',
                  'marca', 'marca_nome', 'ambiente_nome', 'ambiente_categoria',
                  'status', 'motivo', 'aprovador', 'aprovador_email',
                  'data_aprovacao', 'updated_at']
        read_only_fields = ['aprovador', 'aprovador_email', 'data_aprovacao', 'updated_at']


class AmbienteSerializer(serializers.ModelSerializer):
    materials = serializers.SerializerMethodField()

    class Meta:
        model = Ambiente
        fields = '__all__'

    def get_materials(self, obj):
        projeto = self.context.get("projeto")
        if not projeto:
            return []
        qs = MaterialSpec.objects.filter(projeto_id=projeto, ambiente=obj) \
                                 .select_related("marca", "aprovador", "ambiente") \
                                 .order_by("ambiente_id", "item")
        return MaterialSpecSerializer(qs, many=True).data


# Serializer enxuto para lista de projetos (list view)
class ProjetoListSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)

    class Meta:
        model = Projeto
        fields = [
            'id',
            'nome_do_projeto',
            'tipo_do_projeto',
            'status',
            'responsavel_nome',
            'data_criacao',
            'data_atualizacao',
        ]


class ProjetoSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    ambientes = serializers.SerializerMethodField()
    ambientes_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Ambiente.objects.all(), write_only=True, source="ambientes"
    )
    descricao_marcas = DescricaoMarcaSerializer(many=True, read_only=True, source="descricaomarca_set")

    class Meta:
        model = Projeto
        fields = [
            'id', 'nome_do_projeto', 'tipo_do_projeto', 'data_entrega', 'descricao',
            'status', 'responsavel', 'responsavel_nome', 'data_criacao',
            'data_atualizacao', 'ambientes', 'ambientes_ids', 'descricao_marcas',
        ]

    def get_ambientes(self, instance):
        # usa dados já "prefetched"
        materiais_by_amb = {}
        for m in instance.materiais.all():
            materiais_by_amb.setdefault(m.ambiente_id, []).append(m)

        data = []
        for amb in instance.ambientes.all():
            amb_data = AmbienteSerializer(amb).data
            amb_data['materials'] = MaterialSpecSerializer(
                materiais_by_amb.get(amb.id, []), many=True
            ).data
            data.append(amb_data)
        return data

    def validate_nome_do_projeto(self, value):
        if Projeto.objects.filter(nome_do_projeto=value).exists():
            raise serializers.ValidationError("Já existe um projeto com esse nome.")
        return value

    def create(self, validated_data):
        validated_data["responsavel"] = self.context["request"].user
        return super().create(validated_data)


class LogSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    projeto_nome = serializers.CharField(source='projeto.nome_do_projeto', read_only=True)

    class Meta:
        model = Log
        fields = ['id', 'usuario_email', 'acao', 'projeto_nome', 'motivo', 'data_hora']


class ModeloDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloDocumento
        fields = '__all__'


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['cargo'] = user.cargo
        token['full_name'] = user.get_full_name()
        return token