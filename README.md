# PDF Manager - Sistema de Gerenciamento de Documentos com S3

Sistema completo para upload, gerenciamento e download de documentos PDF usando Amazon S3 com URLs pré-assinadas.

## 🚀 Funcionalidades

- ✅ Upload seguro de PDFs para bucket S3 privado
- ✅ URLs pré-assinadas para upload e download
- ✅ Gerenciamento de metadados local (JSON)
- ✅ Interface web responsiva e moderna
- ✅ Suporte a múltiplos usuários
- ✅ Progress tracking durante upload
- ✅ Download direto do S3
- ✅ Deleção de documentos

## 📋 Pré-requisitos

- Python 3.8+
- Conta AWS com acesso ao S3
- Bucket S3 criado e configurado
- Credenciais AWS (Access Key, Secret Key, Session Token se aplicável)

## 🔧 Configuração

### 1. Clone o repositório ou faça download dos arquivos

### 2. Crie e ative um ambiente virtual

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Ativar (Windows CMD)
.\venv\Scripts\activate.bat
```

### 3. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e preencha com suas credenciais:

```powershell
# No PowerShell
Copy-Item .env.example .env
```

Edite o arquivo `.env`:

```bash
# Configurações AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=sua_access_key_aqui
AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
AWS_SESSION_TOKEN=seu_session_token_aqui  # Obrigatório para credenciais temporárias
S3_BUCKET_NAME=seu-bucket-name-aqui

# Tempo de expiração das URLs (em segundos)
PRESIGNED_URL_EXPIRATION_UPLOAD=900      # 15 minutos
PRESIGNED_URL_EXPIRATION_DOWNLOAD=3600   # 1 hora

# Modo debug
DEBUG=True
```

### 5. Configure o CORS do seu bucket S3

No console AWS S3, adicione a seguinte configuração CORS ao seu bucket:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

> ⚠️ **Importante**: Em produção, substitua `"*"` em `AllowedOrigins` pelo domínio específico do seu frontend.

## 🚀 Executando a aplicação

### Desenvolvimento

```powershell
# Com reload automático
python app.py
```

Ou usando uvicorn diretamente:

```powershell
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Produção

```powershell
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

A aplicação estará disponível em: `http://localhost:8000`

## 📁 Estrutura do Projeto

```
test-buckets3/
├── app.py                  # Backend FastAPI
├── requirements.txt        # Dependências Python
├── .env                   # Variáveis de ambiente (não versionado)
├── .env.example           # Exemplo de configuração
├── .gitignore            # Arquivos ignorados pelo Git
├── README.md             # Este arquivo
├── data/                 # Metadados dos documentos (criado automaticamente)
│   └── documents_metadata.json
└── static/               # Frontend
    ├── index.html       # Interface principal
    ├── styles.css       # Estilos
    └── app.js           # Lógica do frontend
```

## 🔐 Segurança

### Bucket S3 Privado

O bucket deve ser configurado como **privado**. O acesso aos arquivos é feito exclusivamente através de URLs pré-assinadas geradas pelo backend.

### URLs Pré-assinadas

- **Upload**: Válida por 15 minutos (configurável)
- **Download**: Válida por 1 hora (configurável)
- As URLs expiram automaticamente após o tempo configurado

### Credenciais AWS

- Nunca commite o arquivo `.env` no Git
- Use credenciais com permissões mínimas necessárias
- Para credenciais temporárias (ASIA...), o `AWS_SESSION_TOKEN` é obrigatório

## 📊 Fluxo de Upload

1. **Frontend**: Usuário seleciona um arquivo PDF
2. **Frontend → Backend**: Solicita URL pré-assinada (`POST /api/presign-upload`)
3. **Backend → AWS**: Gera URL pré-assinada para PUT no S3
4. **Backend → Frontend**: Retorna URL e documentId
5. **Frontend → S3**: Faz upload direto usando a URL pré-assinada
6. **Frontend → Backend**: Notifica conclusão do upload (`POST /api/notify-upload`)
7. **Backend**: Atualiza metadados do documento (status = "uploaded")

## 📥 Fluxo de Download

1. **Frontend**: Usuário clica em "Download"
2. **Frontend → Backend**: Solicita URL de download (`GET /api/documents/{id}/download`)
3. **Backend → AWS**: Gera URL pré-assinada para GET no S3
4. **Backend → Frontend**: Retorna URL de download
5. **Frontend**: Abre a URL em nova aba (download automático)

## 🔌 API Endpoints

### Health Check
```
GET /health
```

### Upload
```
POST /api/presign-upload
Body: {
  "filename": "documento.pdf",
  "userId": "user123",
  "contentType": "application/pdf"
}
```

### Notificar Upload
```
POST /api/notify-upload
Body: {
  "documentId": "uuid",
  "userId": "user123",
  "sizeBytes": 1024000,
  "status": "uploaded"
}
```

### Listar Documentos
```
GET /api/documents?userId=user123
```

### Download
```
GET /api/documents/{documentId}/download?userId=user123
```

### Deletar
```
DELETE /api/documents/{documentId}?userId=user123
```

## 🎨 Interface do Usuário

### Recursos da Interface

- Design moderno e responsivo
- Drag & drop para upload de arquivos
- Barra de progresso durante upload
- Galeria de documentos com cards
- Modal com detalhes do documento
- Notificações de sucesso/erro
- Armazenamento local do ID do usuário

### Como Usar

1. Digite seu ID de usuário e clique em "Carregar Documentos"
2. Arraste um PDF ou clique na área de upload
3. Clique em "Enviar Documento"
4. Acompanhe o progresso do upload
5. Visualize seus documentos na galeria
6. Clique em um documento para ver detalhes, fazer download ou deletar

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web moderno e rápido
- **Boto3**: SDK oficial da AWS para Python
- **Python-dotenv**: Gerenciamento de variáveis de ambiente
- **Pydantic**: Validação de dados
- **Uvicorn**: Servidor ASGI

### Frontend
- **HTML5**: Estrutura semântica
- **CSS3**: Estilos modernos com variáveis CSS
- **JavaScript ES6+**: Lógica do cliente (sem frameworks)

### Cloud
- **Amazon S3**: Armazenamento de objetos
- **AWS IAM**: Gerenciamento de credenciais e permissões

## 🐛 Troubleshooting

### Erro: "Bucket não encontrado"
- Verifique se o nome do bucket está correto no `.env`
- Confirme que o bucket existe na região especificada

### Erro: "Acesso negado ao bucket"
- Verifique se as credenciais AWS estão corretas
- Confirme que a IAM role/user tem permissões de `s3:PutObject` e `s3:GetObject`

### Erro: "Upload falhou"
- Verifique a configuração CORS do bucket
- Confirme que o arquivo é um PDF válido
- Verifique se o tamanho do arquivo não excede 50MB

### Erro: "Session token inválido"
- Se usando credenciais temporárias (AWS Academy), certifique-se de incluir `AWS_SESSION_TOKEN` no `.env`

## 📝 Notas Importantes

- Os metadados são armazenados localmente no arquivo `data/documents_metadata.json`
- Para produção, considere usar um banco de dados (DynamoDB, PostgreSQL, etc.)
- As URLs pré-assinadas expiram - configure os tempos de acordo com suas necessidades
- Em produção, configure CORS e origins específicos (não use `*`)

## 📄 Licença

Este projeto é fornecido como exemplo educacional.

## 👨‍💻 Autor

Desenvolvido para gerenciamento de documentos PDF com armazenamento seguro na AWS S3