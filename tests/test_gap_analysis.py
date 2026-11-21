from services.gap_analysis_service import GapAnalysisService


def test_gap_analysis_keeps_unassessed_distinct():
    reqs = [
        {
            "competency_code": "PY",
            "required_level": 4,
            "weight": 0.5,
            "competency": {"name": "Python"},
        },
        {
            "competency_code": "SQL",
            "required_level": 3,
            "weight": 0.5,
            "competency": {"name": "SQL"},
        },
    ]
    result = GapAnalysisService().analyze(reqs, {"PY": 85})
    assert result["skills"][0]["current_level"] == 5
    assert result["skills"][0]["gap"] == 0
    assert result["skills"][1]["status"] == "Not assessed"
    assert result["assessed_skills"] == 1
