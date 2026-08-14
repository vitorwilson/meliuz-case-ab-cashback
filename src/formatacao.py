"""Formatação de números em pt-BR para relatórios e alertas."""


def fmt_real(valor: float) -> str:
    """4399.2 -> 'R$ 4.399' (pt-BR, sem centavos)."""
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def fmt_pct(valor: float) -> str:
    """0.634 -> '63,4%'."""
    return f"{valor * 100:.1f}%".replace(".", ",")


def fmt_pvalor(p: float) -> str:
    """0.00003 -> '< 0,0001'; 0.3466 -> '0,3466'."""
    if p < 0.0001:
        return "< 0,0001"
    return f"{p:.4f}".replace(".", ",")
