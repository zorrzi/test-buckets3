# Script de teste para verificar conexão com S3
import os
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Carregar variáveis de ambiente
load_dotenv()

REGION = os.environ.get("AWS_REGION", "us-east-1")
BUCKET = os.environ.get("S3_BUCKET_NAME")

print("=" * 60)
print("TESTE DE CONEXÃO AWS S3")
print("=" * 60)

# Verificar configurações
print("\n📋 Configurações:")
print(f"   Região: {REGION}")
print(f"   Bucket: {BUCKET}")
print(f"   Access Key: {'✓ Configurada' if os.environ.get('AWS_ACCESS_KEY_ID') else '✗ Não configurada'}")
print(f"   Secret Key: {'✓ Configurada' if os.environ.get('AWS_SECRET_ACCESS_KEY') else '✗ Não configurada'}")
print(f"   Session Token: {'✓ Configurada' if os.environ.get('AWS_SESSION_TOKEN') else '✗ Não configurada (ok se não for temporária)'}")

if not BUCKET:
    print("\n❌ ERRO: S3_BUCKET_NAME não está configurado no .env")
    exit(1)

# Configurar cliente S3
boto_config = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    signature_version='s3v4'
)

try:
    s3_client = boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        config=boto_config
    )
    
    print("\n✓ Cliente S3 criado com sucesso")
    
    # Teste 1: Verificar acesso ao bucket
    print("\n" + "=" * 60)
    print("TESTE 1: Verificar acesso ao bucket")
    print("=" * 60)
    
    try:
        s3_client.head_bucket(Bucket=BUCKET)
        print(f"✓ Bucket '{BUCKET}' encontrado e acessível")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"✗ Bucket '{BUCKET}' não encontrado")
        elif error_code == '403':
            print(f"✗ Acesso negado ao bucket '{BUCKET}'")
        else:
            print(f"✗ Erro: {e}")
        exit(1)
    
    # Teste 2: Listar objetos (se houver)
    print("\n" + "=" * 60)
    print("TESTE 2: Listar objetos no bucket")
    print("=" * 60)
    
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET, MaxKeys=5)
        
        if 'Contents' in response:
            print(f"✓ Encontrados {len(response['Contents'])} objetos (mostrando primeiros 5):")
            for obj in response['Contents'][:5]:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("ℹ Bucket está vazio (sem objetos)")
    except ClientError as e:
        print(f"✗ Erro ao listar objetos: {e}")
    
    # Teste 3: Gerar URL pré-assinada de upload
    print("\n" + "=" * 60)
    print("TESTE 3: Gerar URL pré-assinada de upload")
    print("=" * 60)
    
    try:
        test_key = "test/test-file.pdf"
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": test_key,
                "ContentType": "application/pdf"
            },
            ExpiresIn=300,
        )
        print(f"✓ URL pré-assinada de upload gerada com sucesso")
        print(f"   Key: {test_key}")
        print(f"   URL: {presigned_url[:80]}...")
    except ClientError as e:
        print(f"✗ Erro ao gerar URL de upload: {e}")
    
    # Teste 4: Gerar URL pré-assinada de download
    print("\n" + "=" * 60)
    print("TESTE 4: Gerar URL pré-assinada de download")
    print("=" * 60)
    
    try:
        # Usar o primeiro objeto do bucket, se houver
        response = s3_client.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
        
        if 'Contents' in response:
            first_key = response['Contents'][0]['Key']
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": BUCKET,
                    "Key": first_key
                },
                ExpiresIn=300,
            )
            print(f"✓ URL pré-assinada de download gerada com sucesso")
            print(f"   Key: {first_key}")
            print(f"   URL: {presigned_url[:80]}...")
        else:
            print("ℹ Não há objetos no bucket para testar download")
    except ClientError as e:
        print(f"✗ Erro ao gerar URL de download: {e}")
    
    # Teste 5: Verificar configuração CORS
    print("\n" + "=" * 60)
    print("TESTE 5: Verificar configuração CORS")
    print("=" * 60)
    
    try:
        cors = s3_client.get_bucket_cors(Bucket=BUCKET)
        print("✓ CORS configurado:")
        for i, rule in enumerate(cors['CORSRules'], 1):
            print(f"\n   Regra {i}:")
            print(f"   - Métodos permitidos: {', '.join(rule.get('AllowedMethods', []))}")
            print(f"   - Origens permitidas: {', '.join(rule.get('AllowedOrigins', []))}")
            print(f"   - Headers permitidos: {', '.join(rule.get('AllowedHeaders', []))}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchCORSConfiguration':
            print("⚠ CORS não está configurado no bucket")
            print("\nPara configurar CORS, adicione a seguinte configuração no console AWS:")
            print("""
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
            """)
        else:
            print(f"✗ Erro ao verificar CORS: {e}")
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    print("\n✓ Todos os testes básicos foram concluídos!")
    print("\nPróximos passos:")
    print("1. Certifique-se de que o CORS está configurado (veja Teste 5)")
    print("2. Execute a aplicação: python app.py")
    print("3. Acesse: http://localhost:8000")
    print("4. Verifique o health check: http://localhost:8000/health")
    
except Exception as e:
    print(f"\n❌ ERRO CRÍTICO: {e}")
    print("\nVerifique:")
    print("1. Suas credenciais AWS no arquivo .env")
    print("2. Se você está usando credenciais temporárias (ASIA...), inclua AWS_SESSION_TOKEN")
    print("3. Se o nome do bucket está correto")
    print("4. Se as permissões IAM estão configuradas corretamente")
    exit(1)
