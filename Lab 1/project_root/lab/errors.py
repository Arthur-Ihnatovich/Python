"""Собственные исключения приложения."""


class StudentManagerError(Exception):
    """Базовое исключение приложения."""


class ValidationError(StudentManagerError):
    """Ошибка проверки введённых или загруженных данных."""


class DuplicateStudentError(StudentManagerError):
    """Попытка добавить студента с уже существующим ID."""


class StudentNotFoundError(StudentManagerError):
    """Студент с указанным ID не найден."""


class CSVFormatError(StudentManagerError):
    """CSV-файл имеет неверный формат или содержит некорректные данные."""
