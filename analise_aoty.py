from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ENTRADA = Path("aoty_tratado/aoty_tratado_long.csv")
SAIDA_DIR = Path("aoty_tratado")
TOP_N_GENEROS = 15
FAIXAS = [75, 80, 85, 90, 95]
FAIXAS_LABELS = ["75-80", "80-85", "85-90", "90-95"]


def carregar(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}. Rode tratamento_aoty.py primeiro.")
    df = pd.read_csv(caminho)
    df["faixa_score"] = pd.cut(df["user_score"], bins=FAIXAS, labels=FAIXAS_LABELS, include_lowest=True)
    return df


def generos_mais_frequentes(df: pd.DataFrame, top_n: int) -> list[str]:
    return df["genero"].value_counts().head(top_n).index.tolist()


def montar_heatmap(df: pd.DataFrame, generos: list[str]) -> dict:
    subset = df[df["genero"].isin(generos)]

    # Valor principal da célula: quantidade de álbuns do gênero em cada faixa de nota.
    # Mostra onde a "massa" de álbuns de cada gênero se concentra, o que dá bem
    # mais contraste do que a média (que fica quase constante dentro da própria faixa).
    contagem = subset.pivot_table(index="genero", columns="faixa_score", values="user_score", aggfunc="count", observed=False)
    contagem = contagem.reindex(index=generos, columns=FAIXAS_LABELS)

    # Nota média por célula: mantida como dado secundário, só para contexto.
    tabela = subset.pivot_table(index="genero", columns="faixa_score", values="user_score", aggfunc="mean", observed=False)
    tabela = tabela.reindex(index=generos, columns=FAIXAS_LABELS)

    valores = []
    notas_medias = []
    for genero in generos:
        linha_valor, linha_nota = [], []
        for faixa in FAIXAS_LABELS:
            n = contagem.loc[genero, faixa]
            v = tabela.loc[genero, faixa]
            linha_valor.append(0 if pd.isna(n) else int(n))
            linha_nota.append(None if pd.isna(v) else round(float(v), 2))
        valores.append(linha_valor)
        notas_medias.append(linha_nota)

    return {
        "linhas": [{"codigo": g, "label": g} for g in generos],
        "colunas": [{"codigo": f, "label": f} for f in FAIXAS_LABELS],
        "valores": valores,
        "nota_media_por_celula": notas_medias,
    }


def resumo_por_genero(df: pd.DataFrame, generos: list[str]) -> list[dict]:
    subset = df[df["genero"].isin(generos)]
    agrupado = subset.groupby("genero").agg(
        nota_media=("user_score", "mean"),
        qtd_albuns=("id", "nunique"),
        soma_avaliacoes=("rating_count", "sum"),
    )
    agrupado = agrupado.reindex(generos)
    return [
        {
            "genero": g,
            "nota_media": round(float(agrupado.loc[g, "nota_media"]), 2),
            "qtd_albuns": int(agrupado.loc[g, "qtd_albuns"]),
            "soma_avaliacoes": int(agrupado.loc[g, "soma_avaliacoes"]),
        }
        for g in generos
    ]


def conclusoes(resumo: list[dict]) -> str:
    melhor = max(resumo, key=lambda d: d["nota_media"])
    pior = min(resumo, key=lambda d: d["nota_media"])
    return (
        f"Entre os {len(resumo)} gêneros mais frequentes do top 5000, {melhor['genero']} tem a maior nota "
        f"média de usuários ({melhor['nota_media']}), enquanto {pior['genero']} tem a menor ({pior['nota_media']}). "
        "Como a amostra já é filtrada para os álbuns mais bem avaliados do site, essas diferenças descrevem "
        "posição relativa dentro de um grupo de elite, não a qualidade geral do gênero na música em geral."
    )


def main() -> int:
    df = carregar(ENTRADA)
    generos = generos_mais_frequentes(df, TOP_N_GENEROS)
    heatmap = montar_heatmap(df, generos)
    resumo = resumo_por_genero(df, generos)

    saida = {
        "gerado_em": pd.Timestamp.now().isoformat(),
        "fonte": {"dataset": "AOTY - Top 5000 álbuns", "origem": "albumoftheyear.org"},
        "total_registros_album_genero": int(len(df)),
        "heatmap_genero_x_faixa_score": heatmap,
        "resumo_por_genero": resumo,
        "conclusao": conclusoes(resumo),
        "observacao_metodologica": (
            "O valor de cada célula do heatmap é a quantidade de álbuns do gênero naquela faixa de nota "
            "(mostra onde a nota dos álbuns de cada gênero se concentra). A nota média por célula "
            "também é salva em 'nota_media_por_celula', para contexto."
        ),
    }
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA_DIR / "dados_heatmap.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Heatmap gerado em {caminho.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
