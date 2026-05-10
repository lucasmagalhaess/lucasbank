import requests
import json
import functions_framework
from datetime import datetime, timezone
from google.cloud import storage

GCS_BUCKET = "lucasbank-pipeline-data-lake"
BACKEND_URL = "https://ubiquitous-doodle-px7prv6rvx627vrx-8000.app.github.dev"

def get_all_clientes():
    res = requests.get(f"{BACKEND_URL}/clientes", timeout=30)
    res.raise_for_status()
    return res.json()["clientes"]

def get_extrato(cliente_id):
    res = requests.get(f"{BACKEND_URL}/clientes/{cliente_id}/extrato", timeout=30)
    res.raise_for_status()
    return res.json()["transacoes"]

def get_cliente(cliente_id):
    res = requests.get(f"{BACKEND_URL}/clientes/{cliente_id}", timeout=30)
    res.raise_for_status()
    return res.json()

def save_to_gcs(data, filename):
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, default=str, indent=2),
        content_type="application/json"
    )
    print(f"Salvo no GCS: {filename}")

@functions_framework.http
def extract_lucasbank(request):
    try:
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")

        print("Iniciando extracao do LucasBank...")
        clientes = get_all_clientes()
        print(f"Clientes encontrados: {len(clientes)}")

        all_transacoes = []
        clientes_data = []

        for c in clientes:
            cliente = get_cliente(c["id"])
            clientes_data.append({
                "id": cliente["id"],
                "nome": cliente["nome"],
                "saldo": cliente["saldo"],
                "extraction_date": today,
                "extraction_timestamp": timestamp
            })

            transacoes = get_extrato(c["id"])
            for t in transacoes:
                all_transacoes.append({
                    **t,
                    "cliente_id": c["id"],
                    "cliente_nome": c["nome"],
                    "extraction_date": today,
                    "extraction_timestamp": timestamp
                })

        payload = {
            "extraction_date": today,
            "extraction_timestamp": timestamp,
            "total_clientes": len(clientes_data),
            "total_transacoes": len(all_transacoes),
            "clientes": clientes_data,
            "transacoes": all_transacoes
        }

        filename = f"bronze/lucasbank/{today}/data_{timestamp.replace(':', '-')}.json"
        save_to_gcs(payload, filename)

        print(f"Extracao concluida! {len(all_transacoes)} transacoes extraidas.")
        return {"status": "success", "transacoes": len(all_transacoes), "clientes": len(clientes_data), "file": filename}, 200

    except Exception as e:
        print(f"Erro: {e}")
        return {"status": "error", "message": str(e)}, 500
