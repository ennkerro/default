"""
Joukkueiden muodostus vastausten samankaltaisuuden perusteella.

Algoritmi:
1. Jokaisen osallistujaparin etaisyys = normalisoitu Hamming-etaisyys eli
   kuinka suureen osaan kysymyksista he vastasivat eri tavalla (0 = tayysin
   samaa mielta kaikesta, 1 = tayysin eri mielta kaikesta). Kaikki kysymykset
   vaikuttavat etaisyyteen yhta paljon.
2. Hierarkkinen agglomeratiivinen klusterointi (average linkage) yhdistaa
   aina kaksi lahinta klusteria kunnes jaljella on tasan k klusteria. Tama
   on deterministinen ja antaa jarkevan lahtokohdan.
3. K-medoids-tarkennus (Partitioning Around Medoids): jokainen osallistuja
   siirretaan sen ryhman luo, jonka todelliseen jaseneen (medoidiin) han on
   kaikista lahinna, minka jalkeen medoidit paivitetaan - toistetaan kunnes
   vakiintuu. Tama varmistaa etta lopputulos perustuu aitoon parittaiseen
   samankaltaisuuteen (kaikista lahimmiten samankaltaisesti vastanneet samaan
   ryhmaan), eika vain siihen etta joku "sopii keskimaarin" johonkin ryhmaan.
4. Tasapainotusvaihe siirtaa tarvittaessa henkiloita ylisuurista klustereista
   alisuuriin (mahdollisimman tasainen koko), mutta valitsee siirrettavaksi
   aina sen henkilon joka sopii huonoiten omaan nykyiseen ryhmaansa, ja
   kohteeksi ryhman johon han sopii parhaiten - vibe pysyy siis ensisijaisena
   periaatteena myos tasapainotuksen aikana.
"""
from itertools import combinations


def hamming_distance(a: dict[str, int], b: dict[str, int], question_ids: list[str]) -> float:
    if not question_ids:
        return 0.0
    diff = sum(1 for q in question_ids if a.get(q) != b.get(q))
    return diff / len(question_ids)


def build_distance_matrix(
    participant_ids: list[int],
    answers: dict[int, dict[str, int]],
    question_ids: list[str],
) -> dict[tuple[int, int], float]:
    dist: dict[tuple[int, int], float] = {}
    for a, b in combinations(participant_ids, 2):
        d = hamming_distance(answers.get(a, {}), answers.get(b, {}), question_ids)
        key = (a, b) if a < b else (b, a)
        dist[key] = d
    return dist


def _pair_distance(dist: dict, i: int, j: int) -> float:
    if i == j:
        return 0.0
    key = (i, j) if i < j else (j, i)
    return dist[key]


def _average_linkage(cluster_a: list[int], cluster_b: list[int], dist: dict) -> float:
    total = 0.0
    count = 0
    for i in cluster_a:
        for j in cluster_b:
            total += _pair_distance(dist, i, j)
            count += 1
    return total / count if count else 0.0


def agglomerative_clusters(participant_ids: list[int], dist: dict, k: int) -> list[list[int]]:
    """Palauttaa tasan k klusteria (tai vahemman, jos osallistujia on vahemman kuin k)."""
    clusters = [[pid] for pid in participant_ids]
    if len(clusters) <= k:
        return clusters

    while len(clusters) > k:
        best_pair = None
        best_dist = None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = _average_linkage(clusters[i], clusters[j], dist)
                if best_dist is None or d < best_dist:
                    best_dist = d
                    best_pair = (i, j)
        i, j = best_pair
        merged = clusters[i] + clusters[j]
        clusters = [c for idx, c in enumerate(clusters) if idx not in (i, j)]
        clusters.append(merged)
    return clusters


def _avg_dist_to_group(person: int, group: list[int], dist: dict) -> float:
    others = [p for p in group if p != person]
    if not others:
        return 0.0
    return sum(_pair_distance(dist, person, o) for o in others) / len(others)


def _medoid(group: list[int], dist: dict) -> int:
    """Ryhman jasen jolla on pienin keskietaisyys ryhman muihin jaseniin - ryhman "aito keskus"."""
    return min(group, key=lambda p: _avg_dist_to_group(p, group, dist))


def k_medoids_refine(clusters: list[list[int]], dist: dict, max_iterations: int = 30) -> list[list[int]]:
    """
    Tarkentaa agglomeratiivisen alkuklusteroinnin PAM-tyyppisella (Partitioning
    Around Medoids) iteraatiolla: jokainen henkilo siirretaan sen ryhman luo,
    jonka medoidiin (ryhman todellinen, olemassa oleva "keskeisin" jasen) han on
    lahinna, minka jalkeen medoidit lasketaan uudelleen. Tama korjaa average
    linkage -menetelman tunnetun heikkouden, jossa joku voi paatya ryhmaan vain
    koska sopii "keskimaarin" siihen, vaikkei olisi aidosti lahinna ketaan
    ryhman sisalla. Suppenee aina (kokonaisetaisyys medoidiin ei koskaan kasva),
    joten max_iterations on vain varmuuden vuoksi eika kaytannossa juuri koskaan
    tayty taman kokoluokan osallistujamaarilla.
    """
    clusters = [list(c) for c in clusters if c]
    if len(clusters) <= 1:
        return clusters

    medoids = [_medoid(c, dist) for c in clusters]
    current_of = {p: i for i, c in enumerate(clusters) for p in c}
    all_points = list(current_of.keys())

    for _ in range(max_iterations):
        new_clusters: list[list[int]] = [[] for _ in medoids]
        for p in all_points:
            current = current_of[p]
            # Tasapelissa (esim. kaksi identtisesti vastannutta osallistujaa)
            # suositaan nykyista ryhmaa - estaa turhan siirtelyn ja sen etta
            # jokin ryhma jaisi tyhjaksi pelkan tasapelin takia.
            best = min(
                range(len(medoids)),
                key=lambda i: (_pair_distance(dist, p, medoids[i]), i != current),
            )
            new_clusters[best].append(p)
            current_of[p] = best

        new_medoids = [
            _medoid(c, dist) if c else medoids[i] for i, c in enumerate(new_clusters)
        ]
        if new_medoids == medoids:
            return new_clusters
        medoids = new_medoids
        clusters = new_clusters

    return clusters


def target_sizes(n: int, k: int) -> list[int]:
    """Mahdollisimman tasainen jako n:sta k:hon ryhmaan, esim. n=10, k=4 -> [3,3,2,2]."""
    if k <= 0:
        return []
    base, remainder = divmod(n, k)
    return [base + 1] * remainder + [base] * (k - remainder)


def rebalance(clusters: list[list[int]], dist: dict, sizes: list[int]) -> list[list[int]]:
    """Siirtaa henkiloita ylisuurista klustereista alisuuriin kunnes koot tasmaavat tavoitteeseen."""
    clusters = [list(c) for c in clusters]
    clusters.sort(key=len, reverse=True)
    targets = sorted(sizes, reverse=True)

    while len(clusters) < len(targets):
        clusters.append([])

    max_iterations = sum(sizes) * 4 + 10
    for _ in range(max_iterations):
        over = [i for i, c in enumerate(clusters) if len(c) > targets[i]]
        if not over:
            break
        i = over[0]
        worst = max(clusters[i], key=lambda p: _avg_dist_to_group(p, clusters[i], dist))
        candidates = [j for j, c in enumerate(clusters) if len(c) < targets[j]]
        if not candidates:
            break
        best_j = min(
            candidates,
            key=lambda j: _avg_dist_to_group(worst, clusters[j], dist) if clusters[j] else 0.0,
        )
        clusters[i].remove(worst)
        clusters[best_j].append(worst)
    return clusters


def compatibility_percent(team: list[int], dist: dict) -> float:
    """Tiimin sisainen yhteensopivuus prosentteina (100 % = kaikki vastasivat identtisesti)."""
    if len(team) < 2:
        return 100.0
    total = 0.0
    count = 0
    for i, j in combinations(team, 2):
        total += _pair_distance(dist, i, j)
        count += 1
    avg_distance = total / count if count else 0.0
    return round((1 - avg_distance) * 100, 1)


def form_teams(
    participant_ids: list[int],
    answers: dict[int, dict[str, int]],
    question_ids: list[str],
    k: int = 4,
) -> tuple[list[list[int]], dict]:
    """Paafunktio: palauttaa (k osallistuja-id-ryhmaa, etaisyysmatriisi)."""
    n = len(participant_ids)
    dist = build_distance_matrix(participant_ids, answers, question_ids)
    if n == 0:
        return [[] for _ in range(k)], dist

    effective_k = min(k, n)
    clusters = agglomerative_clusters(participant_ids, dist, effective_k)
    clusters = k_medoids_refine(clusters, dist)
    sizes = target_sizes(n, k)
    balanced = rebalance(clusters, dist, sizes)
    return balanced, dist
