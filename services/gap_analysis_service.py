from services.competency_service import CompetencyService


class GapAnalysisService:
    def analyze(self, requirements, skill_scores):
        rows, weighted_score, weight_total = [], 0.0, 0.0
        for req in requirements:
            code = req["competency_code"]
            current_score = skill_scores.get(code)
            required_level = int(req["required_level"])
            weight = float(req["weight"])
            if current_score is None:
                rows.append(
                    {
                        "competency_code": code,
                        "name": req.get("competency", {}).get("name", code),
                        "required_level": required_level,
                        "current_level": None,
                        "gap": None,
                        "weight": weight,
                        "status": "Not assessed",
                    }
                )
                continue
            current_level = self._score_to_level(current_score)
            gap = max(0, required_level - current_level)
            rows.append(
                {
                    "competency_code": code,
                    "name": req.get("competency", {}).get("name", code),
                    "required_level": required_level,
                    "current_level": current_level,
                    "gap": gap,
                    "weight": weight,
                    "status": "Gap identified" if gap else "Meets target",
                }
            )
            weighted_score += (current_level / 5) * 100 * weight
            weight_total += weight
        return {
            "skills": rows,
            "weighted_score": round(weighted_score / weight_total, 2)
            if weight_total
            else None,
            "assessed_skills": sum(r["current_level"] is not None for r in rows),
            "total_skills": len(rows),
        }

    @staticmethod
    def _score_to_level(score):
        return CompetencyService.score_to_level(score)
