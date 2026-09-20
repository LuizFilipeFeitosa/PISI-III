from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ENTRADA = Path("aoty_tratado/aoty_tratado.csv")
SAIDA_DIR = Path("aoty_tratado")


def main() -> int:
    df = pd.read_csv(ENTRADA)

    # Distribuições
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].hist(df["user_score"], bins=20, color="#1F3A5F")
    axes[0].set_title("Distribuição de user_score")
    axes[0].set_xlabel("Nota")
    axes[0].set_ylabel("Qtd de álbuns")

    axes[1].hist(df["rating_count"], bins=40, color="#B23A2E")
    axes[1].set_title("Distribuição de rating_count")
    axes[1].set_xlabel("Qtd de avaliações")
    axes[1].set_yscale("log")
    plt.tight_layout()
    plt.savefig("distribuicoes.png", dpi=130)

    # Correlação
    correlacao = round(float(df["user_score"].corr(df["rating_count"])), 3)

    # Tendência por década
    tendencia = df.groupby("decade")["user_score"].agg(["mean", "count"]).round(2)
    tendencia_dict = {
        str(int(decada)): {"nota_media": float(row["mean"]), "qtd_albuns": int(row["count"])}
        for decada, row in tendencia.iterrows()
    }

    resultado = {
        "estatisticas_descritivas": {
            "user_score": df["user_score"].describe().round(2).to_dict(),
            "rating_count": df["rating_count"].describe().round(2).to_dict(),
        },
        "correlacao_user_score_rating_count": correlacao,
        "tendencia_por_decada": tendencia_dict,
        "interpretacao": {
            "correlacao": (
                "Correlação positiva moderada: álbuns mais avaliados tendem a ter nota um pouco mais alta, "
                "mas a relação está longe de ser forte — quantidade de avaliações não é um bom substituto para nota."
            ),
            "tendencia_temporal": (
                "A nota média cai nas décadas mais recentes (2010: 79.5; 2020: 78.3) frente a décadas "
                "anteriores (~81-82). Álbuns antigos que chegaram ao top 5000 já passaram por um filtro "
                "de tempo (só os consagrados permanecem bem avaliados); álbuns recentes ainda estão "
                "entrando e sendo reavaliados. Relevante para o recomendador: nota bruta favorece obras "
                "antigas, pode ser preciso normalizar por época."
            ),
        },
    }

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    (SAIDA_DIR / "eda_complementar.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Correlação user_score x rating_count:", correlacao)
    print(tendencia)
    print("Salvo em aoty_tratado/eda_complementar.json e distribuicoes.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
