# Script para limpar metadados locais
import json
from pathlib import Path

METADATA_FILE = Path("data/documents_metadata.json")

def clear_metadata():
    """Limpa todos os metadados armazenados localmente"""
    print("=" * 60)
    print("LIMPEZA DE METADADOS")
    print("=" * 60)
    
    if not METADATA_FILE.exists():
        print("\n✓ Arquivo de metadados não existe. Nada para limpar.")
        return
    
    # Ler metadados atuais
    with open(METADATA_FILE, 'r') as f:
        data = json.load(f)
    
    # Contar documentos
    total_docs = len(data)
    
    print(f"\nMetadados atuais:")
    print(f"  Total de documentos: {total_docs}")
    
    if total_docs == 0:
        print("\n✓ Não há metadados para limpar.")
        return
    
    # Mostrar detalhes
    print("\nDetalhes:")
    for doc_id, doc in data.items():
        print(f"  - {doc.get('originalFilename', 'N/A')} ({doc.get('sizeBytes', 0)} bytes)")
        print(f"    ID: {doc_id}")
    
    # Confirmar limpeza
    print("\n" + "=" * 60)
    response = input("\n⚠️  ATENÇÃO: Esta ação irá DELETAR todos os metadados locais!\n   Os arquivos no S3 NÃO serão afetados.\n   \n   Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if response.strip().upper() != 'SIM':
        print("\n✓ Operação cancelada. Nenhum dado foi modificado.")
        return
    
    # Limpar metadados
    with open(METADATA_FILE, 'w') as f:
        json.dump({}, f, indent=2)
    
    print("\n✓ Metadados limpos com sucesso!")
    print("\nPróximos passos:")
    print("  - Os metadados foram resetados para um objeto vazio {}")
    print("  - Os arquivos ainda estão no S3 (não foram deletados)")
    print("  - Para deletar arquivos do S3, use o Console AWS ou a interface da aplicação")

if __name__ == "__main__":
    clear_metadata()
