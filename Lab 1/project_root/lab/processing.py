"""Функции обработки, сортировки и статистики студентов."""

from typing import Dict, List, Optional

from lab.errors import DuplicateStudentError, StudentNotFoundError, ValidationError
from lab.models import Student


def add_student(students: List[Student], student: Student) -> None:
    """Добавить студента, если его ID ещё не используется."""
    # any() возвращает True, если хотя бы один элемент последовательности истинный.
    if any(existing.id == student.id for existing in students):
        raise DuplicateStudentError(f"Студент с ID {student.id} уже существует.")
    students.append(student)


def find_student(students: List[Student], student_id: int) -> Student:
    """Найти студента по ID или сообщить об отсутствии."""
    for student in students:
        if student.id == student_id:
            return student
    raise StudentNotFoundError(f"Студент с ID {student_id} не найден.")


def remove_student(students: List[Student], student_id: int) -> Student:
    """Удалить студента по ID и вернуть удалённый объект."""
    student = find_student(students, student_id)
    students.remove(student)
    return student


def update_student_grades(
    students: List[Student], student_id: int, grades: List[Optional[int]]
) -> Student:
    """Заменить оценки студента по ID."""
    student = find_student(students, student_id)
    student.set_grades(grades)
    return student


def sort_students(students: List[Student], sort_by: str = "avg") -> List[Student]:
    """Вернуть отсортированную копию списка по avg, name или id."""
    if sort_by == "avg":
        return sorted(students, key=lambda student: (-student.average, student.name.casefold()))
    if sort_by == "name":
        return sorted(students, key=lambda student: student.name.casefold())
    if sort_by == "id":
        return sorted(students, key=lambda student: student.id)
    raise ValidationError("Критерий сортировки должен быть avg, name или id.")


def filter_students(
    students: List[Student],
    name_contains: str = "",
    min_average: Optional[float] = None,
    max_average: Optional[float] = None,
) -> List[Student]:
    """Отфильтровать студентов по фрагменту имени и диапазону среднего балла."""
    if min_average is not None and max_average is not None and min_average > max_average:
        raise ValidationError("Минимальный средний балл не может быть больше максимального.")
    fragment = name_contains.strip().casefold()
    result = []
    for student in students:
        if fragment and fragment not in student.name.casefold():
            continue
        if min_average is not None and student.average < min_average:
            continue
        if max_average is not None and student.average > max_average:
            continue
        result.append(student)
    return result


def group_statistics(students: List[Student]) -> Dict[str, object]:
    """
    Рассчитать число студентов, общий средний балл, лучшего и худшего.

    Общий средний балл считается по всем фактически имеющимся оценкам,
    а не как среднее арифметическое индивидуальных средних.
    """
    all_grades = [grade for student in students for grade in student.grades if grade is not None]
    overall_average = sum(all_grades) / len(all_grades) if all_grades else 0.0
    if not students:
        best = None
        worst = None
    else:
        best = min(students, key=lambda student: (-student.average, student.name.casefold()))
        worst = min(students, key=lambda student: (student.average, student.name.casefold()))
    return {
        "count": len(students),
        "overall_avg": overall_average,
        "best": best,
        "worst": worst,
    }
