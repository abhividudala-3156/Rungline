from analytics.metrics import average_assessment_score, completion_rate


def learner_summary(attempts, progress_records):
    return {
        "attempt_count": len(attempts),
        "average_score": average_assessment_score(attempts),
        "completion_rate": completion_rate(progress_records),
        "completed_resources": sum(bool(x.get("completed")) for x in progress_records),
    }
