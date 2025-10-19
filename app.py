# app.py
import logging
import os
import json
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do ambiente
REGION = os.environ.get("AWS_REGION", "us-east-1")
BUCKET = os.environ.get("S3_BUCKET_NAME")
PRESIGN_UPLOAD_EXPIRES = int(os.environ.get("PRESIGNED_URL_EXPIRATION_UPLOAD", "900"))
PRESIGN_DOWNLOAD_EXPIRES = int(os.environ.get("PRESIGNED_URL_EXPIRATION_DOWNLOAD", "3600"))
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Validar configurações obrigatórias
if not BUCKET:
    raise ValueError("S3_BUCKET_NAME não está configurado no arquivo .env")

# Configurar cliente S3
boto_config = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    signature_version='s3v4'
)

s3_client = boto3.client(
    "s3",
    region_name=REGION,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
    config=boto_config
)

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pdf-manager-api")

# Criar diretório para metadados localmente
METADATA_DIR = Path("data")
METADATA_DIR.mkdir(exist_ok=True)
METADATA_FILE = METADATA_DIR / "documents_metadata.json"

# Inicializar arquivo de metadados se não existir
if not METADATA_FILE.exists():
    with open(METADATA_FILE, 'w') as f:
        json.dump({}, f)

# FastAPI app
app = FastAPI(
    title="PDF Manager API",
    description="API para gerenciamento de documentos PDF no S3",
    version="1.0.0"
)

# CORS - ajustar origins para produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Modelos Pydantic
class PresignUploadRequest(BaseModel):
    filename: str
    contentType: str = "application/pdf"

class PresignUploadResponse(BaseModel):
    uploadUrl: str
    documentId: str
    key: str
    expires: int

class PresignDownloadResponse(BaseModel):
    downloadUrl: str
    expires: int

class DocumentMetadata(BaseModel):
    documentId: str
    filename: str
    originalFilename: str
    contentType: str
    sizeBytes: Optional[int] = None
    s3Key: str
    uploadedAt: str
    status: str = "pending"  # pending, uploaded, error

class NotifyUploadRequest(BaseModel):
    documentId: str
    sizeBytes: int
    status: str = "uploaded"


# Funções auxiliares para gerenciar metadados
def load_metadata() -> Dict[str, Any]:
    """Carrega metadados do arquivo JSON"""
    try:
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar metadados: {e}")
        return {}

def save_metadata(data: Dict[str, Any]):
    """Salva metadados no arquivo JSON"""
    try:
        with open(METADATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar metadados: {e}")
        raise

def verify_s3_bucket():
    """Verifica se o bucket S3 existe e está acessível"""
    try:
        s3_client.head_bucket(Bucket=BUCKET)
        logger.info(f"Bucket S3 '{BUCKET}' verificado com sucesso")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            logger.error(f"Bucket '{BUCKET}' não encontrado")
        elif error_code == '403':
            logger.error(f"Acesso negado ao bucket '{BUCKET}'")
        else:
            logger.error(f"Erro ao verificar bucket: {e}")
        return False

# Endpoints da API

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação"""
    logger.info("Iniciando PDF Manager API...")
    logger.info(f"Bucket S3: {BUCKET}")
    logger.info(f"Região: {REGION}")
    
    if verify_s3_bucket():
        logger.info("✓ Bucket S3 acessível")
    else:
        logger.warning("✗ Problema ao acessar bucket S3")

@app.get("/")
def read_root():
    """Endpoint raiz - serve o frontend"""
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    """Health check"""
    bucket_ok = verify_s3_bucket()
    return {
        "status": "ok" if bucket_ok else "degraded",
        "bucket": BUCKET,
        "region": REGION,
        "s3_accessible": bucket_ok
    }

@app.post("/api/presign-upload", response_model=PresignUploadResponse)
async def presign_upload(req: PresignUploadRequest):
    """
    Gera URL pré-assinada para upload de PDF no S3
    """
    try:
        # Validar tipo de arquivo
        if req.contentType != "application/pdf":
            raise HTTPException(
                status_code=400, 
                detail="Apenas arquivos PDF são permitidos"
            )
        
        # Gerar ID único para o documento
        document_id = str(uuid4())
        
        # Gerar nome seguro para o arquivo
        safe_filename = f"{document_id}_{req.filename}"
        s3_key = f"documents/{safe_filename}"
        
        # Gerar URL pré-assinada para upload
        # IMPORTANTE: Não incluir Metadata aqui, pois o frontend teria que enviar
        # esses headers no PUT (x-amz-meta-*), causando erro 403 se não enviar
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": s3_key,
                "ContentType": req.contentType
            },
            ExpiresIn=PRESIGN_UPLOAD_EXPIRES,
        )
        
        # Salvar metadados
        metadata = load_metadata()
        
        metadata[document_id] = {
            "documentId": document_id,
            "filename": safe_filename,
            "originalFilename": req.filename,
            "contentType": req.contentType,
            "s3Key": s3_key,
            "uploadedAt": datetime.utcnow().isoformat(),
            "status": "pending",
            "sizeBytes": None
        }
        
        save_metadata(metadata)
        
        logger.info(f"URL pré-assinada gerada para upload: documentId={document_id}")
        
        return PresignUploadResponse(
            uploadUrl=presigned_url,
            documentId=document_id,
            key=s3_key,
            expires=PRESIGN_UPLOAD_EXPIRES
        )
        
    except ClientError as e:
        logger.exception("Erro ao gerar URL pré-assinada")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar URL de upload: {str(e)}"
        )
    except Exception as e:
        logger.exception("Erro inesperado")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notify-upload")
async def notify_upload(req: NotifyUploadRequest):
    """
    Endpoint para o frontend notificar que o upload foi concluído
    Atualiza os metadados do documento
    """
    try:
        metadata = load_metadata()
        
        if req.documentId not in metadata:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Atualizar metadados
        metadata[req.documentId]["status"] = req.status
        metadata[req.documentId]["sizeBytes"] = req.sizeBytes
        
        save_metadata(metadata)
        
        logger.info(f"Upload notificado: documentId={req.documentId}, status={req.status}")
        
        return {
            "message": "Upload confirmado com sucesso",
            "documentId": req.documentId,
            "status": req.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao processar notificação de upload")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def list_documents():
    """
    Lista todos os documentos
    """
    try:
        metadata = load_metadata()
        
        documents = [
            DocumentMetadata(**doc) 
            for doc in metadata.values()
            if doc.get("status") == "uploaded"
        ]
        
        # Ordenar por data de upload (mais recente primeiro)
        documents.sort(key=lambda x: x.uploadedAt, reverse=True)
        
        logger.info(f"Listando documentos: count={len(documents)}")
        
        return {"documents": documents}
        
    except Exception as e:
        logger.exception("Erro ao listar documentos")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/download", response_model=PresignDownloadResponse)
async def get_download_url(document_id: str):
    """
    Gera URL pré-assinada para download de um documento
    """
    try:
        metadata = load_metadata()
        
        if document_id not in metadata:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        doc = metadata[document_id]
        
        # Encoding do filename para suportar caracteres não-ASCII
        # RFC 5987: filename*=UTF-8''encoded-filename
        encoded_filename = quote(doc["originalFilename"])
        
        # Gerar URL pré-assinada para download
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": BUCKET,
                "Key": doc["s3Key"],
                # Usa formato RFC 5987 para suportar caracteres especiais
                "ResponseContentDisposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            },
            ExpiresIn=PRESIGN_DOWNLOAD_EXPIRES,
        )
        
        logger.info(f"URL pré-assinada gerada para download: documentId={document_id}")
        
        return PresignDownloadResponse(
            downloadUrl=presigned_url,
            expires=PRESIGN_DOWNLOAD_EXPIRES
        )
        
    except ClientError as e:
        logger.exception("Erro ao gerar URL de download")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar URL de download: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Deleta um documento do S3 e remove seus metadados
    """
    try:
        metadata = load_metadata()
        
        if document_id not in metadata:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        doc = metadata[document_id]
        
        # Deletar do S3
        try:
            s3_client.delete_object(Bucket=BUCKET, Key=doc["s3Key"])
            logger.info(f"Arquivo deletado do S3: {doc['s3Key']}")
        except ClientError as e:
            logger.warning(f"Erro ao deletar do S3 (continuando): {e}")
        
        # Remover metadados
        del metadata[document_id]
        save_metadata(metadata)
        
        logger.info(f"Documento deletado: documentId={document_id}")
        
        return {
            "message": "Documento deletado com sucesso",
            "documentId": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao deletar documento")
        raise HTTPException(status_code=500, detail=str(e))

# Servir arquivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
