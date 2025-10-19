# Permissões IAM Necessárias

Para que a aplicação funcione corretamente, o usuário ou role IAM que está sendo usado precisa ter as seguintes permissões no bucket S3:

## Política IAM Recomendada

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3BucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:HeadBucket"
            ],
            "Resource": [
                "arn:aws:s3:::SEU-BUCKET-NAME",
                "arn:aws:s3:::SEU-BUCKET-NAME/*"
            ]
        }
    ]
}
```

## Permissões Detalhadas

### s3:HeadBucket
- Permite verificar se o bucket existe e está acessível
- Usado no health check e startup da aplicação

### s3:ListBucket
- Permite listar objetos no bucket
- Útil para operações de listagem (não usado no código atual, mas recomendado)

### s3:PutObject
- **ESSENCIAL** - Permite upload de arquivos
- Usado para gerar URLs pré-assinadas de upload

### s3:GetObject
- **ESSENCIAL** - Permite download de arquivos
- Usado para gerar URLs pré-assinadas de download

### s3:DeleteObject
- Permite deletar arquivos do bucket
- Usado no endpoint de deleção de documentos

## Como Aplicar

### Opção 1: Usuário IAM (Credenciais de longo prazo)

1. Acesse o Console AWS IAM
2. Vá em "Users" → Selecione seu usuário
3. Clique em "Add permissions" → "Attach policies directly"
4. Clique em "Create policy" e cole a política JSON acima
5. Substitua `SEU-BUCKET-NAME` pelo nome real do seu bucket
6. Dê um nome à política (ex: "PDFManagerS3Access")
7. Anexe a política ao seu usuário

### Opção 2: AWS Academy / Credenciais Temporárias

No AWS Academy (Learner Lab), as permissões já estão configuradas através da role `LabRole`. Você só precisa:

1. Obter as credenciais temporárias do AWS Details
2. Incluir `AWS_SESSION_TOKEN` no arquivo `.env`
3. As credenciais expiram - você precisará atualizá-las periodicamente

### Opção 3: EC2 Instance Role (Produção)

Se estiver rodando em uma instância EC2:

1. Crie uma role IAM com a política acima
2. Anexe a role à instância EC2
3. O boto3 usará automaticamente as credenciais da role
4. Não é necessário configurar credenciais no `.env`

## Bucket Policy (Opcional)

Você também pode adicionar uma política diretamente ao bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPresignedURLs",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT-ID:user/USUARIO-NAME"
            },
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::SEU-BUCKET-NAME/*"
        }
    ]
}
```

Substitua:
- `ACCOUNT-ID`: ID da sua conta AWS
- `USUARIO-NAME`: Nome do seu usuário IAM
- `SEU-BUCKET-NAME`: Nome do seu bucket

## Verificação de Permissões

Para testar se as permissões estão corretas, acesse:

```
http://localhost:8000/health
```

A resposta deve incluir `"s3_accessible": true` se tudo estiver configurado corretamente.

## Troubleshooting

### Erro: "AccessDenied"
- Verifique se a política IAM está anexada ao usuário correto
- Confirme que o ARN do bucket está correto
- Verifique se as credenciais no `.env` estão corretas

### Erro: "InvalidToken"
- Para credenciais temporárias (ASIA...), o `AWS_SESSION_TOKEN` é obrigatório
- Credenciais do AWS Academy expiram - gere novas credenciais

### Erro: "ExpiredToken"
- Suas credenciais temporárias expiraram
- Obtenha novas credenciais do AWS Academy/Console
