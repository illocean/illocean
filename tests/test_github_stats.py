import unittest
from dataclasses import FrozenInstanceError

from github_stats import GithubStats, StatsFetchError, fetch_github_stats


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if not 200 <= self.status_code < 300:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses, failure=None):
        self.responses = iter(responses)
        self.failure = failure
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.failure:
            raise self.failure
        return next(self.responses)


class GithubStatsTests(unittest.TestCase):
    def fetch(self, session, token="test-token"):
        return fetch_github_stats("octocat", token=token, session=session)

    def test_successful_multi_page_data(self):
        page_one = [
            {"stargazers_count": 2, "language": "Python"},
            {"stargazers_count": 0, "language": "Python"},
        ]
        page_two = [{"stargazers_count": 5, "language": "Go"}]
        session = FakeSession(
            [
                FakeResponse({"name": "Octo Cat", "public_repos": 3, "followers": 4}),
                FakeResponse(page_one),
                FakeResponse(page_two),
                FakeResponse({"total_count": 6, "incomplete_results": False}),
                FakeResponse({"total_count": 7, "incomplete_results": False}),
                FakeResponse({"total_count": 8, "incomplete_results": False}),
            ]
        )

        result = self.fetch(session)

        self.assertEqual(
            result,
            GithubStats("Octo Cat", 3, 4, 7, 6, 7, 8, ("Python", "Go")),
        )
        self.assertEqual(session.calls[1][1]["params"]["page"], 1)
        self.assertEqual(session.calls[2][1]["params"]["page"], 2)
        self.assertTrue(all(call[1]["timeout"] > 0 for call in session.calls))
        self.assertEqual(session.calls[0][1]["headers"]["Authorization"], "Bearer test-token")
        with self.assertRaises(FrozenInstanceError):
            setattr(result, "repos", 99)

    def test_zero_repos_empty_languages_is_valid(self):
        session = FakeSession(
            [
                FakeResponse({"name": None, "public_repos": 0, "followers": 0}),
                FakeResponse([]),
                FakeResponse({"total_count": 0, "incomplete_results": False}),
                FakeResponse({"total_count": 0, "incomplete_results": False}),
                FakeResponse({"total_count": 0, "incomplete_results": False}),
            ]
        )

        result = self.fetch(session)

        self.assertEqual(result.name, "octocat")
        self.assertEqual(result.repos, 0)
        self.assertEqual(result.stars, 0)
        self.assertEqual(result.top_languages, ())

    def test_malformed_repository_response_fails_closed(self):
        session = FakeSession(
            [
                FakeResponse({"name": "Octo Cat", "public_repos": 1, "followers": 0}),
                FakeResponse([{"language": "Python"}]),
            ]
        )

        with self.assertRaisesRegex(StatsFetchError, "repository page 1"):
            self.fetch(session)

    def test_failed_page_raises(self):
        session = FakeSession(
            [
                FakeResponse({"name": "Octo Cat", "public_repos": 2, "followers": 0}),
                FakeResponse(
                    [
                        {"stargazers_count": 0, "language": None},
                    ]
                ),
                FakeResponse([], status_code=500),
            ]
        )

        with self.assertRaisesRegex(StatsFetchError, "repositories page 2"):
            self.fetch(session)

    def test_empty_token_fails_without_request(self):
        session = FakeSession([])
        with self.assertRaisesRegex(StatsFetchError, "GITHUB_TOKEN is required"):
            self.fetch(session, token="")
        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()
