"""
Ei-kysymyskohtainen huumorisisalto: joukkueiden nimimallit ja loppukaneetit.

Nama ovat tarkoituksella erillaan questions.json:sta, koska ne eivat liity
yksittaiseen kysymykseen vaan koko joukkueen lopputulokseen. Listoja voi
vapaasti pidentaa - mita enemman vaihtoehtoja, sita vahemman toistoa illan
aikana jos sovellusta kaytetaan useampana viikonloppuna.
"""

# Joukkueen nimimallit. {Tag} = isolla alkukirjaimella (esim. "Joutsen"),
# {tag} = pienella (esim. "joutsen"). Vain yhdysmerkillisia tai sellaisenaan
# taipumattomia rakenteita, jotta mika tahansa tag-sana toimii kieliopillisesti.
NAME_TEMPLATES = [
    "Operaatio {Tag}",
    "{Tag}liiga",
    "{Tag}ministeriö",
    "{Tag}paraati",
    "{Tag}-kerho",
    "{Tag}-osasto",
    "Kvantti-{Tag}",
    "Team {Tag}",
    "{Tag}-akatemia",
    "Suuri {Tag}-liitto",
    "{Tag} Society",
    "{Tag}-yksikkö",
    "Salainen {Tag}-neuvosto",
    "{Tag}-kollektiivi",
    "{Tag}-tiimi 3000",
    "Näkymätön {Tag}-verkosto",
]

# Joukkuekortin ylla vilahtava tunnusvari/emoji, kierratetaan jarjestyksessa.
TEAM_EMOJIS = ["🔥", "⚡", "🌊", "🌪️", "✨", "🌀"]

# Loppukaneetti: yksi humoristinen "diagnoosi" per joukkue, arvotaan ilman
# toistoa saman ajon sisalla.
CLOSING_DIAGNOSES = [
    "Varoitus: Tämä ryhmä tekee todennäköisesti spontaanin saunareissun kello 02.17.",
    "Algoritmi suosittelee pitämään nämä henkilöt vähintään viiden metrin päässä grillihiilistä.",
    "Tämän ryhmän arvioitu yhteinen aivosolujen käyttöaste on 113 %.",
    "Ennuste: vähintään yksi spontaani yhteislaulu ennen puoltayötä.",
    "Tämä ryhmä saattaa yrittää neuvotella sään kanssa suoraan.",
    "Havaittu poikkeuksellisen korkea riski perustaa oma pienvaltio viikonlopun aikana.",
    "Tämän joukkueen sisäinen kellotaajuus ei vastaa mitään tunnettua aikavyöhykettä.",
    "Suositus: älä jätä tätä ryhmää yksin veneen kanssa ilman valvontaa.",
    "Analyysi viittaa vahvaan taipumukseen äänestää lisäkahvista kesken yön.",
    "Tämä ryhmä on tilastollisesti merkityksettömästi mutta itsevarmasti muita sekaisempi.",
    "Varotoimi: pidä silmällä ketä tahansa, joka ehdottaa vielä yhtä saunavuoroa.",
    "Tämän tiimin yhteinen päätöksentekokyky heikkenee merkittävästi auringonlaskun jälkeen.",
    "Algoritmi ei voi taata, että tämä ryhmä muistaa aamulla mitä eilen illalla sovittiin.",
    "Todennäköisyys spontaanille mökkijuhlalle: huolestuttavan korkea.",
    "Tämän ryhmän energiasignaali saattaa häiritä lähialueen WiFi-yhteyksiä.",
    "Suositellaan valvontaa, mikäli ryhmän lähellä on samaan aikaan avotulta ja vahvoja mielipiteitä.",
    "Tämä joukkue on tilastollisesti taipuvainen yliarvioimaan omat grillaustaitonsa.",
    "Havaittu merkkejä siitä, että ryhmä keksii omia sanoja kesken viikonlopun.",
    "Algoritmi ei ota vastuuta, jos tämä ryhmä päättää järjestää turnauksen kello 01.",
    "Tämän ryhmän kollektiivinen tyyneys purkautuu todennäköisesti yhtenä isona naurunpuuskana.",
    "Ennustemalli antaa 61 % todennäköisyyden yöuinnille kysymättä lupaa keneltäkään.",
    "Tämä joukkue saattaa yrittää selittää fysiikkaa nuotion ääressä, hyvässä hengessä.",
]

# Varajarjestelma: kaytetaan vain jos jostain kysymyksesta puuttuisi vibe_line
# (esim. jos joku lisaa uuden kysymyksen questions.json:iin eika muista
# kirjoittaa sille perustelulausetta). Toimii aina kieliopillisesti.
GENERIC_FALLBACK_TEMPLATE = '{count}/{total} valitsi saman vastauksen kysymykseen "{question}".'
