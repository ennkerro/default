"""
Muuntaa klusterointialgoritmin tuottamat ryhmat lopullisiksi joukkuetuloksiksi:
nimi, jasenet, "Miksi juuri te?" -perustelut ja loppukaneetti.
"""
import random
from collections import Counter

from app.clustering import compatibility_percent
from app.content import (
    CLOSING_DIAGNOSES,
    GENERIC_FALLBACK_TEMPLATE,
    NAME_TEMPLATES,
    TEAM_EMOJIS,
)


def _format_percent(value: float) -> str:
    """98.4 -> '98,4' (suomalainen desimaalierotin)."""
    return f"{value}".replace(".", ",")


def _score_questions(
    team: list[int],
    others: list[int],
    answers: dict[int, dict[str, int]],
    questions: list[dict],
) -> list[dict]:
    """
    Pisteyttaa jokaisen kysymyksen sen mukaan kuinka ERITTAIN TAMAN joukkueen
    vastaus poikkeaa muista joukkueista ("lift"), ei vain kuinka yhtenainen
    (konsensus) joukkueen oma vastaus on. Pelkka korkea konsensus ei riita
    hyvaksi perusteluksi, jos kaikki muutkin joukkueet vastasivat samoin
    samaan kysymykseen - silloin kysymys ei aidosti erota tata joukkuetta
    muista, vaikka konsensus olisi korkea. Lift on siis paapaino (85 %),
    konsensus vain pieni tasapainoerotin (15 %) - tama estaa samojen
    yleisesti-suosittujen kysymysten toistumisen joka joukkueen selityksissa.
    Palauttaa listan suurimmasta pienimpaan pisteeseen.
    """
    scored = []
    for q in questions:
        qid = q["id"]
        team_choices = [answers[pid][qid] for pid in team if qid in answers.get(pid, {})]
        if not team_choices:
            continue
        counts = Counter(team_choices)
        top_option, top_count = counts.most_common(1)[0]
        team_ratio = top_count / len(team_choices)

        other_choices = [answers[pid][qid] for pid in others if qid in answers.get(pid, {})]
        other_ratio = (
            sum(1 for c in other_choices if c == top_option) / len(other_choices)
            if other_choices
            else 0.0
        )
        lift = team_ratio - other_ratio
        score = lift * 0.85 + team_ratio * 0.15
        scored.append(
            {
                "score": score,
                "question": q,
                "option_index": top_option,
                "count": top_count,
                "total": len(team_choices),
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def _build_reason(entry: dict) -> str:
    question = entry["question"]
    option = question["options"][entry["option_index"]]
    count = entry["count"]
    percent = round(count / entry["total"] * 100, 1) if entry["total"] else 0.0
    template = option.get("vibe_line") or GENERIC_FALLBACK_TEMPLATE
    return template.format(
        count=count,
        total=entry["total"],
        percent=_format_percent(percent),
        question=question["text"],
        option=option["text"],
        # Suomen kielioppi: "1 henkilö" (nominatiivi) mutta "2 henkilöä" (partitiivi) -
        # nama taytetaan oikein taivutettuina, jotta vibe_line-tekstit pysyvat
        # kieliopillisesti oikeina myos silloin kun count on 1.
        henkilo_sana="henkilö" if count == 1 else "henkilöä",
        osallistuja_sana="osallistuja" if count == 1 else "osallistujaa",
    )


def _generate_name(top_tag: str, used_names: set[str], rng: random.Random) -> str:
    tag_cap = top_tag[:1].upper() + top_tag[1:]
    templates = NAME_TEMPLATES.copy()
    rng.shuffle(templates)
    for template in templates:
        name = template.format(Tag=tag_cap, tag=top_tag)
        if name not in used_names:
            return name
    return f"{tag_cap}-joukkue"


def generate_teams(
    clusters: list[list[int]],
    answers: dict[int, dict[str, int]],
    questions: list[dict],
    names_by_id: dict[int, str],
    dist: dict,
    seed: int | None = None,
) -> list[dict]:
    """Muodostaa lopulliset, esityskelpoiset joukkuetulokset."""
    rng = random.Random(seed)
    used_names: set[str] = set()
    available_diagnoses = CLOSING_DIAGNOSES.copy()
    rng.shuffle(available_diagnoses)

    results = []
    team_number = 0
    for cluster in clusters:
        if not cluster:
            continue
        team_number += 1
        cluster_set = set(cluster)
        others = [pid for other in clusters for pid in other if pid not in cluster_set]

        scored = _score_questions(cluster, others, answers, questions)
        num_content_reasons = min(rng.randint(3, 4), len(scored))
        reasons = [_build_reason(entry) for entry in scored[:num_content_reasons]]

        # Yhteensopivuusprosentti ei enaa toistu tekstirivina taalla - se
        # esitetaan omana visuaalisena mittarinaan kortissa (compatibility_percent
        # -kentan kautta), joten teksti- ja lukurivi eivat sano samaa asiaa kahdesti.
        compat = compatibility_percent(cluster, dist)

        top_tag = scored[0]["question"]["options"][scored[0]["option_index"]]["tag"] if scored else "vibe"
        name = _generate_name(top_tag, used_names, rng)
        used_names.add(name)

        diagnosis = available_diagnoses[(team_number - 1) % len(available_diagnoses)]

        results.append(
            {
                "index": team_number,
                "emoji": TEAM_EMOJIS[(team_number - 1) % len(TEAM_EMOJIS)],
                "name": name,
                "members": [names_by_id[pid] for pid in cluster],
                "member_ids": list(cluster),
                "reasons": reasons,
                "diagnosis": diagnosis,
                "compatibility_percent": compat,
            }
        )
    return results
