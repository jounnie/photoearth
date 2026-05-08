"""Gemeinsame Hilfsfunktionen für Tests – kein pytest, nur reine Python-Funktionen."""


def to_dms(value: float) -> list[tuple[int, int]]:
    """Konvertiert einen Dezimalgrad-Wert in das DMS-Rational-Format von piexif.

    Beispiel: 47.37 → [(47, 1), (22, 1), (12000, 1000)]
    """
    value = abs(value)
    d = int(value)
    m = int((value - d) * 60)
    s = round(((value - d) * 60 - m) * 60 * 1000)
    return [(d, 1), (m, 1), (s, 1000)]
