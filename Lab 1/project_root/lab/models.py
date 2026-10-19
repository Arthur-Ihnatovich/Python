"""Модели данных приложения."""

from dataclasses import dataclass, field
from typing import List, Optional

from lab.errors import ValidationError


@dataclass
class Student:
    """
    Студент, его идентификатор, имя и оценки.

    Пустая оценка представляется значением None и не учитывается при расчёте
    среднего балла.
    """

    id: int
    name: str
    # default_factory нужен, чтобы каждый объект получал свой собственный пустой список.
    grades: List[Optional[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Проверить корректность полей после создания объекта."""
        self.id = self.validate_id(self.id)
        self.name = self.validate_name(self.name)
        self.set_grades(self.grades)

    @staticmethod
    def validate_id(value: int) -> int:
        """Проверяет id и возвращает его."""
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValidationError(f"id должен быть целым числом больше 0, получено {value!r}")
        return value

    @staticmethod
    def validate_name(value: str) -> str:
        """Проверяет ФИО (непустая строка), убирает лишние пробелы по краям."""
        if not isinstance(value, str) or not value.strip():  # "" пустая строка это False
            raise ValidationError("ФИО не может быть пустым")
        return value.strip()

    @staticmethod
    def validate_grades(grades: List[Optional[int]]) -> List[Optional[int]]:
        """Проверить, что каждая оценка — целое число от 0 до 100 или None."""
        if not isinstance(grades, list):
            raise ValidationError("Оценки должны быть списком.")

        for grade in grades:
            if grade is None:
                continue
            if isinstance(grade, bool) or not isinstance(grade, int):
                raise ValidationError("Оценки должны быть целыми числами от 0 до 100.")
            if not 0 <= grade <= 100:
                raise ValidationError("Оценка должна находиться в диапазоне от 0 до 100.")
        return grades

    def set_grades(self, grades: List[Optional[int]]) -> None:
        """Проверить и установить оценки студента."""
        # Делегируем проверку статическому методу внутри класса
        self.grades = self.validate_grades(grades)

    @property
    def average(self) -> float:
        """Вернуть среднее по имеющимся оценкам; при их отсутствии вернуть 0.0."""
        present_grades = [grade for grade in self.grades if grade is not None]
        if not present_grades:
            return 0.0
        return sum(present_grades) / len(present_grades)
