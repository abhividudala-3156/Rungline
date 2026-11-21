from agents.competency_agent import CompetencyAnalysisAgent


def test_competency_agent_separates_unknown():
    report = {
        "weighted_score": 70,
        "skills": [
            {"competency_code": "PY", "gap": 2, "weight": 0.5},
            {"competency_code": "SQL", "gap": None, "weight": 0.5},
        ],
    }
    result = CompetencyAnalysisAgent().run(report)
    assert len(result["largest_gaps"]) == 1
    assert len(result["unassessed"]) == 1
