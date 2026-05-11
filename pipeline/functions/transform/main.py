import json
import functions_framework
from datetime import datetime, timezone
from google.cloud import storage, bigquery

GCS_BUCKET = "lucasbank-pipeline-data-lake"
BQ_PROJECT = "lucasbank-pipeline"
BQ_DATASET = "analytics"

def read_from_gcs(filename):
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(filename)
    return json.loads(blob.download_as_string())

def get_existing_ids(table_id, id_field):
    client = bigquery.Client()
    full_table = f"{BQ_PROJECT}.{BQ_DATASET}.{table_id}"
    try:
        query = f"SELECT DISTINCT {id_field} FROM `{full_table}`"
        result = client.query(query).result()
        return {row[id_field] for row in result}
    except Exception:
        return set()

def load_to_bigquery(table_id, rows):
    if not rows:
        print(f"Nenhum registro novo para {table_id}")
        return
    client = bigquery.Client()
    full_table = f"{BQ_PROJECT}.{BQ_DATASET}.{table_id}"
    errors = client.insert_rows_json(full_table, rows)
    if errors:
        raise Exception(f"Erros BigQuery: {errors}")
    print(f"Inseridos {len(rows)} registros novos em {full_table}")

@functions_framework.http
def transform_lucasbank(request):
    try:
        request_json = request.get_json(silent=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = request_json.get("filename") if request_json else None

        if not filename:
            filename = f"bronze/lucasbank/{today}/test.json"

        print(f"Lendo arquivo: {filename}")
        data = read_from_gcs(filename)

        clientes = data.get("clientes", [])
        transacoes = data.get("transacoes", [])

        # Clientes — atualiza sempre (WRITE_TRUNCATE por cliente_id)
        existing_cliente_ids = get_existing_ids("clientes", "id")
        novos_clientes = [c for c in clientes if c["id"] not in existing_cliente_ids]
        load_to_bigquery("clientes", novos_clientes)

        # Transacoes — insere só as novas pelo id
        existing_transacao_ids = get_existing_ids("transacoes", "id")
        novas_transacoes = []
        for t in transacoes:
            if t.get("id") not in existing_transacao_ids:
                novas_transacoes.append({
                    "id": t.get("id"),
                    "cliente_id": t.get("cliente_id"),
                    "cliente_nome": t.get("cliente_nome"),
                    "tipo": t.get("tipo"),
                    "valor": float(t.get("valor", 0)),
                    "descricao": t.get("descricao", ""),
                    "saldo_anterior": float(t.get("saldo_anterior", 0)),
                    "saldo_posterior": float(t.get("saldo_posterior", 0)),
                    "criado_em": str(t.get("criado_em", "")),
                    "extraction_date": t.get("extraction_date"),
                    "extraction_timestamp": t.get("extraction_timestamp")
                })

        load_to_bigquery("transacoes", novas_transacoes)

        return {
            "status": "success",
            "clientes_novos": len(novos_clientes),
            "transacoes_novas": len(novas_transacoes)
        }, 200

    except Exception as e:
        print(f"Erro: {e}")
        return {"status": "error", "message": str(e)}, 500
