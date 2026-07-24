import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from bank_receipt_extractor.integration import extract_receipt


def main():
    if len(sys.argv) < 2:
        print("Usage: python usage_example.py <receipt_file_path>")
        print("Example: python usage_example.py ~/Downloads/receipt.pdf")
        sys.exit(1)
    arquivo = sys.argv[1]
    path = Path(arquivo)
    if not path.exists():
        print(f"Error: File not found: {arquivo}")
        sys.exit(1)
    print(f"Processing: {arquivo}")
    print("-" * 40)

    resultado = extract_receipt(str(path))
    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
    if "erro" in resultado:
        print("\nExtraction failed")
        sys.exit(1)
    else:
        print(f"\nExtraction successful!")
        print(f"   Type: {resultado.get('tipo', 'N/A')}")
        print(f"   Amount: R$ {resultado.get('valor', 'N/A')}")


if __name__ == "__main__":
    main()