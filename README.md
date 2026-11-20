# tableau-emprunt

Calculer la mensualité, le tableau d'amortissement et le coût total d'un prêt (immobilier, auto, consommation), ou le montant qu'on peut emprunter, en ligne de commande ou en Python. Aucune dépendance.

## Installation

```bash
pip install git+https://github.com/TheoPSR01/tableau-emprunt.git
```

Python 3.10 ou plus récent.

## En ligne de commande

200 000 € à 3,5 % sur 25 ans, avec 25 € d'assurance par mois :

```bash
tableau-emprunt 200000 3,5 25 --assurance 25
```

```
Mensualité hors assurance     : 1 001,25 €
Mensualité assurance comprise : 1 026,25 €
Total des intérêts            : 100 373,59 €
Total de l'assurance          : 7 500,00 €
Coût total du crédit          : 107 873,59 €
Montant total remboursé       : 307 873,59 €
```

```bash
tableau-emprunt 200000 3,5 25 --tableau            # toutes les échéances
tableau-emprunt 200000 3,5 25 --csv > pret.csv     # pour Excel
tableau-emprunt 15000 5,9 48 --mois                # prêt auto sur 48 mois
```

## En Python

```python
from tableau_emprunt import mensualite, capacite_emprunt, tableau, resume, taux_endettement

mensualite(200000, 3.5, 300)          # Decimal('1001.25')
capacite_emprunt(1000, 3.5, 300)      # Decimal('199750.88') : ce qu'on emprunte avec 1 000 € par mois
taux_endettement(1050, 3000)          # Decimal('35.0') en %

for e in tableau(200000, 3.5, 300)[:3]:
    print(e.numero, e.interets, e.capital, e.restant_du)
```

## Calcul

Prêt à mensualités constantes : mensualité = C × t / (1 − (1 + t)^−n), où C est le capital, t le taux annuel divisé par 12 et n le nombre de mois. Chaque mois, les intérêts portent sur le capital restant dû et le reste de la mensualité rembourse le capital. Les montants sont arrondis au centime ; la dernière échéance solde le capital et absorbe les écarts d'arrondi (quelques euros sur 25 ans). L'assurance est traitée comme un montant fixe par mois.

## Limites

Le taux saisi est le taux nominal, pas le TAEG : les frais de dossier, de garantie et de courtage ne sont pas inclus. Les prêts à taux variable, à paliers, in fine ou avec différé ne sont pas traités, ni les remboursements anticipés. Pour un projet réel, l'offre de prêt de la banque fait foi.

## Contribuer

```bash
git clone https://github.com/TheoPSR01/tableau-emprunt.git
cd tableau-emprunt
pip install -e ".[dev]"
pytest
```

## Licence

MIT
