from django.core.management.base import BaseCommand
from api.models import MaterialSpec
from django.db.models import Count

class Command(BaseCommand):
    help = "Remove materiais duplicados (mesmo projeto, ambiente e item)"

    def handle(self, *args, **options):
        print("🧹 Limpando duplicatas de MaterialSpec...")

        duplicatas = (
            MaterialSpec.objects.values("projeto_id", "ambiente_id", "item")
            .annotate(qtd=Count("id"))
            .filter(qtd__gt=1)
        )

        total = 0
        for dup in duplicatas:
            repetidos = MaterialSpec.objects.filter(
                projeto_id=dup["projeto_id"],
                ambiente_id=dup["ambiente_id"],
                item=dup["item"],
            ).order_by("id")

            # mantém o primeiro, deleta o resto
            for m in repetidos[1:]:
                m.delete()
                total += 1

        print(f"✅ Limpeza concluída! {total} duplicatas removidas.")