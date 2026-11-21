from database.repositories.career_repository import CareerRepository


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(
            key=lambda item: item.get(field),
            reverse=direction == -1,
        )
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    def find(self, query):
        def matches(document):
            for key, value in query.items():
                if isinstance(value, dict) and "$in" in value:
                    if document.get(key) not in value["$in"]:
                        return False
                elif document.get(key) != value:
                    return False
            return True

        return FakeCursor([item for item in self.documents if matches(item)])

    def find_one(self, query):
        return next(
            (
                item
                for item in self.documents
                if all(item.get(key) == value for key, value in query.items())
            ),
            None,
        )


class FakeDB:
    def __init__(self):
        self.careers = FakeCollection(
            [
                {"code": "DATA_ANALYST", "title": "Data Analyst", "is_active": True},
                {"code": "WEB_DEV", "title": "Web Developer", "is_active": True},
                {"code": "OLD_CAREER", "title": "Old Career", "is_active": False},
            ]
        )

        self.competencies = FakeCollection(
            [
                {"code": "PYTHON", "name": "Python Programming"},
                {"code": "SQL", "name": "SQL and Databases"},
            ]
        )

        self.career_competencies = FakeCollection(
            [
                {
                    "career_code": "DATA_ANALYST",
                    "competency_code": "PYTHON",
                    "weight": 2,
                },
                {
                    "career_code": "DATA_ANALYST",
                    "competency_code": "SQL",
                    "weight": 3,
                },
            ]
        )

        self.learning_resources = FakeCollection(
            [
                {
                    "code": "R1",
                    "competency_code": "PYTHON",
                    "is_active": True,
                },
                {
                    "code": "R2",
                    "competency_code": "SQL",
                    "is_active": False,
                },
            ]
        )


def test_get_career_returns_active_career():
    repository = CareerRepository(FakeDB())

    career = repository.get_career("DATA_ANALYST")

    assert career is not None
    assert career["title"] == "Data Analyst"


def test_get_career_rejects_inactive_career():
    repository = CareerRepository(FakeDB())

    assert repository.get_career("OLD_CAREER") is None


def test_get_career_rejects_invalid_code():
    repository = CareerRepository(FakeDB())

    assert repository.get_career("") is None
    assert repository.get_career("   ") is None
    assert repository.get_career(None) is None
    assert repository.get_career(123) is None


def test_get_career_strips_whitespace():
    repository = CareerRepository(FakeDB())

    career = repository.get_career(" DATA_ANALYST ")

    assert career is not None
    assert career["code"] == "DATA_ANALYST"


def test_list_careers_excludes_inactive_careers():
    repository = CareerRepository(FakeDB())

    careers = repository.list_careers()

    assert len(careers) == 2
    assert all(career["is_active"] for career in careers)


def test_list_careers_sorts_by_title():
    repository = CareerRepository(FakeDB())

    careers = repository.list_careers()

    titles = [career["title"] for career in careers]

    assert titles == sorted(titles)


def test_get_requirements_sorts_by_weight():
    repository = CareerRepository(FakeDB())

    requirements = repository.get_requirements("DATA_ANALYST")

    weights = [item["weight"] for item in requirements]

    assert weights == [3, 2]


def test_get_competencies_returns_code_mapping():
    repository = CareerRepository(FakeDB())

    competencies = repository.get_competencies()

    assert "PYTHON" in competencies
    assert competencies["PYTHON"]["name"] == "Python Programming"


def test_get_resources_excludes_inactive_resources():
    repository = CareerRepository(FakeDB())

    resources = repository.get_resources()

    assert len(resources) == 1
    assert resources[0]["code"] == "R1"


def test_get_resources_filters_by_competency():
    repository = CareerRepository(FakeDB())

    resources = repository.get_resources(["PYTHON"])

    assert len(resources) == 1
    assert resources[0]["competency_code"] == "PYTHON"
