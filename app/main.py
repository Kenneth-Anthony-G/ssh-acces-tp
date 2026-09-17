from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import json
import socket


app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


SOCKET_PATH = "/run/ssh-access/ssh-access.sock"


def send_to_daemon(request_data: dict) -> dict:
    """
    Envoie une requête JSON au daemon via le socket Unix
    et retourne sa réponse.
    """

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        client.connect(SOCKET_PATH)

        data = json.dumps(request_data).encode("utf-8")
        client.sendall(data)

        response = client.recv(65536)

        if not response:
            return {
                "success": False,
                "message": "Le daemon n'a retourné aucune réponse."
            }

        return json.loads(response.decode("utf-8"))

    except PermissionError:
        return {
            "success": False,
            "message": "Permission refusée pour accéder au socket Unix."
        }

    except FileNotFoundError:
        return {
            "success": False,
            "message": "Le socket Unix n'existe pas."
        }

    except ConnectionRefusedError:
        return {
            "success": False,
            "message": "Le daemon n'accepte pas les connexions."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Réponse JSON invalide du daemon."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur de communication : {e}"
        }

    finally:
        client.close()


# ==========================================
# Page principale
# ==========================================

@app.get("/")
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "success": None,
            "error": None,
        },
    )


# ==========================================
# Création d'un accès SSH
# ==========================================

@app.post("/request-access")
async def request_access(
    request: Request,
    login: str = Form(...),
    public_key: str = Form(...),
):

    login = login.strip()
    public_key = public_key.strip()

    if not login or not public_key:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "success": None,
                "error": "Le login et la clé publique sont obligatoires.",
            },
        )

    daemon_request = {
        "action": "create_user",
        "login": login,
        "public_key": public_key,
    }

    result = send_to_daemon(daemon_request)

    if result.get("success"):

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "success": result.get("message"),
                "error": None,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "success": None,
            "error": result.get("message"),
        },
    )


# ==========================================
# Page de monitoring
# ==========================================

@app.get("/monitoring")
async def monitoring(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="monitoring.html",
        context={
            "monitoring": None,
            "error": None,
        },
    )


# ==========================================
# API monitoring
# ==========================================

@app.get("/api/monitoring")
async def monitoring_api():

    daemon_request = {
        "action": "monitoring"
    }

    result = send_to_daemon(daemon_request)

    if result.get("success"):

        return JSONResponse(
            content=result
        )

    return JSONResponse(
        status_code=500,
        content=result
    )
