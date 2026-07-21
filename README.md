# Kukonharjun Psykologinen Vibe-analyysi v4.2

Yhden sivun web-sovellus mökkiporukan "psykologiseen" (täysin absurdiin)
vibe-analyysiin. Osallistujat skannaavat QR-koodin, vastaavat 25 järjettömän
hauskaan monivalintakysymykseen, ja sovellus muodostaa automaattisesti 4
joukkuetta niin, että samanhenkisimmät vastaajat päätyvät samaan joukkueeseen.

Tekninen toteutus on tarkoituksella yksinkertainen: **Python-backend (FastAPI)
+ SQLite + puhdas HTML/CSS/JS-frontend**, ei build-vaihetta, ei ulkoisia
pilvipalveluita, ei nettiyhteyttä vaativia CDN-riippuvuuksia. Kaikki toimii
myös pelkässä mökin WiFi-lähiverkossa ilman internetiä.

## Pikakäynnistys

```bash
pip install -r requirements.txt
python run.py
```

Konsoliin tulostuu kaksi osoitetta:

```
Osallistujille (QR-koodi tämän osoitteen ympärille):
  http://192.168.x.x:8000

Admin-paneeli (pidä salassa):
  http://192.168.x.x:8000/admin/<salainen-tunnus>
```

- **Osallistujien osoite** kannattaa muuttaa QR-koodiksi (esim. millä tahansa
  QR-generaattorilla, tai avaa admin-paneeli - se näyttää QR-koodin valmiiksi
  renderöitynä ja skannattavana).
- **Admin-osoite** on tarkoitettu vain mökki-illan isännälle. Tunnus generoituu
  automaattisesti ensimmäisellä käynnistyskerralla ja tallentuu tiedostoon
  `data/admin_secret.txt`, joten se pysyy samana vaikka palvelin
  käynnistetään uudelleen kesken viikonlopun.

Kaikkien osallistujien puhelinten pitää olla samassa WiFi-verkossa kuin kone,
jolla palvelin pyörii. Sovellus ei tarvitse toimiakseen internet-yhteyttä.

## Osallistujat mobiilidatalla (ei samassa WiFissä)

Jos osa porukasta ei ole samassa WiFi-verkossa - esim. käyttävät mobiilidataa -
edellä tulostettu `192.168.x.x`-osoite ei toimi heille, koska se näkyy vain
samassa lähiverkossa. Ratkaisu on avata koneelta väliaikainen julkinen tunneli
paikalliseen palvelimeen. Helpoin tapa, ei vaadi rekisteröitymistä:

```bash
brew install cloudflared      # jos ei jo asennettuna
python run.py                 # käynnistä sovellus ensin, jää pyörimään
cloudflared tunnel --url http://localhost:8000    # toisessa terminaalissa
```

`cloudflared` tulostaa julkisen osoitteen muotoa
`https://joku-satunnainen-nimi.trycloudflare.com`. Käytä **tätä** osoitetta
(et enää `192.168.x.x`-osoitetta) sekä:

- osallistujien QR-koodin/linkin pohjana, ja
- **admin-paneelin avaamiseen omalla koneellasi** - eli mene osoitteeseen
  `https://joku-satunnainen-nimi.trycloudflare.com/admin/<salainen-tunnus>`,
  et `localhost`-osoitteeseen. Tämä on tärkeää: admin-sivu generoi QR-koodin
  sen osoitteen perusteella jolla sivu itse avattiin, joten jos avaat
  adminin `localhost`-osoitteesta, QR-koodi osoittaisi puhelimille
  toimimattomaan `localhost`-osoitteeseen.

Tunneli pysyy voimassa niin kauan kuin `cloudflared`-komento on käynnissä.
Kun ilta on ohi, `Ctrl+C` molemmissa terminaaleissa riittää sulkemaan kaiken.

Vaihtoehtoisesti `ngrok http 8000` toimii samalla periaatteella, mutta vaatii
ilmaisen tilin ja tunnuksen (`ngrok config add-authtoken ...`) ensimmäisellä
kerralla.

## Miten kysymyksiä muokataan

Kaikki 25 kysymystä asuvat tiedostossa [`app/questions.json`](app/questions.json).
Jokainen kysymys on JSON-olio, jossa on `id`, `text` ja neljä `options`-oliota:

```json
{
  "id": "kirjanpitaja-elain",
  "text": "Mikä eläin olisi paras kirjanpitäjä?",
  "options": [
    { "text": "Mehiläinen – järjestelmällinen ja ahkera", "tag": "mehilainen", "vibe_line": "{count}/{total} luottaisi kirjanpitonsa mehiläiselle epäröimättä." }
  ]
}
```

- `text` / option-`text`: näkyy sellaisenaan osallistujalle. Voi muokata vapaasti.
- `tag`: yksi sana (pieni alkukirjain), jota käytetään jos tämä vaihtoehto
  osoittautuu jonkin joukkueen tunnusomaisimmaksi vastaukseksi - se syötetään
  joukkueen nimigeneraattoriin (`app/content.py`, `NAME_TEMPLATES`).
- `vibe_line`: valmiiksi kirjoitettu perustelulause tulossivun "Miksi juuri
  te?" -osioon. Placeholderit `{count}`, `{total}` ja `{percent}` täytetään
  automaattisesti oikeilla luvuilla kun tätä vaihtoehtoa käytetään perusteluna.

Uuden kysymyksen lisääminen: kopioi yksi olio `questions`-listan sisään, anna
sille uniikki `id`, ja kirjoita neljä vaihtoehtoa. Ei koodimuutoksia tarvita.
Kysymysten määrän ei tarvitse olla tasan 25 - mikä tahansa määrä toimii.

## Projektirakenne

```
app/
  main.py            FastAPI-reitit (sivut, API, WebSocket)
  database.py        SQLite-kerros (osallistujat, vastaukset, tulokset)
  models.py          Pydantic-skeemat
  clustering.py       Samankaltaisuuslaskenta ja joukkueiden muodostus
  team_generator.py   Joukkueen nimi, perustelut ja loppukaneetti
  content.py          Nimimallit ja loppukaneettien pankki
  questions.json       Kysymyspankki (muokattava)
  questions_data.py    Kysymysten lataus/välimuisti
  ws_manager.py        WebSocket-yleislähetys
  config.py            Asetukset (portti, admin-tunnus, tietokantapolku)
static/
  index.html           Osallistujan yhden sivun sovellus
  admin.html           Admin-paneeli
  css/style.css        Tyylit (mobile first, ei ulkoisia fontteja/CDN:ää)
  js/app.js             Osallistujan sovelluslogiikka
  js/admin.js           Admin-paneelin logiikka
  js/teams-reveal.js    Jaettu laskenta-animaatio + joukkuekorttien piirto
run.py                 Käynnistysskripti (tulostaa QR-osoitteet konsoliin)
```

## Miten joukkueet muodostetaan

1. Jokaisen osallistujaparin väliltä lasketaan **normalisoitu Hamming-etäisyys**
   (kuinka suureen osaan 25 kysymyksestä he vastasivat eri tavalla).
2. **Hierarkkinen agglomeratiivinen klusterointi** (average linkage) yhdistää
   lähimmät klusterit kunnes jäljellä on tasan 4 ryhmää - tämä muodostaa
   luonnostaan samanhenkiset porukat ilman että koon tasapainoa täytyy valita
   etukäteen.
3. Jos ryhmien koot menevät kovin epätasan, **tasapainotusvaihe** siirtää
   ylisuurista ryhmistä alisuuriin aina sen henkilön, joka sopii huonoiten
   omaan nykyiseen ryhmäänsä - ja kohteeksi ryhmän johon hän sopii parhaiten.
   Vibe pysyy siis ensisijaisena periaatteena myös tasapainotuksen aikana.
4. Jokaiselle joukkueelle etsitään sen **tunnusomaisimmat kysymykset**
   (korkea sisäinen yksimielisyys + erottuu muista joukkueista), joiden
   pohjalta generoidaan joukkueen nimi ja 3-5 perustelua. Viimeinen perustelu
   on aina algoritmin oikeasti laskema yhteensopivuusprosentti.

Admin voi muodostaa joukkueet uudelleen milloin tahansa (nappi toimii myös
uudelleen, jos joku vastaa myöhässä) - tuorein ajo korvaa edellisen tuloksen.

## Tapahtuman nollaus (uudelleenkäyttö)

Admin-paneelin "Nollaa"-painike tyhjentää kaikki osallistujat, vastaukset ja
tulokset - kätevä jos sovellusta käytetään uudestaan seuraavana
viikonloppuna eri porukalla. Kysymyspankki ja admin-tunnus säilyvät ennallaan.

## Ympäristömuuttujat (valinnaisia)

| Muuttuja      | Oletus        | Kuvaus                                   |
|---------------|---------------|-------------------------------------------|
| `PORT`        | `8000`        | Palvelimen portti                         |
| `HOST`        | `0.0.0.0`     | Kuunneltava osoite                        |
| `ADMIN_TOKEN` | (generoidaan) | Pakota tietty admin-URL-tunnus            |
| `TEAM_COUNT`  | `4`           | Kuinka moneen joukkueeseen jaetaan         |

## Deployment vaihtoehtoisesti pilveen

Sovellus toimii sellaisenaan myös esim. Renderissä, Fly.io:ssa tai muussa
Python-yhteensopivassa palvelussa, jos mökillä ei ole omaa konetta jota
pitää palvelimena. Tällöin `ADMIN_TOKEN` kannattaa asettaa itse
ympäristömuuttujana, ja QR-koodi osoittaa saatuun julkiseen osoitteeseen.
