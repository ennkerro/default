#!/bin/bash
# Tuplaklikkaa tata tiedostoa Finderissa kaynnistaaksesi
# Kukonharjun Psykologinen Vibe-analyysin. Ei vaadi komentojen kirjoittamista.
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Kukonharjun Psykologinen Vibe-analyysi - kaynnistetaan"
echo "============================================================"
echo ""

if ! python3 --version >/dev/null 2>&1; then
  echo "Toimivaa Python 3:a ei loytynyt talta koneelta."
  echo ""
  echo "Jos naet erillisen ikkunan joka ehdottaa 'Command Line Developer"
  echo "Tools' -asennusta: paina siina Cancel. Se on iso (satoja megoja)"
  echo "Applen paketti eika tarpeen - alla oleva vaihtoehto riittaa ja on"
  echo "paljon nopeampi."
  echo ""
  echo "Asenna Python suoraan taalta (n. 40 Mt):"
  echo "  https://www.python.org/downloads/macos/"
  echo "  -> lataa 'macOS 64-bit universal2 installer' ja aja se."
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
