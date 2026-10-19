"""Тесты модели Student: проверка данных и средний балл."""

import pytest

from lab.errors import ValidationError
from lab.models import Student


def test_average_of_grades():
    assert Student(1, "Иванов", [80, 90]).average == 85.0


def test_average_ignores_none():
    # Пропуск (None) не должен считаться нулём
    assert Student(1, "Иванов", [100, None, 80]).average == 90.0


def test_average_of_empty_grades_is_zero():
    assert Student(1, "Иванов", []).average == 0.0


def test_name_is_stripped():
    assert Student(1, "  Иванов Иван  ").name == "Иванов Иван"


def test_default_grades_are_not_shared():
    # У каждого студента должен быть свой список оценок
    first, second = Student(1, "А"), Student(2, "Б")
    first.grades.append(50)
    assert second.grades == []


@pytest.mark.parametrize("bad_id", [0, -5, "1", 1.5, True, None])
def test_invalid_id(bad_id):
    with pytest.raises(ValidationError):
        Student(bad_id, "Иванов")


@pytest.mark.parametrize("bad_name", ["", "   ", None, 123])
def test_invalid_name(bad_name):
    with pytest.raises(ValidationError):
        Student(1, bad_name)


@pytest.mark.parametrize("bad_grades", [[101], [-1], ["5"], [1.5], [True], "80,90"])
def test_invalid_grades(bad_grades):
    with pytest.raises(ValidationError):
        Student(1, "Иванов", bad_grades)


@pytest.mark.parametrize("edge_grades", [[0], [100], [0, None, 100]])
def test_boundary_grades_are_valid(edge_grades):
    assert Student(1, "Иванов", edge_grades).grades == edge_grades


def test_set_grades_replaces_grades():
    student = Student(1, "Иванов", [50])
    student.set_grades([70, None])
    assert student.grades == [70, None]
