"""
Tratamento inicial do dataset AOTY (Album of the Year).

Mesma lógica do tratamento.py do projeto projpisi3-ufrpe, adaptada às
colunas do dataset de música:
1. Conversão de rating_count (texto "28,594 ratings") para número.
2. Extração de ano e década a partir de release_date.
3. "Explosão" da coluna genres (um álbum pode ter vários gêneros) em
   formato longo, uma linha por (álbum, gênero) — necessário para
   qualquer análise agrupada por gênero.
4. Geração de metadados e estatísticas antes/depois, no mesmo espírito
   do metadados_base.json do projeto original.

Saídas (em aoty_tratado/):
- aoty_tratado.csv       -> uma linha por álbum (wide), colunas limpas
- aoty_tratado_long.csv  -> uma linha por (álbum, gênero), para agrupar por gênero
- metadados.json         -> dicionário de variáveis e decisões de tratamento

Dependências:
    pip install pandas
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ENTRADA = Path("aoty.csv")
SAIDA_DIR = Path("aoty_tratado")


def ler_dataset(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    return pd.read_csv(caminho)


def limpar_rating_count(df: pd.DataFrame) -> pd.DataFrame:
    # "28,594 ratings" -> 28594 (int)
    df = df.copy()
    df["rating_count"] = (
        df["rating_count"]
        .astype(str)
        .apply(lambda v: re.sub(r"[^0-9]", "", v))
        .replace("", "0")
        .astype(int)
    )
    return df


def extrair_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    datas = pd.to_datetime(df["release_date"], format="%B %d, %Y", errors="coerce")
    df["release_year"] = datas.dt.year
    df["decade"] = (df["release_year"] // 10 * 10).astype("Int64")
    return df


def explodir_generos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["genero"] = df["genres"].str.split(",\\s*")
    longo = df.explode("genero")
    longo["genero"] = longo["genero"].str.strip()
    return longo


def gerar_metadados(original: pd.DataFrame, tratado: pd.DataFrame, longo: pd.DataFrame, pasta_saida: Path) -> None:
    metadata = {
        "fonte": {
            "dataset": "Album of the Year - Top 5000",
            "origem": "AOTY (albumoftheyear.org)",
            "observacao": "Amostra enviesada para os álbuns mais bem avaliados; não representa todo o catálogo musical.",
        },
        "dimensoes": {
            "albuns_originais": int(len(original)),
            "albuns_tratados": int(len(tratado)),
            "linhas_formato_longo_album_genero": int(len(longo)),
            "generos_distintos": int(longo["genero"].nunique()),
            "artistas_distintos": int(tratado["artist"].nunique()),
        },
        "variaveis": {
            "user_score": {"tipo": "contínua (0-100)", "descricao": "Nota média dada pelos usuários do AOTY."},
            "rating_count": {"tipo": "contínua", "descricao": "Quantidade de avaliações recebidas pelo álbum."},
            "release_year": {"tipo": "ordinal", "descricao": "Ano de lançamento extraído de release_date."},
            "decade": {"tipo": "ordinal", "descricao": "Década de lançamento (ex: 2010)."},
            "genero": {"tipo": "categórica (multivalorada)", "descricao": "Um álbum pode pertencer a mais de um gênero; dado 'explodido' em aoty_tratado_long.csv."},
        },
        "motivos_do_tratamento": [
            {"etapa": "Limpeza de rating_count", "motivo": "Converter texto em número para permitir soma/média."},
            {"etapa": "Extração de ano/década", "motivo": "Permitir agrupar e comparar álbuns ao longo do tempo."},
            {"etapa": "Explosão de gêneros", "motivo": "Cada álbum pode ter múltiplos gêneros; para analisar por gênero, cada combinação (álbum, gênero) precisa virar uma linha própria."},
        ],
    }
    (pasta_saida / "metadados.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def executar_tratamento(entrada: Path = ENTRADA, pasta_saida: Path = SAIDA_DIR) -> None:
    original = ler_dataset(entrada)
    tratado = limpar_rating_count(original)
    tratado = extrair_data(tratado)
    longo = explodir_generos(tratado)

    pasta_saida.mkdir(parents=True, exist_ok=True)
    tratado.to_csv(pasta_saida / "aoty_tratado.csv", index=False)
    longo.to_csv(pasta_saida / "aoty_tratado_long.csv", index=False)
    gerar_metadados(original, tratado, longo, pasta_saida)

    print("Tratamento concluído.")
    print(f"Álbuns: {len(tratado):,}")
    print(f"Linhas no formato longo (álbum x gênero): {len(longo):,}")
    print(f"Resultados em: {pasta_saida.resolve()}")


if __name__ == "__main__":
    executar_tratamento()
