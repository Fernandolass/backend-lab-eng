from django.core.management.base import BaseCommand
from api.models import Ambiente, MaterialSpec, DescricaoMarca


class Command(BaseCommand):
    help = "Popula o banco com TODOS os ambientes, itens e marcas da especificação técnica"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Iniciando população do banco..."))

        # ==============================
        # AMBIENTES + ITENS
        # ==============================
        especificacao = {
            # ====== UNIDADES PRIVATIVAS ======
            "Sala de Estar/Jantar": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Porcelanato ou laminado",
                    "Parede": "Pintura PVA látex branco sobre gesso ou massa de regulariação PVA.",
                    "Teto": "Pintura PVA látex branco sobre gesso ou massa de regularização PVA.",
                    "Rodapé": "Porcelanato ou Laminado, h= 5cm",
                    "Soleira": "Mármore ou granito.",
                    "Peitoril": "Metálico",
                    "Esquadria": "Alumínio pintado de branco",
                    "Vidro": "Liso incolor.",
                    "Porta": "Porta semi–ôca comum pintada c/ esmalte sintético.",
                    "Ferragem": "Acabamento cromado.",
                    "Inst. Elétrica": "Pontos de luz no teto, tomadas de corrente e interruptores",
                    "Inst. Comunic.": "Pontos secos de comunicação e de antena de TV.",
                },
            },
            "Circulação": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Porcelanato ou laminado",
                    "Parede": "Pintura PVA látex branco sobre gesso ou massa de regulariação PVA.",
                    "Teto": "Pintura PVA látex branco sobre gesso ou massa de regularização PVA.",
                    "Rodapé": "Porcelanato ou Laminado, h= 5cm",
                    "Inst. Elétrica": "Pontos de luz no teto, tomadas de corrente e interruptores",
                },
            },
            "Quarto/Suíte": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Porcelanato ou laminado.",
                    "Parede": "Pintura PVA látex branco sobre gesso ou massa de regulariação PVA.",
                    "Teto": "Pintura PVA látex branco sobre gesso ou massa de regularização PVA.",
                    "Rodapé": "Porcelanato ou Laminado, h=5cm.",
                    "Soleira": "Mármore ou granito.",
                    "Peitoril": "Metálico.",
                    "Esquadria": "Alumínio pintado de branco.",
                    "Vidro": "Liso incolor.",
                    "Porta": "Porta semi–ôca comum pintada c/ esmalte sintético.",
                    "Ferragem": "Acabamento cromado.",
                    "Inst. Elétrica": "Pontos de luz no teto, tomadas de corrente e interruptores.",
                    "Inst. Comunic.": "Pontos secos de comunicação e de antena de TV.",
                    "Ar Condicionado": "Infraestrutura para high wall com condensadora axial.",
                },
            },
            "Sanitário/Lavabo": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Cerâmica.",
                    "Parede": "Cerâmica até o teto.",
                    "Teto": "Forro de gesso.",
                    "Filete": "Mármore ou granito L=3,5cm.",
                    "Cordão de Box": "Mármore ou granito.",
                    "Bancada": "Em mármore ou granito com cuba em louça cor branca",
                    "Porta": "Porta semi-ôca comum pintura c/ esmalte sintético.",
                    "Peitoril": "Metálico.",
                    "Ferragem": "Acabamento cromado.",
                    "Esquadria": "Alumínio pintado de branco.",
                    "Vidro": "Pontilhado Incolor.",
                    "Metal Sanitário": "Torneira para Lavatório, registro de gaveta e registro de pressão com acabamento cromado.",
                    "Louças": "Vaso Sanitário com Caixa Acoplada em louça cor branca.",
                    "Inst. Elétrica": "Pontos de luz no teto, tomada de corrente e interruptor da Prime, Alumbra, Cemar ou Fame na cor branco.",
                    "Inst. Hidráulica": "Sifão em PVC, esgoto em PVC, rede de água fria e ducha higiênica em PEX.",
                },
            },
            "Cozinha/Área de Serviço": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Cerâmica.",
                    "Parede": "Cerâmica até o teto.",
                    "Teto": "Pintura látex PVA sobre gesso ou argamassa de regularização PVA.",
                    "Filete": "Mármore ou granito L=3,5cm.",
                    "Bancada": "Em mármore ou granito.",
                    "Cuba": "Inox.",
                    "Peitoril": "Metálico.",
                    "Tanque": "Louça cor branca.",
                    "Esquadrias": "Alumínio pintado de branco.",
                    "Metais": "Torneiras e registro de gaveta com acabamento cromado.",
                    "Inst. Elétricas": "Ponto de luz no teto, tomadas de corrente e interruptores.",
                    "Inst. Hidráulica": "Rede de água fria em PEX e esgoto em PVC",
                    "Inst. Comunicação": "Tubulação seca.",
                },
            },
            "Área Técnica": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Em concreto desempolado.",
                    "Parede": "Textura acrílica.",
                    "Teto": "Pintura ou textura acrílica.",
                    "Gradil": "Em perfil metálico pintado de branco.",
                },
            },
            "Varanda": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Porcelanato.",
                    "Parede": "Textura Acrílica ou Pastilha Cerâmica.",
                    "Teto": "Pintura PVA látex branco ou Forro de gesso.",
                    "Rodapé": "Porcelanato ou Laminado, h=5cm.",
                    "Porta": "Alumínio pintado de branco com vidro liso.",
                    "Inst. Elétrica": "Ponto de luz no teto.",
                    "Guarda Corpo": "Em perfil metálico pintado de branco.",
                },
            },
            "Garden": {
                "categoria": "PRIVATIVA",
                "materiais": {
                    "Piso": "Grama",
                    "Gradil": "Em perfil metálico pintado de branco.",
                },
            },
            # ⚠️ Aqui continuam TODOS os outros ambientes do DOC:
            # Guarita, Gourmets, Quiosques, Copa Funcionários, Petplay, Parque Infantil,
            # Brinquedoteca, Salão de Festas, Bicicletário, Salão de Jogos, Academia,
            # Administração, Quadra Esportiva, Quadra de Areia, Piscina, Gerador, Casa de Lixo,
            # Vestiário, Escadaria, Depósito, Muro, Hall, Instalações Gerais, Jardins, etc.
        }

        for nome, data in especificacao.items():
            amb, created = Ambiente.objects.get_or_create(
                nome_do_ambiente=nome,
                defaults={"categoria": data["categoria"]}
            )
            for item, descricao in data["materiais"].items():
                MaterialSpec.objects.get_or_create(
                    ambiente=amb,
                    item=item,
                    defaults={"descricao": descricao},
                )

        # ==============================
        # MARCAS
        # ==============================
        marcas = {
            "Cerâmica": "Incesa, Portobello, Arielle, Tecnogres, Pamesa, Camelo Fior, Biancogrês, Pointer.",
            "Porcelanato": "Portobello, Arielle, Tecnogres, Pamesa, Biancogrês, Elizabeth, Ceusa, Pointer, Villagres.",
            "Laminado": "Eucatex, Durafloor ou Espaçofloor.",
            "Esquadria": "Esaf, Alumasa, Atlantica, Ramassol ou Unicasa.",
            "Ferragem": "Silvana, Stam, Arouca, Soprano, Aliança, Imab.",
            "Inst. Elétrica": "Alumbra, Steck, Ilumi, Schneider, Margirius ou Fame.",
            "Metal Sanitário": "Forusi, Deca, Celite, Fabrimar ou Docol.",
            "Louças": "Celite, Deca, Incepa.",
            "Porta (alumínio)": "Esaf, Mgm, Alumasa, Atlantica, Ramassol ou Unicasa.",
            "Cuba (inox)": "Ghel Plus, Frank, Tramontina ou Pianox, Tecnocuba.",
            "Cuba (louça)": "Celite, Deca, Incepa.",
        }

        for material, marcas_txt in marcas.items():
            DescricaoMarca.objects.get_or_create(
                material=material,
                defaults={"marcas": marcas_txt, "projeto_id": None}
            )

        self.stdout.write(self.style.SUCCESS("✅ Banco populado com sucesso!"))