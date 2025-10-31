Como Rodar o Backend

Passos

1. Clone o repositório:
```
git clone https://github.com/Fernandolass/backend-lab-eng.git
cd backend-lab-eng
```

2. Crie e ative um ambiente virtual:

 ```
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
 ```
Caso dê erro tipo 
```
O arquivo  não pode ser carregado porque a execução de scripts foi desabilitada neste sistema. 
```
Utilize este comando: 
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

4. Configure variáveis de ambiente criando um arquivo .env:
```
DEBUG=True
SECRET_KEY=m@5#f$_c+69y=_w3@g45w658sdttig!#m12gh@6m=bzyg!2-

MYSQLHOST=interchange.proxy.rlwy.net
MYSQLPORT=15925
MYSQLUSER=root
MYSQLPASSWORD=DsiYJlmgkaUPVYguxlVAILfvUBJXhUhL
MYSQLDATABASE=railway
```

5. Inicie o servidor de desenvolvimento:
```
python manage.py runserver
```
