from rest_framework import serializers
from .models import Usuario, Projeto, Ambiente, Log, ModeloDocumento, MaterialSpec, TipoAmbiente, Marca, DescricaoMarca
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import unicodedata


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
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'cargo', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password('123456')
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


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
        fields = ["id", "material", "marcas"]


class DescricaoMarcaSalvarSerializer(serializers.Serializer):
    material = serializers.CharField()
    marcas = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )

    def _normalize_list(self, nomes):
        
        vistos_lower = set()
        result = []
        for n in (n.strip() for n in nomes if n and str(n).strip()):
            lower = n.lower()
            if lower not in vistos_lower:
                vistos_lower.add(lower)
                result.append(n)
        return result

    def create(self, validated_data):
        material = validated_data["material"].strip()
        novas = self._normalize_list(validated_data["marcas"])

        
        obj, created = DescricaoMarca.objects.get_or_create(
            material=material,
            defaults={"marcas": ", ".join(novas)}
        )
        
       
        atuais = [m.strip() for m in (obj.marcas or "").split(",") if m.strip()]
        mescladas = self._normalize_list(atuais + novas)
        obj.marcas = ", ".join(mescladas)
        obj.save(update_fields=["marcas"])

        
        for nome in novas:
            Marca.objects.get_or_create(nome=nome.strip())

        return obj


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


def normalizar_texto(text):
    """Remove acentos e transforma em minúsculo."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()

class ProjetoSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    ambientes = serializers.SerializerMethodField()
    ambientes_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Ambiente.objects.all(), write_only=True, source="ambientes")
    materiais_com_marcas = serializers.SerializerMethodField()  

    class Meta:
        model = Projeto
        fields = [
            'id', 'nome_do_projeto', 'tipo_do_projeto', 'data_entrega', 'descricao',
            'status', 'responsavel', 'responsavel_nome', 'data_criacao',
            'data_atualizacao', 'ambientes', 'ambientes_ids',
            'materiais_com_marcas', 
        ]

    # --------------- NOVA LÓGICA AQUI -----------------
    def get_materiais_com_marcas(self, projeto):
        materiais_projeto = MaterialSpec.objects.filter(projeto=projeto)
        todas_marcas = DescricaoMarca.objects.all()  # globais
        resultado = []
        ja_adicionados = set()

        for material in materiais_projeto:
            # Nome do item, exemplo: "Ferragem", "Parede", "Piso"
            item_nome = (material.item or "").strip().lower()
            descricao = (material.descricao or "").strip().lower()

            # Se o nome do item for exatamente igual ao nome do material cadastrado globalmente → adiciona
            for marca_global in todas_marcas:
                nome_material = marca_global.material.strip().lower()

                if nome_material == item_nome and nome_material not in ja_adicionados:
                    ja_adicionados.add(nome_material)
                    resultado.append({
                        "material": marca_global.material,
                        "marcas": marca_global.marcas
                    })

            #Agora tenta detectar materiais dentro da DESCRIÇÃO (como "cerâmica", "porcelanato")
            for marca_global in todas_marcas:
                nome_material = marca_global.material.strip().lower()

                if nome_material in descricao and nome_material not in ja_adicionados:
                    ja_adicionados.add(nome_material)
                    resultado.append({
                        "material": marca_global.material,
                        "marcas": marca_global.marcas
                    })

        return resultado

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
    projeto_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ModeloDocumento
        fields = ["id", "nome", "descricao", "projeto", "projeto_nome"]

    def get_projeto_nome(self, obj):
        return getattr(obj.projeto, "nome_do_projeto", None)



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['cargo'] = user.cargo
        token['full_name'] = user.get_full_name()
        return token