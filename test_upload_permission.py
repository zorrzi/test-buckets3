"""
Script para testar permissões de upload no S3
"""
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

print("=" * 60)
print("TESTE DE PERMISSÕES S3")
print("=" * 60)
print(f"Bucket: {S3_BUCKET_NAME}")
print(f"Região: {AWS_REGION}")
print(f"Access Key: {AWS_ACCESS_KEY_ID}")
print("=" * 60)

# Cria cliente S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Teste 1: Verificar acesso ao bucket
print("\n1️⃣  Testando acesso ao bucket (HeadBucket)...")
try:
    s3.head_bucket(Bucket=S3_BUCKET_NAME)
    print("   ✅ SUCESSO: Bucket acessível")
except ClientError as e:
    print(f"   ❌ ERRO: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
    exit(1)

# Teste 2: Verificar permissão de listagem
print("\n2️⃣  Testando listagem de objetos (ListObjects)...")
try:
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
    print(f"   ✅ SUCESSO: Listagem permitida (objetos no bucket: {response.get('KeyCount', 0)})")
except ClientError as e:
    print(f"   ❌ ERRO: {e.response['Error']['Code']} - {e.response['Error']['Message']}")

# Teste 3: Verificar permissão de upload
print("\n3️⃣  Testando upload de arquivo (PutObject)...")
test_key = "documents/test-permission-check.txt"
test_content = b"Este eh um arquivo de teste para verificar permissoes"

try:
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=test_key,
        Body=test_content,
        ContentType='text/plain'
    )
    print(f"   ✅ SUCESSO: Upload permitido")
    print(f"   📄 Arquivo criado: s3://{S3_BUCKET_NAME}/{test_key}")
    
    # Teste 4: Verificar se consegue deletar
    print("\n4️⃣  Testando exclusão de arquivo (DeleteObject)...")
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=test_key)
        print("   ✅ SUCESSO: Exclusão permitida")
    except ClientError as e:
        print(f"   ⚠️  AVISO: Não foi possível deletar - {e.response['Error']['Code']}")
        print(f"   (Arquivo de teste permanece em: s3://{S3_BUCKET_NAME}/{test_key})")
        
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_msg = e.response['Error']['Message']
    print(f"   ❌ ERRO: {error_code} - {error_msg}")
    
    if error_code == 'AccessDenied':
        print("\n" + "=" * 60)
        print("⚠️  PROBLEMA IDENTIFICADO: PERMISSÃO DE UPLOAD NEGADA")
        print("=" * 60)
        print("\nSeu usuário IAM NÃO tem permissão 's3:PutObject'.")
        print("\nPara corrigir, adicione esta política ao seu usuário IAM:")
        print("-" * 60)
        print('''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::documents-ijr/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::documents-ijr"
        }
    ]
}''')
        print("-" * 60)
        print("\nOu adicione esta política ao BUCKET (Bucket Policy):")
        print("-" * 60)
        print(f'''{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Principal": {{
                "AWS": "arn:aws:iam::ACCOUNT_ID:user/SEU_USUARIO"
            }},
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::{S3_BUCKET_NAME}/*"
        }}
    ]
}}''')
        print("-" * 60)

# Teste 5: Testar geração de URL pré-assinada
print("\n5️⃣  Testando geração de URL pré-assinada...")
try:
    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': S3_BUCKET_NAME,
            'Key': 'documents/test-presigned.pdf',
            'ContentType': 'application/pdf'
        },
        ExpiresIn=900
    )
    print("   ✅ SUCESSO: URL pré-assinada gerada")
    print(f"   🔗 URL: {presigned_url[:100]}...")
    print("\n   ⚠️  NOTA: URL gerada com sucesso, mas pode falhar com 403")
    print("   se o usuário não tiver permissão s3:PutObject")
except Exception as e:
    print(f"   ❌ ERRO: {str(e)}")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO")
print("=" * 60)
