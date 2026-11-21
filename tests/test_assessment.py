from services.competency_service import CompetencyService


def test_skill_scores_exclude_unanswered():
    questions = [
        {"code": "q1", "competency_code": "PY", "correct_option": 1},
        {"code": "q2", "competency_code": "PY", "correct_option": 0},
        {"code": "q3", "competency_code": "SQL", "correct_option": 2},
    ]
    assert CompetencyService.aggregate_answers(questions, {"q1": 1, "q2": 1}) == {
        "PY": 50.0
    }
