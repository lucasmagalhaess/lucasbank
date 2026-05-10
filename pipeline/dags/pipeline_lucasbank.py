from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests

EXTRACT_URL = "https://us-central1-lucasbank-pipeline.cloudfunctions.net/extract-lucasbank"
TRANSFORM_URL = "https://us-central1-lucasbank-pipeline.cloudfunctions.net/transform-lucasbank"

default_args = {
    'owner': 'lucas',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'pipeline_lucasbank',
    default_args=default_args,
    description='Pipeline LucasBank — PostgreSQL para BigQuery via Cloud Functions',
    schedule_interval='0 */6 * * *',
    catchup=False,
    tags=['lucasbank', 'fintech', 'cloud-functions', 'bigquery', 'gcp'],
) as dag:

    def extract_task(**context):
        print(f"Chamando Cloud Function: {EXTRACT_URL}")
        response = requests.get(EXTRACT_URL, timeout=180)
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "success":
            raise Exception(f"Extracao falhou: {result}")
        filename = result["file"]
        context['task_instance'].xcom_push(key='filename', value=filename)
        print(f"Extraidos: {result['clientes']} clientes, {result['transacoes']} transacoes")
        return filename

    def transform_task(**context):
        filename = context['task_instance'].xcom_pull(key='filename', task_ids='extrair_lucasbank')
        response = requests.post(TRANSFORM_URL, json={"filename": filename}, timeout=180)
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "success":
            raise Exception(f"Transformacao falhou: {result}")
        print(f"Carregados: {result['clientes']} clientes, {result['transacoes']} transacoes")
        return result

    t1 = PythonOperator(task_id='extrair_lucasbank', python_callable=extract_task, provide_context=True)
    t2 = PythonOperator(task_id='transformar_e_carregar_bigquery', python_callable=transform_task, provide_context=True)

    t1 >> t2
