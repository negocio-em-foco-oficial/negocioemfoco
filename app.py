app.py (Atualizado e Completo)
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Importar modelos e configurações
from models import db, User, File 
from config import Config

load_dotenv()

# Inicialização da Aplicação
app = Flask(__name__)
app.config.from_object(Config)

# Inicialização dos Extensões
db.init_app(app) 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define a rota de login

# --- Funções do Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    # Retorna o objeto User dado o ID
    return User.query.get(int(user_id))

# --- Funções de Ajuda (MOCK DE API) ---
# ******************************************************************
# ATENÇÃO: ESTAS FUNÇÕES SÃO MOCKS E DEVEM SER SUBSTITUÍDAS PELA 
# LÓGICA REAL DE INTERAÇÃO COM A API DO GOOGLE DRIVE E EXTRAÇÃO DE METADADOS.
# ******************************************************************
def mock_google_drive_upload(file_data, filename):
    """Simula o upload para o Google Drive e retorna um ID."""
    print(f"[MOCK] Uploading {filename} to Google Drive...")
    # Em um projeto real, você usaria a Google API Client aqui.
    return "drive-id-" + str(hash(filename + str(datetime.now()))) 

def extract_metadata(file_path, file_mime):
    """Simula a extração de metadados de imagem/documento."""
    if 'image' in file_mime:
        # AQUI você usaria PIL ou pyexiftool para extração real
        return {"creator": "Câmera Exif", "date_taken": datetime.now()}
    elif 'pdf' in file_mime or 'document' in file_mime:
        # AQUI você usaria PyPDF2/python-docx
        return {"creator": "Autor do Doc", "date_taken": datetime.now()}
    
    return {"creator": "System", "date_taken": datetime.now()}

# --- Rotas da Aplicação ---

@app.route('/')
@login_required # Garante que apenas usuários logados acessem
def index():
    # Pega todos os arquivos do usuário logado
    files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', files=files)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Verifique usuário e senha.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Nome de usuário já existe.', 'danger')
            return redirect(url_for('register'))

        # Criptografia da senha
        hashed_password = generate_password_hash(password, method='scrypt') # 'scrypt' é recomendado
        
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename != '':
            
            # 1. Salvar o arquivo temporariamente para processamento (Necessário para o mock e extração)
            temp_path = os.path.join(app.root_path, 'temp_uploads', uploaded_file.filename)
            # Garantir que a pasta temporária exista
            os.makedirs(os.path.join(app.root_path, 'temp_uploads'), exist_ok=True)
            uploaded_file.save(temp_path)
            
            file_mime = uploaded_file.mimetype

            # 2. Upload para o Google Drive (MOCK)
            drive_id = mock_google_drive_upload(temp_path, uploaded_file.filename) 
            
            # 3. Extrair Metadados
            metadata = extract_metadata(temp_path, file_mime)
            
            # 4. Salvar no Banco de Dados
            new_file = File(
                filename=uploaded_file.filename,
                drive_id=drive_id,
                file_type=file_mime,
                creator=metadata['creator'],
                date_taken=metadata['date_taken'],
                user_id=current_user.id
            )
            db.session.add(new_file)
            db.session.commit()
            
            # 5. Limpar Arquivo Temporário
            os.remove(temp_path)
            
            flash('Arquivo enviado e metadados lidos com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nenhum arquivo selecionado.', 'danger')
            
    return render_template('upload.html') 

# --- Inicialização do Banco de Dados ---
# Crie o banco de dados e as tabelas ANTES de rodar o app pela primeira vez.
with app.app_context():
    # Cria as tabelas se não existirem
    db.create_all() 

    # Cria um usuário de teste inicial (se não existir)
    if not User.query.filter_by(username='teste').first():
        hashed_password = generate_password_hash('123456', method='scrypt')
        test_user = User(username='teste', email='teste@example.com', password_hash=hashed_password)
        db.session.add(test_user)
        db.session.commit()
        print("Usuário de teste 'teste' (senha: 123456) criado.")

if __name__ == '__main__':
    # Você deve criar um arquivo .env com o SECRET_KEY, por exemplo:
    # SECRET_KEY="sua-chave-secreta-aqui"
    app.run(debug=True)

2. Criação dos Templates HTML (Mínimos)
Para que o código acima funcione, você precisará de templates básicos.
templates/base.html (Estrutura base com mensagens flash)
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Rede Privada - {{ self.title() }}</title>
</head>
<body>
    <header>
        <nav>
            {% if current_user.is_authenticated %}
                Olá, {{ current_user.username }}! 
                | <a href="{{ url_for('index') }}">Home</a>
                | <a href="{{ url_for('upload_file') }}">Upload</a>
                | <a href="{{ url_for('logout') }}">Sair</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                | <a href="{{ url_for('register') }}">Registrar</a>
            {% endif %}
        </nav>
    </header>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul class="flashes">
        {% for category, message in messages %}
          <li class="{{ category }}">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}

</body>
</html>

templates/login.html
{% extends "base.html" %}

{% block title %}Login{% endblock %}

{% block content %}
    <h2>Login</h2>
    <form method="POST">
        <label for="username">Usuário:</label>
        <input type="text" name="username" required><br><br>
        
        <label for="password">Senha:</label>
        <input type="password" name="password" required><br><br>
        
        <button type="submit">Entrar</button>
    </form>
{% endblock %}

templates/register.html
{% extends "base.html" %}

{% block title %}Registro{% endblock %}

{% block content %}
    <h2>Registro</h2>
    <form method="POST">
        <label for="username">Usuário:</label>
        <input type="text" name="username" required><br><br>
        
        <label for="email">E-mail:</label>
        <input type="email" name="email" required><br><br>
        
        <label for="password">Senha:</label>
        <input type="password" name="password" required><br><br>
        
        <button type="submit">Registrar</button>
    </form>
{% endblock %}

templates/upload.html
{% extends "base.html" %}

{% block title %}Upload de Arquivo{% endblock %}

{% block content %}
    <h2>Upload de Arquivo para a Biblioteca</h2>
    
    <form method="POST" enctype="multipart/form-data">
        <label for="file">Selecione o Arquivo (Foto/Vídeo/Doc):</label>
        <input type="file" name="file" required><br><br>
        
        <button type="submit">Enviar Arquivo</button>
    </form>
{% endblock %}

Como Rodar o Teste:
 * Crie os Arquivos: Garanta que você tenha os arquivos app.py, config.py, models.py, requirements.txt e as pastas templates/ e static/ conforme a estrutura.
 * Instale as Dependências: pip install -r requirements.txt
 * Crie o arquivo .env na raiz do projeto com pelo menos a chave secreta: SECRET_KEY="sua-chave-secreta-aqui"
 * Execute a Aplicação: python app.py
 * Acesse: Abra seu navegador em http://127.0.0.1:5000/.
O sistema irá:
 * Criar o banco de dados database.db (se não existir).
 * Criar o usuário de teste teste com a senha 123456.
 * Você poderá fazer login e ir para a tela de Upload para testar o envio de arquivos e a leitura (simulada) de metadados.
Este é o ponto de partida sólido para você começar a integrar as APIs reais (Google Drive/Calendar) e desenvolver as funcionalidades de Projeto e Discussão!
