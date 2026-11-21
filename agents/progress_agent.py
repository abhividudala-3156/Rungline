class ProgressMonitoringAgent:
    name = "progress_monitoring"

    def run(self, attempts, progress_records):
        completed = sum(1 for x in progress_records if x.get("completed"))
        latest_score = attempts[0].get("overall_score") if attempts else None
        previous_score = attempts[1].get("overall_score") if len(attempts) > 1 else None
        delta = (
            round(latest_score - previous_score, 2)
            if latest_score is not None and previous_score is not None
            else None
        )
        return {
            "completed_resources": completed,
            "latest_assessment_score": latest_score,
            "score_change": delta,
        }
