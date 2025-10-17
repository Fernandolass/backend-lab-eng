from django.db import models
# backend/api/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

#Modelo de Usuário 
class Usuario(AbstractUser):
    CARGO_CHOICES = [
        ('atendente', 'Atendente'),
        ('gerente', 'Gerente'),
        ('superadmin', 'Super Admin'),
    ]
    email = models.EmailField(unique=True)
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default='atendente')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

# modelo de Projeto / documento de criação / entidade central

class Projeto(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REPROVADO', 'Reprovado'),
    ]
    
    TIPO_PROJETO_CHOICES = [
        ('RESIDENCIAL', 'Residencial'),
        ('COMERCIAL', 'Comercial'),
    ]

    nome_do_projeto = models.CharField(max_length=255)
    tipo_do_projeto = models.CharField(max_length=50, choices=TIPO_PROJETO_CHOICES)
    data_entrega = models.DateField()
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='projetos_criados')
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"

    def __str__(self):
        return self.nome_do_projeto

class Ambiente(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='ambientes')
    
    nome_do_ambiente = models.CharField(max_length=100)
    guia_de_cores = models.CharField(max_length=255, blank=True)

    piso = models.TextField(blank=True)
    parede = models.TextField(blank=True)
    teto = models.TextField(blank=True)
    rodape = models.TextField(blank=True)
    soleira = models.TextField(blank=True)
    peitoril = models.TextField(blank=True)
    esquadria = models.TextField(blank=True)
    vidro = models.TextField(blank=True)
    porta = models.TextField(blank=True)
    ferragem = models.TextField(blank=True)
    inst_eletrica = models.TextField(blank=True, verbose_name="Instalação Elétrica")
    inst_comunicacao = models.TextField(blank=True, verbose_name="Instalação de Comunicação")

    class Meta:
        verbose_name = "Ambiente"
        verbose_name_plural = "Ambientes"

    def __str__(self):
        return f"{self.nome_do_ambiente} - {self.projeto.nome_do_projeto}"

class Log(models.Model):
    ACAO_CHOICES = [
        ('CRIACAO', 'Criação'),
        ('APROVACAO', 'Aprovação'),
        ('REPROVACAO', 'Reprovação'),
        ('EDICAO', 'Edição'),
        ('LOGIN', 'Login'),
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    
    projeto = models.ForeignKey(Projeto, on_delete=models.SET_NULL, null=True, blank=True)
    
    motivo = models.TextField(blank=True, null=True) 
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"

    def __str__(self):
        return f"{self.usuario.email} - {self.acao} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

class ModeloDocumento(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()

    def __str__(self):
        return self.nome

class TipoAmbiente(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Ambiente"
        verbose_name_plural = "Tipos de Ambiente"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Marca(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# vínculo opcional do Ambiente com um TipoAmbiente
# (se quiser poderá preencher depois sem quebrar nada)
Ambiente.add_to_class('tipo', models.ForeignKey(
    TipoAmbiente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ambientes'
))


class MaterialSpec(models.Model):
    STATUS = (
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REPROVADO', 'Reprovado'),
    )
    ITENS = (
        ('PISO', 'Piso'),
        ('PAREDE', 'Parede'),
        ('TETO', 'Teto'),
        ('RODAPE', 'Rodapé'),
        ('SOLEIRA', 'Soleira'),
        ('PEITORIL', 'Peitoril'),
        ('ESQUADRIA', 'Esquadria'),
        ('VIDRO', 'Vidro'),
        ('PORTA', 'Porta'),
        ('FERRAGEM', 'Ferragem'),
        ('INST_ELETRICA', 'Inst. Elétrica'),
        ('INST_COMUNICACAO', 'Inst. Comunicação'),
    )

    ambiente = models.ForeignKey('Ambiente', on_delete=models.CASCADE, related_name='materials')
    item = models.CharField(max_length=30, choices=ITENS)
    descricao = models.TextField(blank=True)
    # catálogo (opcional)
    marca = models.ForeignKey(Marca, null=True, blank=True, on_delete=models.SET_NULL, related_name='materiais')

    status = models.CharField(max_length=10, choices=STATUS, default='PENDENTE')
    motivo = models.TextField(blank=True, null=True)
    aprovador = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='materiais_aprovados')
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('ambiente', 'item')  # um item de cada tipo por ambiente
        ordering = ['ambiente_id', 'item']
        verbose_name = 'Material do Ambiente'
        verbose_name_plural = 'Materiais do Ambiente'

    def __str__(self):
        return f'{self.ambiente} - {self.get_item_display()}'