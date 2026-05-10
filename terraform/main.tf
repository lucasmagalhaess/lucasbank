terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file("lucasbank-pipeline-d3465cd5baaf.json")
  project     = var.project_id
  region      = var.region
}

resource "google_storage_bucket" "data_lake" {
  name          = "${var.project_id}-data-lake"
  location      = var.region
  force_destroy = true
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id = "analytics"
  location   = var.region
}

resource "google_bigquery_table" "transacoes" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "transacoes"
  deletion_protection = false

  schema = jsonencode([
    { name = "id", type = "INTEGER" },
    { name = "cliente_id", type = "INTEGER" },
    { name = "cliente_nome", type = "STRING" },
    { name = "tipo", type = "STRING" },
    { name = "valor", type = "FLOAT" },
    { name = "descricao", type = "STRING" },
    { name = "saldo_anterior", type = "FLOAT" },
    { name = "saldo_posterior", type = "FLOAT" },
    { name = "criado_em", type = "STRING" },
    { name = "extraction_date", type = "STRING" },
    { name = "extraction_timestamp", type = "STRING" }
  ])
}

resource "google_bigquery_table" "clientes" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "clientes"
  deletion_protection = false

  schema = jsonencode([
    { name = "id", type = "INTEGER" },
    { name = "nome", type = "STRING" },
    { name = "saldo", type = "FLOAT" },
    { name = "extraction_date", type = "STRING" },
    { name = "extraction_timestamp", type = "STRING" }
  ])
}
