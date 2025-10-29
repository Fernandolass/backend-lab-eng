from django.core.management.base import BaseCommand
from api.models import Projeto, MaterialSpec


class Command(BaseCommand):
    help = "Verifica se os projetos estão herdando corretamente os materiais do memorial"

    def handle(self, *args, **kwargs):
        projetos = Projeto.objects.all().order_by("id")

        if not projetos.exists():
            self.stdout.write(self.style.WARNING("⚠️ Nenhum projeto encontrado."))
            return

        for projeto in projetos:
            self.stdout.write(self.style.SUCCESS(f"\n🧱 Projeto {projeto.id}: {projeto.nome_do_projeto}"))
            materiais = MaterialSpec.objects.filter(projeto=projeto).select_related("ambiente")

            if not materiais.exists():
                self.stdout.write(self.style.ERROR("❌ Nenhum material vinculado a este projeto!"))
                continue

            ambientes = {}
            for m in materiais:
                ambientes.setdefault(m.ambiente.nome_do_ambiente, []).append(m)

            for nome, itens in ambientes.items():
                self.stdout.write(self.style.HTTP_INFO(f"   🏠 Ambiente: {nome}"))
                for mat in itens:
                    desc = (mat.descricao or "").strip() or "—"
                    self.stdout.write(f"      • {mat.item_label}: {desc}")

        # Checagem de modelos base
        base_count = MaterialSpec.objects.filter(projeto__isnull=True).count()
        self.stdout.write(f"\n📦 Materiais-base no memorial: {base_count}")
        self.stdout.write(self.style.SUCCESS("✅ Verificação concluída!"))