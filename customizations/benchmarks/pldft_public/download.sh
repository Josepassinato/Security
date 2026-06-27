#!/usr/bin/env bash
# Baixa o IBM AML (ealtman2019) HI-Small para /root/datasets/ibm-aml (fora do repo).
# Pré-requisito: token Kaggle novo em ~/.kaggle/access_token (KGAT_…) OU env KAGGLE_API_TOKEN.
set -euo pipefail

DS="ealtman2019/ibm-transactions-for-anti-money-laundering-aml"
DEST="${1:-/root/datasets/ibm-aml}"
SIZE="${2:-Small}"   # Small | Medium | Large

mkdir -p "$DEST"
command -v kaggle >/dev/null || { echo "kaggle CLI ausente: pip3 install -U kaggle"; exit 1; }

for f in "HI-${SIZE}_Trans.csv" "HI-${SIZE}_accounts.csv" "HI-${SIZE}_Patterns.txt"; do
  echo ">> baixando $f"
  kaggle datasets download "$DS" -f "$f" -p "$DEST" --unzip
done

echo ">> pronto em $DEST"
ls -lh "$DEST"
