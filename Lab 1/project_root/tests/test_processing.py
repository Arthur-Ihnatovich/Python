"""Тесты функций обработки: добавление, удаление, сортировка, фильтрация, статистика."""

import pytest

from lab.errors import DuplicateStudentError, StudentNotFoundError, ValidationError
from lab.models import Student
from lab.processing import (
    add_student,
    filter_students,
    find_student,
    group_statistics,
    remove_student,
    sort_students,
    update_student_grades,
)


# ---------- добавление / поиск / удаление / обновление ----------

def test_add_student(students):
    add_student(students, Student(10, "Новый Студент"))
    assert len(students) == 4


def test_add_duplicate_id_raises(students):
    with pytest.raises(DuplicateStudentError):
        add_student(students, Student(1, "Другой Человек"))


def test_find_student(students):
    assert find_student(students, 2).name == "Борисов Борис"


def test_find_missing_student_raises(students):
    with pytest.raises(StudentNotFoundError):
        find_student(students, 999)


def test_remove_student(students):
    removed = remove_student(students, 1)
    assert removed.name == "Петров Пётр"
    assert len(students) == 2


def test_remove_missing_student_raises(students):
    with pytest.raises(StudentNotFoundError):
        remove_student(students, 999)


def test_update_grades(students):
    update_student_grades(students, 1, [100, 100])
    assert find_student(students, 1).average == 100.0


def test_update_grades_missing_student_raises(students):
    with pytest.raises(StudentNotFoundError):
        update_student_grades(students, 999, [50])


def test_update_grades_invalid_grades_raises(students):
    with pytest.raises(ValidationError):
        update_student_grades(students, 1, [200])


# ---------- сортировка ----------

def test_sort_by_avg_desc_then_name(students):
    # Петров (90) первый; у Алексеева и Борисова по 70 — между ними по имени
    result = sort_students(students, "avg")
    assert [s.id for s in result] == [1, 3, 2]


def test_sort_by_name(students):
    assert [s.id for s in sort_students(students, "name")] == [3, 2, 1]


def test_sort_by_id(students):
    assert [s.id for s in sort_students(students, "id")] == [1, 2, 3]


def test_sort_does_not_change_original(students):
    sort_students(students, "name")
    assert [s.id for s in students] == [1, 2, 3]


def test_sort_unknown_key_raises(students):
    with pytest.raises(ValidationError):
        sort_students(students, "weight")


# ---------- фильтрация ----------

def test_filter_by_name_ignores_case(students):
    assert [s.id for s in filter_students(students, "ПЕТРОВ")] == [1]


def test_filter_by_min_average(students):
    assert [s.id for s in filter_students(students, min_average=80)] == [1]


def test_filter_by_max_average(students):
    assert [s.id for s in filter_students(students, max_average=70)] == [2, 3]


def test_filter_without_conditions_returns_all(students):
    assert len(filter_students(students)) == 3


def test_filter_wrong_range_raises(students):
    with pytest.raises(ValidationError):
        filter_students(students, min_average=90, max_average=10)


# ---------- статистика ----------

def test_group_statistics(students):
    stats = group_statistics(students)
    assert stats["count"] == 3
    assert stats["overall_avg"] == pytest.approx(76.666, abs=0.01)
    assert stats["best"].id == 1
    assert stats["worst"].id == 3  # при равенстве 70 и 70 выбирается по имени


def test_group_statistics_empty_list():
    stats = group_statistics([])
    assert stats == {"count": 0, "overall_avg": 0.0, "best": None, "worst": None}


def test_overall_average_is_by_all_grades():
    # Среднее по всем оценкам: (100 + 0 + 0 + 0) / 4 = 25,
    # а не среднее средних: (100 + 0) / 2 = 50
    group = [Student(1, "А", [100]), Student(2, "Б", [0, 0, 0])]
    assert group_statistics(group)["overall_avg"] == 25.0
