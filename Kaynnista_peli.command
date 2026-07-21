#!/bin/bash
# Tuplaklikkaa tata tiedostoa Finderissa kaynnistaaksesi
# Kukonharjun Psykologinen Vibe-analyysin. Ei vaadi komentojen kirjoittamista.
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Kukonharjun Psykologinen Vibe-analyysi - kaynnistetaan"
echo "============================================================"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3:a ei loytynyt talta koneelta."
  echo ""
  echo "Asenna se osoitteesta:"
  echo "  https://www.python.org/downloads/macos/"
  echo ""
  echo "Kun asennus on valmis, tuplaklikkaa tata tiedostoa uudelleen."
  echo ""
  read -p "Paina Enter sulkeaksesi tama ikkuna..."
  exit 1
fi

echo "Asennetaan tarvittavat kirjastot (kestaa hetken vain ensimmaisella kerralla)..."
if ! python3 -m pip install --quiet -r requirements.txt; then
  echo ""
  echo "Kirjastojen asennus epaonnistui - katso virheilmoitus ylempaa."
  read -p "Paina Enter sulkeaksesi tama ikkuna..."
  exit 1
fi

echo ""
echo "------------------------------------------------------------"
echo "  Peli kaynnistyy. Osoitteet ilmestyvat alle hetken kuluttua."
echo "  TATA IKKUNAA EI SAA SULKEA ILLAN AIKANA - se pitaa pelin kaynnissa."
echo "  Kun ilta on ohi: sulje tama ikkuna tai paina Ctrl+C."
echo "------------------------------------------------------------"
echo ""

python3 run.py

echo ""
read -p "Peli on pysahtynyt. Paina Enter sulkeaksesi tama ikkuna..."
