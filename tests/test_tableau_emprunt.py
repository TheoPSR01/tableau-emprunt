from decimal import Decimal

import pytest

from tableau_emprunt import capacite_emprunt, main, mensualite, resume, tableau, taux_endettement


def test_mensualite_reference():
    # 200 000 € à 3,5 % sur 25 ans
    assert mensualite(200000, 3.5, 300) == Decimal("1001.25")


def test_mensualite_taux_zero():
    assert mensualite(12000, 0, 48) == Decimal("250.00")


def test_capacite_emprunt():
    assert capacite_emprunt(1000, 3.5, 300) == Decimal("199750.88")
    assert capacite_emprunt(500, 0, 24) == Decimal("12000.00")


def test_tableau_coherent():
    lignes = tableau(200000, "3,5", 300)
    assert len(lignes) == 300
    assert lignes[0].interets == Decimal("583.33")          # 200 000 × 3,5 % / 12
    assert lignes[0].capital == Decimal("417.92")
    assert sum(l.capital for l in lignes) == Decimal(200000)
    assert lignes[-1].restant_du == 0
    assert all(l.mensualite == Decimal("1001.25") for l in lignes[:-1])
    assert abs(lignes[-1].mensualite - Decimal("1001.25")) < 1


def test_resume_avec_assurance():
    r = resume(100000, 4, 120, assurance_mensuelle=20)
    assert r.mensualite == mensualite(100000, 4, 120)
    assert r.mensualite_assurance_comprise == r.mensualite + 20
    assert r.total_assurance == Decimal(2400)
    assert r.cout_total == r.total_interets + 2400
    assert r.total_rembourse == 100000 + r.cout_total


def test_taux_endettement():
    assert taux_endettement(1050, 3000) == Decimal("35.0")


@pytest.mark.parametrize("args", [(0, 3, 120), (1000, 3, 0), (1000, -1, 12)])
def test_erreurs(args):
    with pytest.raises(ValueError):
        mensualite(*args)


def test_cli(capsys):
    assert main(["200000", "3,5", "25"]) == 0
    assert "1 001,25 €" in capsys.readouterr().out
    assert main(["12000", "0", "48", "--mois", "--csv"]) == 0
    assert "48;250,00;0,00;250,00;0;0,00" in capsys.readouterr().out


def test_cli_aide():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
