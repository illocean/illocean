import re
import unittest
from pathlib import Path

from profile_content import PROFILE_CATEGORIES, profile_lines


class ProfileContentTests(unittest.TestCase):
    def test_exact_sections_order_and_items(self):
        self.assertEqual(
            list(PROFILE_CATEGORIES.items()),
            [
                ("Languages", ("PHP", "Python", "Java", "C/C++", "COBOL")),
                (
                    "Frameworks & Tools",
                    (
                        "Laravel",
                        "Livewire",
                        "Spring Boot",
                        "Filament",
                        "Alpine.js",
                        "Tailwind CSS",
                        "Git/GitHub",
                    ),
                ),
                ("Databases", ("PostgreSQL", "MySQL", "SQLite")),
                (
                    "AI & Workflow",
                    (
                        "MCP servers",
                        "prompt engineering",
                        "skill-based tool chaining",
                        "agentic orchestration",
                    ),
                ),
            ],
        )

    def test_no_legacy_entries(self):
        items = [
            value
            for values in PROFILE_CATEGORIES.values()
            for value in values
        ]
        text = " ".join(items)
        for legacy in (
            "Cloud",
            "DevOps",
            "Monitoring",
            "MongoDB",
            "HTML",
            "Node.js",
        ):
            self.assertNotRegex(text, rf"\b{re.escape(legacy)}\b")
        self.assertNotRegex(text, r"(?<!\w)\.NET(?!\w)")
        for item in items:
            if item != "Tailwind CSS":
                self.assertNotRegex(item, r"\bCSS\b")

    def test_every_category_first_line_has_label_and_value_prefix(self):
        lines = iter(profile_lines())
        label_width = max(len(label) for label in PROFILE_CATEGORIES) + 2
        for label in PROFILE_CATEGORIES:
            for line in lines:
                if line.startswith(label):
                    self.assertEqual(
                        line[:label_width], f"{label}: ".ljust(label_width)
                    )
                    self.assertTrue(line[label_width:].strip(), label)
                    break
            else:
                self.fail(f"missing first line for {label}")

    def test_generators_use_shared_profile_source(self):
        root = Path(__file__).resolve().parents[1]
        for name in (
            "generate_debian.py",
            "generate_liquid_glass.py",
            "generate_with_stats.py",
        ):
            source = (root / name).read_text(encoding="utf-8")
            self.assertIn("from profile_content import profile_lines", source, name)
            self.assertRegex(source, r"(?m)^profile = profile_lines\(\)$", name)
            self.assertNotRegex(source, r"(?m)^(?:SKILL_LABELS|skills) = \[$", name)

    def test_lines_are_readable_after_ansi_removal(self):
        lines = profile_lines()
        ansi = re.compile(r"\x1b\[[0-9;]*m")
        self.assertTrue(lines)
        for line in lines:
            visible = ansi.sub("", line)
            self.assertLessEqual(len(visible), 80, visible)

    def test_items_are_not_split_across_lines(self):
        lines = profile_lines()
        for values in PROFILE_CATEGORIES.values():
            for item in values:
                self.assertTrue(any(item in line for line in lines), item)


if __name__ == "__main__":
    unittest.main()
