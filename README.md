# SSH Access Manager

Application FastAPI minimale permettant de saisir un login et une clé publique SSH.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Puis ouvrir `http://IP_DE_LA_VM:8000`.

Cette première version ne réalise aucune opération root.
