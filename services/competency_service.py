class CompetencyService:
    @staticmethod
    def aggregate_answers(questions, answers):
        """Return competency score percentages.

        Only attempted questions enter the denominator.
        """
        by_skill = {}

        for question in questions:
            code = question["competency_code"]
            selected = answers.get(question["code"])

            if selected is None:
                continue

            bucket = by_skill.setdefault(
                code,
                {"correct": 0, "attempted": 0},
            )

            bucket["attempted"] += 1

            if selected == question["correct_option"]:
                bucket["correct"] += 1

        return {
            code: round(
                values["correct"] / values["attempted"] * 100,
                2,
            )
            for code, values in by_skill.items()
        }

    @staticmethod
    def score_to_level(score):
        if score < 20:
            return 1
        if score < 40:
            return 2
        if score < 60:
            return 3
        if score < 80:
            return 4
        return 5
