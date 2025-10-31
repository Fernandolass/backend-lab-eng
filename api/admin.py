from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Projeto, Ambiente, Log, ModeloDocumento, MaterialSpec, TipoAmbiente, Marca, DescricaoMarca

class CustomUserAdmin(UserAdmin):
    # Mostra os campos personalizados na lista de usuários
    list_display = ('email', 'username', 'cargo', 'is_staff')
    # Adiciona o campo 'cargo' ao formulário de edição do usuário
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('cargo',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('cargo',)}),
    )

admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Projeto)
admin.site.register(Ambiente)
admin.site.register(Log)
admin.site.register(ModeloDocumento)
admin.site.register(MaterialSpec)
admin.site.register(TipoAmbiente)
admin.site.register(Marca)
admin.site.register(DescricaoMarca)