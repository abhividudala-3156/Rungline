import pytest
from pydantic import ValidationError

from models.learning_path import LearningPath


def valid_learning_path():
    return {
        "career_code": "PYTHON_DEV",
        "summary": "A structured learning roadmap for Python development.",
        "steps": [
            {
                "competency_code": "PYTHON",
                "title": "Python Fundamentals",
                "objective": "Learn Python programming fundamentals.",
                "activities": [
                    "Study variables and data types",
                    "Practice conditional statements",
                ],
                "resource_urls": ["https://docs.python.org/3/tutorial/"],
                "estimated_hours": 10,
                "priority": 9,
            }
        ],
    }


def test_valid_learning_path():
    result = LearningPath.model_validate(valid_learning_path())

    assert result.career_code == "PYTHON_DEV"
    assert len(result.steps) == 1


def test_reject_empty_summary():
    data = valid_learning_path()
    data["summary"] = ""

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_reject_more_than_30_steps():
    data = valid_learning_path()
    data["steps"] = data["steps"] * 31

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_reject_more_than_15_activities():
    data = valid_learning_path()
    data["steps"][0]["activities"] = ["Activity"] * 16

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_reject_activity_over_500_characters():
    data = valid_learning_path()
    data["steps"][0]["activities"] = ["A" * 501]

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_reject_more_than_10_resource_urls():
    data = valid_learning_path()
    data["steps"][0]["resource_urls"] = ["https://example.com/resource"] * 11

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_reject_resource_url_over_2048_characters():
    data = valid_learning_path()
    data["steps"][0]["resource_urls"] = ["https://" + "a" * 2041]

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_reject_extra_learning_path_fields():
    data = valid_learning_path()
    data["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        LearningPath.model_validate(data)


def test_default_lists_are_independent():
    first = LearningPath.model_validate(valid_learning_path())
    second = LearningPath.model_validate(valid_learning_path())

    first.steps[0].activities.append("Additional activity")

    assert "Additional activity" not in second.steps[0].activities
