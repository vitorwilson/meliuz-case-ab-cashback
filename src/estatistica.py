"""Testes estatísticos em stdlib puro (sem scipy/pandas).

Welch t-test com p-valor bicaudal via função beta incompleta regularizada
(Numerical Recipes, 3ª ed., §6.4) e IC bootstrap para diferença de médias.
Stdlib puro para a solução rodar em qualquer Python 3 sem instalação.
"""
from __future__ import annotations

import math
import random
import statistics

N_REAMOSTRAS_BOOTSTRAP = 10_000
SEMENTE_BOOTSTRAP = 42  # seed fixa: mesma análise, mesmo resultado


def welch_pvalor(x: list[float], y: list[float]) -> float:
    """p-valor bicaudal do teste t de Welch (H0: médias iguais).

    Ex.: welch_pvalor([10, 12, 14, 16, 18], [8, 10, 12, 14, 16]) ≈ 0.347
    """
    n1, n2 = len(x), len(y)
    if n1 < 2 or n2 < 2:
        return 1.0
    m1, m2 = statistics.mean(x), statistics.mean(y)
    v1, v2 = statistics.variance(x), statistics.variance(y)
    if v1 == 0 and v2 == 0:
        return 1.0 if m1 == m2 else 0.0
    t = (m1 - m2) / math.sqrt(v1 / n1 + v2 / n2)
    gl = _graus_liberdade_welch(v1, v2, n1, n2)
    return _beta_regularizada(gl / 2, 0.5, gl / (gl + t * t))


def t_pareado_pvalor(diferencas: list[float]) -> float:
    """p-valor bicaudal do teste t pareado (H0: média das diferenças = 0).

    Usado quando as variantes rodam nas mesmas datas: parear por dia
    remove o ruído de calendário comum a todas elas.
    Ex.: t_pareado_pvalor([1, 2, 3, 4, 5]) ≈ 0.013
    """
    n = len(diferencas)
    if n < 2:
        return 1.0
    media = statistics.mean(diferencas)
    desvio = statistics.stdev(diferencas)
    if desvio == 0:
        return 1.0 if media == 0 else 0.0
    t = media / (desvio / math.sqrt(n))
    gl = n - 1
    return _beta_regularizada(gl / 2, 0.5, gl / (gl + t * t))


def _graus_liberdade_welch(v1: float, v2: float, n1: int, n2: int) -> float:
    a, b = v1 / n1, v2 / n2
    return (a + b) ** 2 / (a**2 / (n1 - 1) + b**2 / (n2 - 1))


def ic_bootstrap_diferenca(
    x: list[float],
    y: list[float],
    n_reamostras: int = N_REAMOSTRAS_BOOTSTRAP,
    semente: int = SEMENTE_BOOTSTRAP,
) -> tuple[float, float]:
    """IC 95% (percentil) para mean(x) − mean(y), determinístico pela seed.

    Ex.: ic_bootstrap_diferenca(serie_a, serie_b) -> (120.4, 980.7)
    """
    rng = random.Random(semente)
    diferencas = sorted(
        _media_reamostra(x, rng) - _media_reamostra(y, rng)
        for _ in range(n_reamostras)
    )
    return (
        diferencas[int(0.025 * n_reamostras)],
        diferencas[int(0.975 * n_reamostras)],
    )


def _media_reamostra(valores: list[float], rng: random.Random) -> float:
    n = len(valores)
    return statistics.mean(valores[rng.randrange(n)] for _ in range(n))


def ic_bootstrap_media(
    valores: list[float],
    n_reamostras: int = N_REAMOSTRAS_BOOTSTRAP,
    semente: int = SEMENTE_BOOTSTRAP,
) -> tuple[float, float]:
    """IC 95% (percentil) para a média de uma série — usado nas diferenças pareadas.

    Ex.: ic_bootstrap_media(diferencas_diarias) -> (390.2, 640.8)
    """
    rng = random.Random(semente)
    medias = sorted(_media_reamostra(valores, rng) for _ in range(n_reamostras))
    return (
        medias[int(0.025 * n_reamostras)],
        medias[int(0.975 * n_reamostras)],
    )


def _beta_regularizada(a: float, b: float, x: float) -> float:
    """I_x(a, b): beta incompleta regularizada."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1 - x)
    )
    bt = math.exp(ln_bt)
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def _betacf(a: float, b: float, x: float) -> float:
    """Fração contínua da beta incompleta (Lentz)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 / _proteger(1.0 - qab * x / qap)
    h = d
    for m in range(1, 201):
        m2 = 2 * m
        h, d, c = _passo_betacf(h, d, c, m * (b - m) * x / ((qam + m2) * (a + m2)))
        h, d, c = _passo_betacf(
            h, d, c, -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        )
        if abs(d * c - 1.0) < 3e-14:
            break
    return h


def _passo_betacf(
    h: float, d: float, c: float, aa: float
) -> tuple[float, float, float]:
    d = _proteger(1.0 + aa * d)
    c = _proteger(1.0 + aa / c)
    return h * (1.0 / d) * c, 1.0 / d, c


def _proteger(valor: float) -> float:
    return valor if abs(valor) > 1e-300 else 1e-300
