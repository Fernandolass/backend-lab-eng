Como Rodar o Backend 
1. Clone o repositório
git clone https://github.com/Fernandolass/backend-lab-eng.git
cd backend-lab-eng

2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Linux / Mac


Se aparecer erro de script no PowerShell (Windows):

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

3. Instale as dependências
pip install -r requirements.txt

4. Configure o arquivo .env

Crie um arquivo chamado .env na raiz do projeto e copie o conteúdo do arquivo .env.example, por exemplo:

DEBUG=True
SECRET_KEY=sua-secret-key-aqui
USE_SQLITE=True


Não coloque senhas reais ou dados da empresa.

5. (Opcional) Popular banco com dados fictícios
python manage.py migrate
python manage.py popular_fake_data


Isso criará usuários de teste:

Usuário	Email	Senha	Cargo
Admin	admin@teste.com admin123
Gerente	gerente@teste.com gerente123	gerente
Atendente	atendente@teste.com atendente123	atendente

6. Inicie o servidor
python manage.py runserver