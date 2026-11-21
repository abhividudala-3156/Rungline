import pytest

from ai.output_parser import parse_question, parse_recommendation


def test_parse_recommendation():
    result = parse_recommendation(
        '{"summary":"A useful summary here","recommendations":["Practice SQL joins"]}'
    )
    assert result["recommendations"][0] == "Practice SQL joins"


def test_reject_invalid_question():
    with pytest.raises(Exception):
        parse_question(
            '{"prompt":"Question?","options":["a","b"],"correct_option":9,"explanation":"x"}'
        )


def test_reject_duplicate_question_options():
    with pytest.raises(ValueError):
        parse_question(
            '{"prompt":"What is SQL?","options":["Database","Database"],'
            '"correct_option":0,"explanation":"SQL is used for databases."}'
        )


def test_reject_empty_question_option():
    with pytest.raises(ValueError):
        parse_question(
            '{"prompt":"What is SQL?","options":["","Database"],'
            '"correct_option":0,"explanation":"SQL is used for databases."}'
        )


def test_reject_invalid_correct_option_type():
    with pytest.raises(ValueError):
        parse_question(
            '{"prompt":"What is SQL?","options":["Database","Language"],'
            '"correct_option":true,"explanation":"SQL is used for databases."}'
        )


def test_reject_question_with_extra_fields():
    with pytest.raises(ValueError):
        parse_question(
            '{"prompt":"What is SQL?","options":["Database","Language"],'
            '"correct_option":0,"explanation":"SQL is used for databases.",'
            '"unexpected":"value"}'
        )


def test_reject_empty_recommendation():
    with pytest.raises(ValueError):
        parse_recommendation(
            '{"summary":"A useful summary here","recommendations":[""]}'
        )


def test_reject_recommendation_with_extra_fields():
    with pytest.raises(ValueError):
        parse_recommendation(
            '{"summary":"A useful summary here",'
            '"recommendations":["Practice SQL"],"unexpected":"value"}'
        )
