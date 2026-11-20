"""tableau_emprunt : tableau d'amortissement d'un prêt à mensualités constantes.

Mensualité hors assurance : M = C × t / (1 - (1 + t)^-n), avec t le taux annuel
divisé par 12 et n le nombre de mois. Chaque mois, les intérêts portent sur le
capital restant dû ; le reste de la mensualité rembourse le capital.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import TextIO, Union

__version__ = "0.1.0"

Montant = Union[int, float, str, Decimal]
CENT = Decimal("0.01")


def _d(x: Montant) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x).replace(",", "."))


def _arrondi(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def _taux_mensuel(taux_annuel: Montant) -> Decimal:
    t = _d(taux_annuel)
    if t < 0:
        raise ValueError("le taux ne peut pas être négatif")
    return t / Decimal(100) / Decimal(12)


def mensualite(capital: Montant, taux_annuel: Montant, duree_mois: int) -> Decimal:
    """Mensualité hors assurance, arrondie au centime. ``taux_annuel`` en % (3.5 pour 3,5 %)."""
    c = _d(capital)
    if c <= 0 or duree_mois < 1:
        raise ValueError("capital et durée doivent être positifs")
    t = _taux_mensuel(taux_annuel)
    if t == 0:
        return _arrondi(c / duree_mois)
    return _arrondi(c * t / (1 - (1 + t) ** -duree_mois))


def capacite_emprunt(mensualite_max: Montant, taux_annuel: Montant, duree_mois: int) -> Decimal:
    """Capital empruntable pour une mensualité donnée (hors assurance)."""
    m = _d(mensualite_max)
    t = _taux_mensuel(taux_annuel)
    if t == 0:
        return _arrondi(m * duree_mois)
    return _arrondi(m * (1 - (1 + t) ** -duree_mois) / t)


@dataclass(frozen=True)
class Echeance:
    numero: int
    mensualite: Decimal        # hors assurance
    interets: Decimal
    capital: Decimal           # capital remboursé ce mois-ci
    assurance: Decimal
    restant_du: Decimal

    @property
    def total(self) -> Decimal:
        return self.mensualite + self.assurance


def tableau(capital: Montant, taux_annuel: Montant, duree_mois: int, assurance_mensuelle: Montant = 0) -> list:
    """Tableau d'amortissement complet. La dernière échéance solde le capital (écarts d'arrondi)."""
    c = _d(capital)
    t = _taux_mensuel(taux_annuel)
    m = mensualite(c, taux_annuel, duree_mois)
    ass = _d(assurance_mensuelle)
    lignes, restant = [], c
    for k in range(1, duree_mois + 1):
        interets = _arrondi(restant * t)
        if k == duree_mois:
            amorti = restant
            m_k = amorti + interets
        else:
            amorti = m - interets
            m_k = m
        restant -= amorti
        lignes.append(Echeance(k, m_k, interets, amorti, ass, restant))
    return lignes


@dataclass(frozen=True)
class Resume:
    mensualite: Decimal
    mensualite_assurance_comprise: Decimal
    total_interets: Decimal
    total_assurance: Decimal
    cout_total: Decimal         # intérêts + assurance
    total_rembourse: Decimal


def resume(capital: Montant, taux_annuel: Montant, duree_mois: int, assurance_mensuelle: Montant = 0) -> Resume:
    lignes = tableau(capital, taux_annuel, duree_mois, assurance_mensuelle)
    interets = sum((l.interets for l in lignes), Decimal(0))
    assurance = sum((l.assurance for l in lignes), Decimal(0))
    m = lignes[0].mensualite
    return Resume(m, m + lignes[0].assurance, interets, assurance, interets + assurance,
                  sum((l.total for l in lignes), Decimal(0)))


def taux_endettement(mensualites_credits: Montant, revenus_mensuels_nets: Montant) -> Decimal:
    """Part des revenus consacrée aux crédits, en %. Les banques visent 35 % maximum, assurance comprise."""
    r = _d(revenus_mensuels_nets)
    if r <= 0:
        raise ValueError("revenus positifs attendus")
    return (_d(mensualites_credits) / r * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def ecrire_csv(lignes: list, sortie: TextIO) -> None:
    w = csv.writer(sortie, delimiter=";")
    w.writerow(["Echeance", "Mensualite", "Interets", "Capital", "Assurance", "Restant du"])
    fr = lambda x: str(x).replace(".", ",")
    for l in lignes:
        w.writerow([l.numero, fr(l.mensualite), fr(l.interets), fr(l.capital), fr(l.assurance), fr(l.restant_du)])


def _fr(x: Decimal) -> str:
    return f"{x:,.2f}".replace(",", " ").replace(".", ",")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="tableau-emprunt", description="Tableau d'amortissement d'un prêt à mensualités constantes.")
    p.add_argument("--version", action="version", version=f"tableau-emprunt {__version__}")
    p.add_argument("capital", help="montant emprunté")
    p.add_argument("taux", help="taux annuel en %% (ex. 3,5)")
    p.add_argument("duree", type=int, help="durée en années (ou en mois avec --mois)")
    p.add_argument("--mois", action="store_true", help="la durée est exprimée en mois")
    p.add_argument("--assurance", default="0", help="assurance mensuelle en euros")
    p.add_argument("--tableau", action="store_true", help="afficher toutes les échéances")
    p.add_argument("--csv", action="store_true", help="tableau complet au format CSV")
    args = p.parse_args(argv)
    n = args.duree if args.mois else args.duree * 12
    try:
        lignes = tableau(args.capital, args.taux, n, args.assurance)
        r = resume(args.capital, args.taux, n, args.assurance)
    except (ValueError, InvalidOperation) as exc:
        print(f"tableau-emprunt : {exc}", file=sys.stderr)
        return 2
    if args.csv:
        ecrire_csv(lignes, sys.stdout)
        return 0
    if args.tableau:
        print(f"{'N°':>4} {'Mensualité':>12} {'Intérêts':>11} {'Capital':>11} {'Assurance':>10} {'Restant dû':>13}")
        for l in lignes:
            print(f"{l.numero:>4} {_fr(l.mensualite):>12} {_fr(l.interets):>11} {_fr(l.capital):>11} {_fr(l.assurance):>10} {_fr(l.restant_du):>13}")
        print()
    print(f"Mensualité hors assurance   : {_fr(r.mensualite)} €")
    print(f"Mensualité assurance comprise : {_fr(r.mensualite_assurance_comprise)} €")
    print(f"Total des intérêts          : {_fr(r.total_interets)} €")
    print(f"Total de l'assurance         : {_fr(r.total_assurance)} €")
    print(f"Coût total du crédit        : {_fr(r.cout_total)} €")
    print(f"Montant total remboursé      : {_fr(r.total_rembourse)} €")
    return 0


__all__ = ["Echeance", "Resume", "capacite_emprunt", "ecrire_csv", "main", "mensualite", "resume", "tableau", "taux_endettement"]
