"""Общие фикстуры: заготовки данных, которые используются сразу в нескольких тестах."""

import pytest

from lab.models import Student


@pytest.fixture
def students():
    """Три студента с разными средними баллами: Петров 90, Алексеев 70, Борисов 70."""
    return [
        Student(1, "Петров Пётр", [90, 90]),
        Student(2, "Борисов Борис", [60, 80]),
        Student(3, "Алексеев Алексей", [70, 70]),
    ]


@pytest.fixture
def csv_file(tmp_path):
    """Временный CSV-файл с заголовком (tmp_path — временная папка от pytest)."""
    path = tmp_path / "students.csv"
    path.write_text(
        "id,name,grade1,grade2,grade3\n"
        "1,Иванов Иван,78,85,90\n"
        "2,Иванов Петр,65,70,0\n"
        "4,Иванов Олег,100,90,\n",
        encoding="utf-8",
    )
    return path
