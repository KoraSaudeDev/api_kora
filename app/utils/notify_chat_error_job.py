import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# CONFIGURAÇÕES FIXAS DO GOOGLE CHAT
SERVICE_ACCOUNT_FILE = 'itsmkora-account-file.json'
SCOPES = ['https://www.googleapis.com/auth/chat.messages']
SPACE_ID = 'spaces/AAQAtWGVfq0'
CHAT_API_URL = f'https://chat.googleapis.com/v1/{SPACE_ID}/messages'

def notificar_erro_chat(job_id: int, erro: str, dados: dict = None):
    
    print(f"📣 Função notificar_erro_chat foi chamada para o job {job_id}")
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        if not credentials.valid or credentials.expired:
            credentials.refresh(Request())

        texto = f"🚨 *Erro na Integração* #{job_id}\n"
        texto += f"❌ *Erro:* `{erro}`\n"
        if dados:
            preview = json.dumps(dados, indent=2, ensure_ascii=False)
            texto += f"📦 *Dados:* ```\n{preview[:500]}\n```"

        payload = {"text": texto}
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(CHAT_API_URL, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            print(f"[CHAT] ❌ Falha ao enviar mensagem: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"[CHAT] ⚠️ Falha ao notificar erro no Google Chat: {e}")
