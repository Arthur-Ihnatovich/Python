"""Консольное меню приложения. Запуск: python -m lab.main"""

from pathlib import Path
from typing import Callable, Dict, List, Optional

from lab.errors import StudentManagerError, ValidationError
from lab.io_utils import export_top_students_csv, load_students_csv, save_students_csv
from lab.models import Student
from lab.processing import (
    add_student,
    filter_students,
    group_statistics,
    remove_student,
    sort_students,
    update_student_grades,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_CSV = DATA_DIR / "students.csv"
DEFAULT_TOP_CSV = DATA_DIR / "top_students.csv"

MENU = """
StudentManager:
1. Загрузить из CSV
2. Сохранить в CSV
3. Показать всех студентов
4. Добавить студента
5. Удалить студента по ID
6. Обновить оценки по ID
7. Статистика по группе
8. Экспорт ТОП-N в CSV
9. Сортировка (avg/name/id)
10. Фильтрация студентов
0. Выход
"""


def format_students(students: List[Student]) -> str:
    """Подготовить таблицу студентов для печати."""
    if not students:
        return "Список студентов пуст."

    header = f"{'ID':<6} {'ФИО':<30} {'Средний балл':>13}  Оценки"
    lines = [header, "-" * len(header)]
    for student in students:
        grades = ", ".join(
            "—" if grade is None else str(grade) for grade in student.grades
        )
        lines.append(
            f"{student.id:<6} {student.name:<30} "
            f"{student.average:>13.2f}  {grades}"
        )
    return "\n".join(lines)


def ask_path(prompt: str, default: Path) -> Path:
    """Запросить путь к файлу; Enter означает путь по умолчанию."""
    value = input(f"{prompt} [{default}]: ").strip()
    return Path(value) if value else default


def ask_int(prompt: str, minimum: Optional[int] = None) -> int:
    """Запросить целое число и проверить минимальное значение."""
    value = input(prompt).strip()
    try:
        number = int(value)
    except ValueError:
        raise ValidationError("Введите целое число.") from None

    if minimum is not None and number < minimum:
        raise ValidationError(f"Число должно быть не меньше {minimum}.")
    return number


def ask_grades() -> List[Optional[int]]:
    """Считать оценки через запятую; пустая ячейка означает пропуск."""
    value = input("Оценки через запятую (например, 80, 90; пропуск — пустая часть): ")
    if not value.strip():
        return []

    grades: List[Optional[int]] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            grades.append(None)
            continue
        try:
            grade = int(part)
        except ValueError:
            raise ValidationError(f"'{part}' не является целой оценкой.") from None
        if not 0 <= grade <= 100:
            raise ValidationError("Оценка должна быть от 0 до 100.")
        grades.append(grade)
    return grades


# Действия меню вынесены в отдельные функции, чтобы основной цикл был коротким.
def action_load(students: List[Student]) -> None:
    loaded = load_students_csv(ask_path("Путь к CSV", DEFAULT_CSV))
    students[:] = loaded
    print(f"Загружено студентов: {len(students)}")


def action_save(students: List[Student]) -> None:
    path = ask_path("Куда сохранить", DEFAULT_CSV)
    save_students_csv(students, path)
    print(f"Сохранено студентов: {len(students)} -> {path}")


def action_show(students: List[Student]) -> None:
    print(format_students(students))


def action_add(students: List[Student]) -> None:
    student_id = ask_int("ID нового студента: ", minimum=1)
    name = input("ФИО: ").strip()
    student = Student(student_id, name, ask_grades())
    add_student(students, student)
    print("Студент добавлен.")


def action_remove(students: List[Student]) -> None:
    student_id = ask_int("ID студента для удаления: ", minimum=1)
    removed = remove_student(students, student_id)
    print(f"Удалён студент: {removed.name}")


def action_update(students: List[Student]) -> None:
    student_id = ask_int("ID студента: ", minimum=1)
    student = update_student_grades(students, student_id, ask_grades())
    print(f"Оценки обновлены: {student.name}")


def action_statistics(students: List[Student]) -> None:
    stats = group_statistics(students)
    print(f"Количество студентов: {stats['count']}")
    print(f"Общий средний балл по всем оценкам: {stats['overall_avg']:.2f}")

    if stats["best"] is None:
        print("Лучший студент: нет данных")
        print("Худший студент: нет данных")
        return

    best = stats["best"]
    worst = stats["worst"]
    print(f"Лучший студент: {best.name} ({best.average:.2f})")
    print(f"Худший студент: {worst.name} ({worst.average:.2f})")


def action_export(students: List[Student]) -> None:
    count = ask_int("Сколько студентов экспортировать (N): ", minimum=0)
    path = ask_path("Куда экспортировать", DEFAULT_TOP_CSV)
    export_top_students_csv(students, count, path)
    print(f"ТОП-{count} экспортирован в {path}")


def action_sort(students: List[Student]) -> None:
    key = input("Критерий сортировки (avg/name/id): ").strip().lower()
    print(format_students(sort_students(students, key)))


def ask_optional_float(prompt: str) -> Optional[float]:
    """Запросить число; пустой ввод означает отсутствие ограничения."""
    value = input(prompt).strip().replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValidationError("Введите число или оставьте поле пустым.") from None


def action_filter(students: List[Student]) -> None:
    name_part = input("Фрагмент ФИО (Enter — любое имя): ").strip()
    min_avg = ask_optional_float("Минимальный средний балл (Enter — без ограничения): ")
    max_avg = ask_optional_float("Максимальный средний балл (Enter — без ограничения): ")
    print(format_students(filter_students(students, name_part, min_avg, max_avg)))


ACTIONS: Dict[str, Callable[[List[Student]], None]] = {
    "1": action_load,
    "2": action_save,
    "3": action_show,
    "4": action_add,
    "5": action_remove,
    "6": action_update,
    "7": action_statistics,
    "8": action_export,
    "9": action_sort,
    "10": action_filter,
}


def run_cli() -> None:
    """Показать меню и выполнять выбранные действия до выхода."""
    students: List[Student] = []
    while True:
        print(MENU)
        try:
            choice = input("Выберите пункт: ").strip()
            if choice == "0":
                print("Работа завершена.")
                return

            action = ACTIONS.get(choice)
            if action is None:
                print("Неизвестный пункт меню. Выберите число от 0 до 10.")
                continue
            action(students)
        except StudentManagerError as exc:
            print(f"Ошибка: {exc}")
        except (EOFError, KeyboardInterrupt):
            print("\nРабота завершена.")
            return


def main() -> None:
    """Точка входа для запуска через python -m lab.main."""
    run_cli()


if __name__ == "__main__":
    main()
