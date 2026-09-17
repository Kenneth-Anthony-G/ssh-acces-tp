#!/usr/bin/env python3

import json
import os
import socket
import subprocess
import grp


SOCKET_PATH = "/run/ssh-access/ssh-access.sock"

ADD_USER_SCRIPT = "/home/edem/ssh-access/scripts/add_ssh_user.sh"
MONITORING_SCRIPT = "/home/edem/ssh-access/scripts/monitoring.sh"

SOCKET_GROUP = "sshaccess"


def run_script(script_path, arguments=None):
    """
    Exécute un script Bash et retourne son résultat.
    """

    if arguments is None:
        arguments = []

    try:
        result = subprocess.run(
            [script_path, *arguments],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "success": False,
                "message": result.stderr.strip() or "Le script a échoué."
            }

        return {
            "success": True,
            "output": result.stdout.strip()
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Le script a dépassé le délai d'exécution."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur d'exécution : {e}"
        }


def handle_create_user(login, public_key):
    """
    Demande au script Bash de créer un utilisateur SSH.
    """

    if not login or not public_key:
        return {
            "success": False,
            "message": "Login ou clé publique manquant."
        }

    result = run_script(
        ADD_USER_SCRIPT,
        [login, public_key]
    )

    if not result["success"]:
        return result

    return {
        "success": True,
        "message": result["output"]
    }


def handle_monitoring():
    """
    Exécute le script de monitoring et retourne
    les données JSON au client.
    """

    result = run_script(MONITORING_SCRIPT)

    if not result["success"]:
        return result

    try:
        monitoring_data = json.loads(result["output"])

        return {
            "success": True,
            "data": monitoring_data
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Le script de monitoring a retourné un JSON invalide."
        }


def handle_request(data):
    """
    Analyse une requête reçue depuis le socket Unix.
    """

    try:
        request = json.loads(data)

    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Requête JSON invalide."
        }

    action = request.get("action")

    # ==============================
    # Création utilisateur SSH
    # ==============================

    if action == "create_user":

        login = request.get("login")
        public_key = request.get("public_key")

        return handle_create_user(
            login,
            public_key
        )

    # ==============================
    # Monitoring
    # ==============================

    if action == "monitoring":

        return handle_monitoring()

    # ==============================
    # Action inconnue
    # ==============================

    return {
        "success": False,
        "message": "Action inconnue."
    }


def start_server():

    # Suppression d'un ancien socket
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    server = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    )

    server.bind(SOCKET_PATH)

    # Permissions du socket
    os.chmod(
        SOCKET_PATH,
        0o660
    )

    # Groupe sshaccess
    gid = grp.getgrnam(SOCKET_GROUP).gr_gid

    os.chown(
        SOCKET_PATH,
        0,
        gid
    )

    server.listen(5)

    print(
        f"Daemon SSH en écoute sur {SOCKET_PATH}",
        flush=True
    )

    while True:

        connection, _ = server.accept()

        with connection:

            try:

                data = connection.recv(65536)

                if not data:
                    continue

                request = data.decode("utf-8")

                print(
                    f"Requête reçue : {request}",
                    flush=True
                )

                response = handle_request(request)

                connection.sendall(
                    json.dumps(response).encode("utf-8")
                )

            except Exception as e:

                response = {
                    "success": False,
                    "message": f"Erreur lors du traitement : {e}"
                }

                connection.sendall(
                    json.dumps(response).encode("utf-8")
                )


if __name__ == "__main__":
    start_server()
