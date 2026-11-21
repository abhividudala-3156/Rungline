class CompetencyAnalysisAgent:
    name = "competency_analysis"

    def run(self, gap_report):
        gaps = [x for x in gap_report["skills"] if x["gap"] not in (None, 0)]
        unassessed = [x for x in gap_report["skills"] if x["gap"] is None]
        return {
            "largest_gaps": sorted(
                gaps, key=lambda x: (x["gap"], x["weight"]), reverse=True
            ),
            "unassessed": unassessed,
            "weighted_score": gap_report["weighted_score"],
        }
