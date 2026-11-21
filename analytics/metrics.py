def completion_rate(progress_records):
    if not progress_records:
        return 0.0
    return round(
        100
        * sum(bool(x.get("completed")) for x in progress_records)
        / len(progress_records),
        1,
    )


def average_assessment_score(attempts):
    scores = [
        x["overall_score"] for x in attempts if x.get("overall_score") is not None
    ]
    return round(sum(scores) / len(scores), 1) if scores else None
