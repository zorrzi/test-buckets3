# 🚀 Guia de Início Rápido

Siga estes passos para ter a aplicação funcionando rapidamente!

## Passo 1: Instalar Dependências

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

## Passo 2: Configurar o .env

1. Copie o arquivo de exemplo:
```powershell
Copy-Item .env.example .env
```

2. Edite o arquivo `.env` e preencha com suas credenciais AWS:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...  # Obrigatório para credenciais temporárias (ASIA...)
S3_BUCKET_NAME=seu-bucket-name
```

### Como obter as credenciais no AWS Academy:

1. Acesse o AWS Academy Learner Lab
2. Clique em "AWS Details"
3. Clique em "Show" ao lado de "AWS CLI"
4. Copie as três linhas e cole no `.env`:
   - `aws_access_key_id` → `AWS_ACCESS_KEY_ID`
   - `aws_secret_access_key` → `AWS_SECRET_ACCESS_KEY`
   - `aws_session_token` → `AWS_SESSION_TOKEN`

## Passo 3: Configurar o Bucket S3

### 3.1 Criar o Bucket (se ainda não existir)

1. Acesse o Console AWS S3
2. Clique em "Create bucket"
3. Escolha um nome único (ex: `pdf-manager-seunome-2024`)
4. Região: **us-east-1** (ou a que você configurou)
5. **IMPORTANTE**: Em "Block Public Access", deixe TODAS as opções marcadas (bucket privado)
6. Clique em "Create bucket"

### 3.2 Configurar CORS

1. Selecione seu bucket
2. Vá em "Permissions"
3. Role até "Cross-origin resource sharing (CORS)"
4. Clique em "Edit"
5. Cole a seguinte configuração:

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

6. Clique em "Save changes"

## Passo 4: Testar Conexão

Execute o script de teste para verificar se tudo está funcionando:

```powershell
python test_s3_connection.py
```

✅ Se todos os testes passarem, você está pronto!

## Passo 5: Executar a Aplicação

```powershell
python app.py
```

Ou com uvicorn:

```powershell
uvicorn app:app --reload
```

A aplicação estará disponível em: **http://localhost:8000**

## Passo 6: Usar a Aplicação

1. Abra seu navegador em `http://localhost:8000`
2. Digite um ID de usuário (ex: `user123`)
3. Clique em "Carregar Documentos"
4. Faça upload de um PDF
5. Veja o documento aparecer na galeria
6. Clique no documento para ver detalhes, fazer download ou deletar

## 🐛 Problemas Comuns

### "Bucket não encontrado"
- ✅ Verifique se o nome do bucket no `.env` está correto
- ✅ Confirme que o bucket foi criado na região especificada

### "Access Denied"
- ✅ Verifique se as credenciais estão corretas no `.env`
- ✅ Confirme que você tem as permissões necessárias (veja `IAM_PERMISSIONS.md`)
- ✅ Se usando AWS Academy, verifique se o lab está "Started" (verde)

### "Invalid Token" ou "Expired Token"
- ✅ As credenciais do AWS Academy expiram! Gere novas credenciais
- ✅ Certifique-se de incluir o `AWS_SESSION_TOKEN` para credenciais temporárias

### "CORS Error" no navegador
- ✅ Verifique se o CORS está configurado corretamente no bucket (Passo 3.2)
- ✅ Certifique-se de que salvou as mudanças

### "Import não encontrado" ao executar Python
- ✅ Verifique se o ambiente virtual está ativado
- ✅ Execute `pip install -r requirements.txt` novamente

## 📊 Verificar Status

Acesse o endpoint de health check:

```
http://localhost:8000/health
```

Resposta esperada:
```json
{
  "status": "ok",
  "bucket": "seu-bucket-name",
  "region": "us-east-1",
  "s3_accessible": true
}
```

## 🎉 Pronto!

Sua aplicação está funcionando! Agora você pode:

- ✅ Fazer upload de PDFs
- ✅ Listar documentos por usuário
- ✅ Fazer download usando URLs pré-assinadas
- ✅ Deletar documentos

## 📚 Mais Informações

- **README.md**: Documentação completa
- **IAM_PERMISSIONS.md**: Detalhes sobre permissões necessárias
- **app.py**: Código do backend
- **static/**: Código do frontend

## 🆘 Precisa de Ajuda?

1. Execute o script de teste: `python test_s3_connection.py`
2. Verifique os logs da aplicação
3. Acesse `/health` para verificar o status
4. Revise o README.md completo
