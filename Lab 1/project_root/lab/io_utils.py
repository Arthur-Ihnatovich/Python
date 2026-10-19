"""Чтение, запись и экспорт студентов в CSV."""

import csv
from pathlib import Path
from typing import List, Optional, Sequence, Union

from lab.errors import CSVFormatError, StudentManagerError, ValidationError
from lab.models import Student
from lab.processing import sort_students

PathLike = Union[str, Path]


def _parse_grade(value: str, line_number: int, column_number: int) -> Optional[int]:
    """Преобразовать ячейку оценки в число или None."""
    value = value.strip()
    if not value:
        return None

    try:
        grade = int(value)
    except ValueError:
        raise CSVFormatError(
            f"Строка {line_number}, колонка {column_number}: оценка должна быть целым числом."
        ) from None

    if not 0 <= grade <= 100:
        raise CSVFormatError(
            f"Строка {line_number}, колонка {column_number}: оценка должна быть от 0 до 100."
        )
    return grade


def _is_header(row: Sequence[str]) -> bool:
    """Определить заголовок по первым двум ячейкам: id,name."""
    return len(row) >= 2 and row[0].strip().lstrip("\ufeff").lower() == "id" \
        and row[1].strip().lower() == "name"


def parse_rows(rows: Sequence[Sequence[str]]) -> List[Student]:
    """Преобразовать строки CSV в студентов и проверить данные."""
    students: List[Student] = []
    seen_ids = set()
    has_checked_first_row = False

    for line_number, row in enumerate(rows, start=1):
        # Пропускаем полностью пустые строки.
        if not row or not any(cell.strip() for cell in row):
            continue

        if not has_checked_first_row:
            has_checked_first_row = True
            if _is_header(row):
                continue

        if len(row) < 2:
            raise CSVFormatError(f"Строка {line_number}: нужны как минимум ID и имя.")

        id_text = row[0].strip()
        try:
            student_id = int(id_text)
        except ValueError:
            raise CSVFormatError(
                f"Строка {line_number}: ID должен быть целым числом."
            ) from None

        grades = [
            _parse_grade(value, line_number, column_number)
            for column_number, value in enumerate(row[2:], start=3)
        ]

        try:
            student = Student(student_id, row[1], grades)
        except ValidationError as exc:
            raise CSVFormatError(f"Строка {line_number}: {exc}") from exc

        if student.id in seen_ids:
            raise CSVFormatError(f"Строка {line_number}: ID {student.id} повторяется.")

        seen_ids.add(student.id)
        students.append(student)

    return students


def load_students_csv(path: PathLike) -> List[Student]:
    """Загрузить студентов из CSV с заголовком или без него."""
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.reader(file))
    except OSError as exc:
        if isinstance(exc, FileNotFoundError):
            message = f"Файл не найден: {path}"
        elif isinstance(exc, PermissionError):
            message = f"Нет прав для чтения файла: {path}"
        else:
            message = f"Не удалось прочитать файл {path}: {exc}"
        raise StudentManagerError(message) from exc
    except (csv.Error, UnicodeError) as exc:
        raise CSVFormatError(f"Не удалось разобрать CSV-файл {path}: {exc}") from exc

    return parse_rows(rows)


def _write_rows(path: PathLike, rows: List[List[object]]) -> None:
    """Записать подготовленные строки в CSV."""
    try:
        with open(path, "w", encoding="utf-8", newline="") as file:
            csv.writer(file).writerows(rows)
    except OSError as exc:
        if isinstance(exc, PermissionError):
            message = f"Нет прав для записи файла: {path}"
        else:
            message = f"Не удалось записать файл {path}: {exc}"
        raise StudentManagerError(message) from exc
    except (csv.Error, UnicodeError) as exc:
        raise StudentManagerError(f"Не удалось записать CSV-файл {path}: {exc}") from exc


def save_students_csv(students: Sequence[Student], path: PathLike) -> None:
    """Сохранить студентов; строки дополняются пустыми ячейками до общей длины."""
    grade_count = max((len(student.grades) for student in students), default=0)
    rows: List[List[object]] = [
        ["id", "name"] + [f"grade{i}" for i in range(1, grade_count + 1)]
    ]

    for student in students:
        grades = list(student.grades)
        grades.extend([None] * (grade_count - len(grades)))
        grades = ["" if grade is None else grade for grade in grades]
        rows.append([student.id, student.name] + grades)

    _write_rows(path, rows)


def export_top_students_csv(
    students: Sequence[Student], count: int, path: PathLike
) -> None:
    """Экспортировать N студентов с самым высоким средним баллом."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValidationError("Количество студентов N должно быть целым неотрицательным числом.")

    top_students = sort_students(list(students), "avg")[:count]
    rows: List[List[object]] = [["id", "name", "average", "grades"]]

    for student in top_students:
        grades = " ".join(
            str(grade) for grade in student.grades if grade is not None
        )
        rows.append([student.id, student.name, f"{student.average:.2f}", grades])

    _write_rows(path, rows)
