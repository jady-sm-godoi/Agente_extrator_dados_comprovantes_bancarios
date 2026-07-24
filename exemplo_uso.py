import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agente_extrator.integration import extrair_comprovante


def main():
    if len(sys.argv) < 2:
        print("Uso: python exemplo_uso.py <caminho_do_comprovante>")
        print("Exemplo: python exemplo_uso.py ~/Downloads/comprovante.pdf")
        sys.exit(1)

    arquivo = sys.argv[1]
    path = Path(arquivo)

    if not path.exists():
        print(f"Erro: Arquivo não encontrado: {arquivo}")
        sys.exit(1)

    print(f"Processando: {arquivo}")
    print("-" * 40)

    resultado = extrair_comprovante(str(path))

    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))

    if "erro" in resultado:
        print("\n❌ Falha na extração")
        sys.exit(1)
    else:
        print(f"\n✅ Extração concluída!")
        print(f"   Tipo: {resultado.get('tipo', 'N/A')}")
        print(f"   Valor: R$ {resultado.get('valor', 'N/A')}")


if __name__ == "__main__":
    main()
