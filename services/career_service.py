from database.repositories.career_repository import CareerRepository


class CareerService:
    def __init__(self, db):
        self.repo = CareerRepository(db)

    def list_careers(self):
        return self.repo.list_careers()

    def requirements(self, career_code):
        career = self.repo.get_career(career_code)
        if not career:
            raise ValueError("Career not found.")
        mappings = self.repo.get_requirements(career_code)
        competencies = self.repo.get_competencies()
        return [
            {**m, "competency": competencies.get(m["competency_code"], {})}
            for m in mappings
        ]
