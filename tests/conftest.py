
class FakeCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        from types import SimpleNamespace

        doc = dict(doc)
        doc.setdefault("_id", str(len(self.docs) + 1))
        self.docs.append(doc)
        return SimpleNamespace(inserted_id=doc["_id"])

    def find_one(self, query):
        return next(
            (
                d
                for d in self.docs
                if all(d.get(k) == v for k, v in query.items())
            ),
            None,
        )

    def count_documents(self, query):
        return sum(
            1
            for doc in self.docs
            if all(doc.get(k) == v for k, v in query.items())
        )


class FakeDB:
    def __init__(self):
        for name in [
            "users",
            "careers",
            "competencies",
            "career_competencies",
            "questions",
            "assessment_attempts",
            "competency_profiles",
            "learning_paths",
            "learning_resources",
            "learning_progress",
            "notifications",
            "ai_interactions",
            "organizations",
            "audit_logs",
        ]:
            setattr(self, name, FakeCollection())

        self._collections = {
            n: getattr(self, n)
            for n in [
                "users",
                "careers",
                "competencies",
                "career_competencies",
                "questions",
                "assessment_attempts",
                "competency_profiles",
                "learning_paths",
                "learning_resources",
                "learning_progress",
                "notifications",
                "ai_interactions",
                "organizations",
                "audit_logs",
            ]
        }

    def __getitem__(self, key):
        return self._collections[key]
