class CareerRepository:
    def __init__(self, db):
        self.careers = db.careers
        self.competencies = db.competencies
        self.mappings = db.career_competencies
        self.resources = db.learning_resources

    def list_careers(self):
        return list(self.careers.find({"is_active": True}).sort("title", 1))

    def get_career(self, code):
        if not isinstance(code, str) or not code.strip():
            return None

        return self.careers.find_one(
            {
                "code": code.strip(),
                "is_active": True,
            }
        )

    def get_requirements(self, code):
        return list(self.mappings.find({"career_code": code}).sort("weight", -1))

    def get_competencies(self):
        return {item["code"]: item for item in self.competencies.find({})}

    def get_resources(self, competency_codes=None):
        query = {"is_active": True}

        if competency_codes is not None:
            query["competency_code"] = {"$in": list(competency_codes)}

        return list(self.resources.find(query))
