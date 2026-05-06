# --- PYTHON LERNEN: Imports ---
# Mit "from" und "import" holst du Funktionen/Klassen aus anderen Bibliotheken.
# SQLAlchemy ist eine Bibliothek, die Python mit Datenbanken verbindet.
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# --- PYTHON LERNEN: Variablen und Strings ---
# Eine Variable speichert einen Wert. Hier ist es ein String (Text in Anführungszeichen).
# "sqlite:///" bedeutet: benutze eine lokale SQLite-Datei als Datenbank.
DATABASE_URL = "sqlite:///./photoearth.db"

# --- PYTHON LERNEN: Funktionsaufruf mit Argumenten ---
# create_engine() ist eine Funktion. Die Klammern () rufen sie auf.
# connect_args={"check_same_thread": False} ist ein dict (Wörterbuch) als Argument.
# Dict: geschweifte Klammern {}, enthält Schlüssel-Wert-Paare.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# sessionmaker() gibt eine Klasse zurück, mit der wir Datenbank-Sitzungen öffnen können.
# autocommit=False: Änderungen werden nicht sofort gespeichert, wir müssen db.commit() aufrufen.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- PYTHON LERNEN: Klassen ---
# "class" definiert einen neuen Datentyp (Bauplan für Objekte).
# "Base" erbt von DeclarativeBase – das Doppelpunkt-Einrücken zeigt den Rumpf der Klasse.
# Alle Datenbankmodelle erben später von dieser Klasse.
class Base(DeclarativeBase):
    pass  # "pass" bedeutet: diese Klasse hat keinen eigenen Inhalt (nur geerbt)


# --- PYTHON LERNEN: Generator-Funktionen (yield) ---
# "def" definiert eine Funktion. Diese hier ist ein Generator:
# "yield" gibt einen Wert zurück UND pausiert – der Code nach yield läuft am Ende weiter.
# Das ist nützlich für Ressourcen, die man öffnen und sicher schließen muss.
def get_db():
    db = SessionLocal()  # Neue Datenbank-Sitzung öffnen
    try:
        yield db          # Sitzung an den Aufrufer übergeben (FastAPI nutzt das automatisch)
    finally:
        db.close()        # finally: läuft IMMER, auch wenn ein Fehler passiert
