"""Shared profile content for every terminal theme."""

from types import MappingProxyType


# Declared working categories, not rankings or proficiency claims.
PROFILE_CATEGORIES = MappingProxyType(
    {
        "Languages": ("PHP", "Python", "Java", "C/C++", "COBOL"),
        "Frameworks & Tools": (
            "Laravel",
            "Livewire",
            "Spring Boot",
            "Filament",
            "Alpine.js",
            "Tailwind CSS",
            "Git/GitHub",
        ),
        "Databases": ("PostgreSQL", "MySQL", "SQLite"),
        "AI & Workflow": (
            "MCP servers",
            "prompt engineering",
            "skill-based tool chaining",
            "agentic orchestration",
        ),
    }
)


def profile_lines() -> tuple[str, ...]:
    """Return ordered profile lines wrapped for the 700px terminal."""
    label_width = max(len(label) for label in PROFILE_CATEGORIES) + 2
    lines = []
    for label, values in PROFILE_CATEGORIES.items():
        continuation = []
        current = ""
        for value in values:
            candidate = f"{current}, {value}" if current else value
            if current and len(candidate) > 80 - label_width:
                continuation.append(current)
                current = value
            else:
                current = candidate
        if current:
            continuation.append(current)
        for index, value in enumerate(continuation):
            prefix = f"{label}:" if index == 0 else ""
            lines.append(f"{prefix.ljust(label_width)}{value}")
    return tuple(lines)
