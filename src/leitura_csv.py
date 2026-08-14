"""Leitura e validação dos CSVs de testes A/B de cashback.

Schema esperado (enunciado do case):
Data,Grupos de usuários,Parceiro,compradores,comissão,cashback,vendas totais

Erros de schema/parse abortam com ValueError; problemas de qualidade
(datas faltantes, duplicatas, valores negativos) viram alertas.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta

COLUNAS_ESPERADAS = [
    "Data", "Grupos de usuários", "Parceiro",
    "compradores", "comissão", "cashback", "vendas totais",
]
MAX_ALERTAS_POR_TIPO = 3


@dataclass(frozen=True)
class Observacao:
    """Uma linha do dataset: métricas de um grupo em um dia."""
    data: date
    grupo: str
    parceiro: str
    compradores: int
    comissao: float
    cashback: float
    vendas: float


@dataclass
class Dataset:
    observacoes: list[Observacao]
    alertas: list[str] = field(default_factory=list)


def parse_real(valor: str) -> float:
    """Converte string monetária pt-BR em float.

    >>> parse_real("R$ 10.273")
    10273.0
    >>> parse_real("R$ 1.234,56")
    1234.56
    """
    texto = valor.strip().replace("R$", "").replace(" ", "")
    if not texto:
        raise ValueError(
            f"valor monetário vazio; esperado 'R$ 10.273', recebido: {valor!r}"
        )
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1 or (
        texto.count(".") == 1 and len(texto.rsplit(".", 1)[1]) == 3
    ):
        texto = texto.replace(".", "")
    try:
        return float(texto)
    except ValueError:
        raise ValueError(
            f"valor monetário inválido: {valor!r}; esperado 'R$ 10.273'"
        ) from None


def carregar_dataset(caminho: str) -> Dataset:
    """Carrega o CSV, valida schema/valores e anexa alertas de qualidade.

    Ex.: dataset = carregar_dataset("data/dataset_01_parceiroA.csv")
    """
    with open(caminho, encoding="utf-8-sig", newline="") as arq:
        leitor = csv.DictReader(arq)
        _validar_cabecalho(leitor.fieldnames, caminho)
        observacoes = [
            _linha_para_observacao(linha, numero)
            for numero, linha in enumerate(leitor, start=2)
        ]
    if not observacoes:
        raise ValueError(f"dataset vazio: {caminho}")
    return Dataset(observacoes=observacoes, alertas=_alertas_qualidade(observacoes))


def _validar_cabecalho(colunas: list[str] | None, caminho: str) -> None:
    faltantes = [c for c in COLUNAS_ESPERADAS if c not in (colunas or [])]
    if faltantes:
        raise ValueError(
            f"{caminho}: colunas ausentes {faltantes}; esperado {COLUNAS_ESPERADAS}"
        )


def _linha_para_observacao(linha: dict[str, str], numero: int) -> Observacao:
    try:
        return Observacao(
            data=_parse_data(linha["Data"]),
            grupo=linha["Grupos de usuários"].strip(),
            parceiro=linha["Parceiro"].strip(),
            compradores=_parse_int(linha["compradores"]),
            comissao=parse_real(linha["comissão"]),
            cashback=parse_real(linha["cashback"]),
            vendas=parse_real(linha["vendas totais"]),
        )
    except ValueError as exc:
        raise ValueError(f"linha {numero}: {exc}") from None


def _parse_data(valor: str) -> date:
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        raise ValueError(f"data inválida: {valor!r}; esperado YYYY-MM-DD") from None


def _parse_int(valor: str) -> int:
    try:
        return int(valor.strip())
    except ValueError:
        raise ValueError(f"inteiro inválido: {valor!r}") from None


def _alertas_qualidade(observacoes: list[Observacao]) -> list[str]:
    alertas = _alertas_duplicatas(observacoes)
    alertas += _alertas_datas_faltantes(observacoes)
    alertas += _alertas_valores_negativos(observacoes)
    return alertas


def _alertas_duplicatas(observacoes: list[Observacao]) -> list[str]:
    vistos: set[tuple[date, str]] = set()
    alertas: list[str] = []
    for obs in observacoes:
        chave = (obs.data, obs.grupo)
        if chave in vistos and len(alertas) < MAX_ALERTAS_POR_TIPO:
            alertas.append(f"linha duplicada para {obs.grupo} em {obs.data}")
        vistos.add(chave)
    return alertas


def _alertas_datas_faltantes(observacoes: list[Observacao]) -> list[str]:
    por_grupo: dict[str, set[date]] = {}
    for obs in observacoes:
        por_grupo.setdefault(obs.grupo, set()).add(obs.data)
    alertas = []
    for grupo, datas in sorted(por_grupo.items()):
        esperadas = _intervalo_datas(min(datas), max(datas))
        faltantes = sorted(esperadas - datas)
        if faltantes:
            exemplos = ", ".join(str(d) for d in faltantes[:MAX_ALERTAS_POR_TIPO])
            alertas.append(f"{grupo}: {len(faltantes)} dia(s) sem dados ({exemplos})")
    return alertas


def _intervalo_datas(inicio: date, fim: date) -> set[date]:
    dias = (fim - inicio).days
    return {inicio + timedelta(days=i) for i in range(dias + 1)}


def _alertas_valores_negativos(observacoes: list[Observacao]) -> list[str]:
    alertas = []
    for obs in observacoes:
        negativos = [
            campo
            for campo, valor in [
                ("compradores", obs.compradores), ("comissão", obs.comissao),
                ("cashback", obs.cashback), ("vendas", obs.vendas),
            ]
            if valor < 0
        ]
        if negativos and len(alertas) < MAX_ALERTAS_POR_TIPO:
            alertas.append(
                f"{obs.grupo} em {obs.data}: valores negativos em {negativos}"
            )
    return alertas
