# Kukonharjun Psykologinen Vibe-analyysi v4.2

Yhden sivun web-sovellus mökkiporukan "psykologiseen" (täysin absurdiin)
vibe-analyysiin. Osallistujat skannaavat QR-koodin, vastaavat 25 järjettömän
hauskaan monivalintakysymykseen, ja sovellus muodostaa automaattisesti
joukkueet (oletuksena 4, admin voi valita 2-10) niin, että samanhenkisimmät
vastaajat päätyvät samaan joukkueeseen.

Tekninen toteutus on tarkoituksella yksinkertainen: **Python-backend (FastAPI)
+ SQLite + puhdas HTML/CSS/JS-frontend**, ei build-vaihetta, ei ulkoisia
pilvipalveluita, ei nettiyhteyttä vaativia CDN-riippuvuuksia. Kaikki toimii
myös pelkässä mökin WiFi-lähiverkossa ilman internetiä.

## Ilmainen nettiversio (Render) - ei paikallista asennusta

Jos et halua asentaa mitään omalle koneellesi (ei Pythonia, ei Terminaalia),
sovelluksen voi julkaista ilmaiseksi osoitteeseen `https://jokin-nimi.onrender.com`.
Tämän jälkeen sekä admin että osallistujat vain avaavat linkin selaimessa -
toimii myös mobiilidatalla, ja sama linkki on käytettävissä myös ensi vuonna.

**Kertaluontoinen käyttöönotto (n. 10 min):**

1. Mene osoitteeseen [render.com](https://render.com) ja luo tili ("Get Started" -> "Sign up with GitHub" on helpoin).
2. Dashboardissa: **New +** -> **Blueprint**.
3. Valitse tämä GitHub-repositorio (`ennkerro/default`) ja branch
   `claude/kukonharjun-vibe-analyysi-npky9y`. Render löytää automaattisesti
   tämän repon `render.yaml`-tiedoston ja ehdottaa valmiiksi täytettyä palvelua.
4. Kysyttäessä `ADMIN_TOKEN`-arvoa, liitä oma salainen tunnuksesi (voit
   keksiä minkä tahansa, esim. jokin ei-arvattava sanayhdistelmä).
5. Paina **Apply** / **Create Web Service**. Ensimmäinen julkaisu kestää
   pari minuuttia.
6. Kun se on valmis, Render näyttää julkisen osoitteen, esim.
   `https://kukonharjun-vibe-analyysi.onrender.com`. Admin-paneeli on
   samassa osoitteessa polussa `/admin/<ADMIN_TOKEN jonka annoit vaiheessa 4>`.

**Kaksi asiaa jotka kannattaa tietää ilmaisesta tasosta:**

- Palvelu "nukahtaa" 15 minuutin jouten olon jälkeen. Ensimmäinen avaus sen
  jälkeen kestää ~30-60 sekuntia herätä. Avaa admin-linkki pari minuuttia
  ennen aloitusta, niin se on jo hereillä kun kaverit skannaavat QR-koodin.
- Levytila on väliaikainen: jos palvelu joutuu nukkumaan kesken kaiken
  (esim. 15 minuutin täysin hiljainen tauko kesken kyselyn), kertyneet
  vastaukset katoavat ja osallistujien pitäisi vastata uudelleen. Tämä on
  epätodennäköistä kun porukka on aktiivisesti käyttämässä sovellusta
  (kenen tahansa toiminta pitää palvelun hereillä), mutta jos haluat
  nollariskin, voit lisäksi asettaa ilmaisen "pingaus"-palvelun kuten
  [cron-job.org](https://cron-job.org) käymään osoitteessasi n. 10 min
  välein - täysin valinnainen lisävarmistus, ei pakollinen.

Ensi vuonna: avaa sama Render-osoite, paina admin-paneelista **"Nollaa"**,
ja peli on valmis uudelle porukalle - ei mitään uudelleenasennusta.

## Paikallinen pikakäynnistys (oma kone / mökin lähiverkko)

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

**Helpoin tapa - admin-paneelista, ei koodia tarvita:** avaa admin-paneeli ja
paina "✏️ Muokkaa kysymyksiä". Sieltä voit:

- muokata minkä tahansa kysymyksen tai vaihtoehdon tekstiä suoraan
- poistaa tylsät kysymykset (roskakori-ikoni)
- lisätä uusia kysymyksiä ("+ Lisää kysymys" - täytä teksti ja neljä vaihtoehtoa)
- palauttaa alkuperäiset 25 oletuskysymystä ("Palauta oletukset")
- ladata varmuuskopion nykyisistä kysymyksistä tiedostoksi omalle koneelle, ja
  tuoda se takaisin myöhemmin ("Lataa varmuuskopio" / "Tuo tiedostosta")

Muista painaa **"Tallenna muutokset"** - muokkaukset eivät tallennu ilman sitä.
Kysymysten muokkaaminen kannattaa tehdä ennen kuin kaverit alkavat vastata,
ei kesken kyselyn.

**Huom Render-version käyttäjille:** kysymyspankki tallentuu samaan
väliaikaiseen levytilaan kuin osallistujatkin (ks. yllä oleva kohta ilmaisen
tason rajoituksista) - jos palvelu joutuu nukkumaan pitkäksi aikaa muokkauksen
ja pelin välillä, muokkaukset voivat kadota. Jos olet tehnyt paljon omia
kysymyksiä, ota varmuuskopio ("Lataa varmuuskopio") ja tuo se tarvittaessa
takaisin ennen peli-iltaa.

**Teknisempi vaihtoehto - questions.json suoraan:** kysymysten alkuperäinen
"tehdasasetus" asuu tiedostossa [`app/questions.json`](app/questions.json) ja
sitä käytetään aina kun tietokannassa ei vielä ole yhtään kysymystä tai kun
painat "Palauta oletukset". Jokainen kysymys on JSON-olio, jossa on `id`,
`text` ja neljä `options`-oliota:

```json
{
  "id": "kirjanpitaja-elain",
  "text": "Mikä eläin olisi paras kirjanpitäjä?",
  "options": [
    { "text": "Mehiläinen – järjestelmällinen ja ahkera", "tag": "mehilainen", "vibe_line": "{count}/{total} luottaisi kirjanpitonsa mehiläiselle epäröimättä." }
  ]
}
```

- `text` / option-`text`: näkyy sellaisenaan osallistujalle.
- `tag`: yksi sana (pieni alkukirjain), jota käytetään jos tämä vaihtoehto
  osoittautuu jonkin joukkueen tunnusomaisimmaksi vastaukseksi - se syötetään
  joukkueen nimigeneraattoriin (`app/content.py`, `NAME_TEMPLATES`). Admin-
  paneelin kautta lisätyille kysymyksille tämä päätellään automaattisesti.
- `vibe_line`: valmiiksi kirjoitettu perustelulause tulossivun "Miksi juuri
  te?" -osioon. Placeholderit `{count}`, `{total}` ja `{percent}` täytetään
  automaattisesti oikeilla luvuilla. Jos puuttuu, käytetään yleispätevää
  varalausetta - admin-paneelin kautta lisätyt kysymykset toimivat siis aina,
  vaikka valmista perustelulausetta ei kirjoitettaisikaan.

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
  questions.json       Kysymyspankin oletussisältö ("tehdasasetus")
  questions_data.py    Kysymyspankin lataus tietokannasta, validointi, oletusten palautus
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
   (kuinka suureen osaan kysymyksistä he vastasivat eri tavalla). Kaikki
   kysymykset vaikuttavat yhtä paljon.
2. **Hierarkkinen agglomeratiivinen klusterointi** (average linkage) yhdistää
   lähimmät klusterit kunnes jäljellä on admin-paneelista valittu määrä
   ryhmiä (oletus 4) - antaa järkevän lähtökohdan.
3. **K-medoids-tarkennus** (Partitioning Around Medoids): jokainen osallistuja
   siirretään sen ryhmän luo jonka todelliseen jäseneen (medoidiin) hän on
   kaikista lähinnä, minkä jälkeen medoidit päivitetään - toistetaan kunnes
   vakiintuu. Tämä varmistaa että lopputulos perustuu aitoon parittaiseen
   samankaltaisuuteen, ei vain siihen että joku "sopii keskimäärin" johonkin
   ryhmään.
4. Jos ryhmien koot menevät kovin epätasan, **tasapainotusvaihe** siirtää
   ylisuurista ryhmistä alisuuriin aina sen henkilön, joka sopii huonoiten
   omaan nykyiseen ryhmäänsä - ja kohteeksi ryhmän johon hän sopii parhaiten.
   Vibe pysyy siis ensisijaisena periaatteena myös tasapainotuksen aikana.
5. Jokaiselle joukkueelle etsitään sen **tunnusomaisimmat kysymykset** -
   painotetaan erityisesti sitä kuinka paljon joukkueen vastaus poikkeaa
   *muista* joukkueista, ei vain sisäistä yksimielisyyttä. Näin eri
   joukkueiden perustelut nostavat esiin eri kysymyksiä sen sijaan että
   kaikki viittaisivat samaan yleisesti suosittuun vastaukseen. Näiden
   pohjalta generoidaan joukkueen nimi ja 3-5 perustelua. Viimeinen perustelu
   on aina algoritmin oikeasti laskema yhteensopivuusprosentti.

Admin voi muodostaa joukkueet uudelleen milloin tahansa ja eri
joukkuemäärällä (nappi toimii myös uudelleen, jos joku vastaa myöhässä) -
tuorein ajo korvaa edellisen tuloksen kaikkien näytöillä.

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
| `TEAM_COUNT`  | `4`           | Joukkueiden oletusmäärä (admin voi silti valita 2-10 per ajo paneelista) |
