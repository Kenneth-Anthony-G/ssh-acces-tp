#!/bin/bash

set -euo pipefail

# Vérification des arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <login> <cle_publique>" >&2
    exit 1
fi

LOGIN="$1"
PUBLIC_KEY="$2"
RAPPORT="/home/edem/ssh-access/files/rapport_projet_synthese_linux.pdf"

# Vérification du login Linux
if [[ ! "$LOGIN" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
    echo "Erreur : login invalide." >&2
    exit 1
fi

# Vérification basique du format de la clé SSH
if [[ ! "$PUBLIC_KEY" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521)[[:space:]]+[^[:space:]]+ ]]; then
    echo "Erreur : clé publique SSH invalide." >&2
    exit 1
fi

# Vérifier si l'utilisateur existe déjà
if id "$LOGIN" &>/dev/null; then
    echo "Erreur : l'utilisateur '$LOGIN' existe déjà." >&2
    exit 1
fi

# Création du compte Linux
useradd \
    --create-home \
    --shell /bin/bash \
    "$LOGIN"

# Création du dossier SSH
SSH_DIR="/home/$LOGIN/.ssh"

mkdir -p "$SSH_DIR"

# Création du fichier authorized_keys
echo "$PUBLIC_KEY" > "$SSH_DIR/authorized_keys"

# Permissions
chmod 700 "$SSH_DIR"
chmod 600 "$SSH_DIR/authorized_keys"

# Propriétaire
chown -R "$LOGIN:$LOGIN" "$SSH_DIR"

# Copie du fichier de création
cp "$RAPPORT" "/home/$LOGIN/rapport_projet.pdf"

# Propriétaire et permissions
chown "$LOGIN:$LOGIN" "/home/$LOGIN/rapport_projet.pdf"
chmod 644 "/home/$LOGIN/rapport_projet.pdf"

echo "Utilisateur SSH '$LOGIN' créé avec succès."
