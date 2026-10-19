"""Тесты чтения/записи CSV и экспорта ТОП-N."""

import csv

import pytest

from lab import io_utils
from lab.errors import CSVFormatError, StudentManagerError, ValidationError
from lab.io_utils import (
    export_top_students_csv,
    load_students_csv,
    parse_rows,
    save_students_csv,
)
from lab.models import Student


# ---------- разбор строк (parse_rows) ----------

def test_parse_rows_with_header():
    rows = [["id", "name", "grade1"], ["1", "Иванов", "80"]]
    result = parse_rows(rows)
    assert len(result) == 1
    assert result[0].grades == [80]


def test_parse_rows_without_header():
    result = parse_rows([["1", "Иванов", "80", "90"]])
    assert result[0].id == 1
    assert result[0].grades == [80, 90]


def test_parse_rows_empty_cells_become_none():
    result = parse_rows([["1", "Иванов", "80", "", "90"]])
    assert result[0].grades == [80, None, 90]


def test_parse_rows_only_id_and_name():
    assert parse_rows([["1", "Иванов"]])[0].grades == []


def test_parse_rows_skips_blank_lines():
    assert len(parse_rows([[], ["", " "], ["1", "Иванов"]])) == 1


@pytest.mark.parametrize(
    "bad_row",
    [
        ["abc", "Иванов", "80"],     # ID не число
        ["1"],                        # нет имени
        ["1", "Иванов", "abc"],       # оценка не число
        ["1", "Иванов", "8.5"],       # оценка не целая
        ["1", "Иванов", "101"],       # оценка больше 100
        ["1", "Иванов", "-1"],        # оценка меньше 0
        ["1", "   ", "80"],           # пустое имя
        ["0", "Иванов", "80"],        # ID должен быть > 0
    ],
)
def test_parse_rows_invalid_data_raises(bad_row):
    with pytest.raises(CSVFormatError):
        parse_rows([bad_row])


def test_parse_rows_duplicate_id_raises():
    with pytest.raises(CSVFormatError):
        parse_rows([["1", "Иванов"], ["1", "Петров"]])


def test_error_message_contains_line_number():
    with pytest.raises(CSVFormatError, match="Строка 2"):
        parse_rows([["1", "Иванов"], ["x", "Петров"]])


# ---------- чтение файла ----------

def test_load_csv_with_header(csv_file):
    result = load_students_csv(csv_file)
    assert [s.id for s in result] == [1, 2, 4]
    assert result[2].grades == [100, 90, None]


def test_load_csv_without_header(tmp_path):
    path = tmp_path / "no_header.csv"
    path.write_text("1,Иванов Иван,80,90\n", encoding="utf-8")
    assert load_students_csv(path)[0].name == "Иванов Иван"


def test_load_csv_with_bom(tmp_path):
    # Excel часто добавляет в начало файла невидимый маркер BOM
    path = tmp_path / "bom.csv"
    path.write_text("id,name,grade1\n1,Иванов,80\n", encoding="utf-8-sig")
    assert len(load_students_csv(path)) == 1


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(StudentManagerError, match="не найден"):
        load_students_csv(tmp_path / "net_takogo.csv")


def test_load_invalid_csv_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("id,name,grade1\n1,Иванов,abc\n", encoding="utf-8")
    with pytest.raises(CSVFormatError):
        load_students_csv(path)


def test_load_wrong_encoding_raises(tmp_path):
    path = tmp_path / "cp1251.csv"
    path.write_bytes("1,Иванов\n".encode("cp1251"))
    with pytest.raises(CSVFormatError):
        load_students_csv(path)


def test_load_permission_error(monkeypatch, csv_file):
    # Подменяем open внутри модуля так, чтобы он «не пускал» к файлу
    def fake_open(*args, **kwargs):
        raise PermissionError("нет доступа")

    monkeypatch.setattr(io_utils, "open", fake_open, raising=False)
    with pytest.raises(StudentManagerError, match="Нет прав"):
        load_students_csv(csv_file)


# ---------- запись файла ----------

def test_save_writes_header_and_aligns_columns(tmp_path):
    group = [Student(1, "А", [80, 90, 70]), Student(2, "Б", [50])]
    path = tmp_path / "out.csv"
    save_students_csv(group, path)

    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows[0] == ["id", "name", "grade1", "grade2", "grade3"]
    assert rows[1] == ["1", "А", "80", "90", "70"]
    assert rows[2] == ["2", "Б", "50", "", ""]  # короткая строка дополнена пустыми


def test_save_empty_list_writes_only_header(tmp_path):
    path = tmp_path / "empty.csv"
    save_students_csv([], path)
    assert path.read_text(encoding="utf-8").strip() == "id,name"


def test_roundtrip_save_then_load(tmp_path, csv_file):
    original = load_students_csv(csv_file)
    path = tmp_path / "copy.csv"
    save_students_csv(original, path)
    assert load_students_csv(path) == original


def test_roundtrip_keeps_cyrillic(tmp_path):
    path = tmp_path / "cyr.csv"
    save_students_csv([Student(1, "Ёлкина Юлия Щукина", [100])], path)
    assert load_students_csv(path)[0].name == "Ёлкина Юлия Щукина"


def test_save_to_missing_folder_raises(tmp_path):
    with pytest.raises(StudentManagerError):
        save_students_csv([], tmp_path / "нет_папки" / "out.csv")


# ---------- экспорт ТОП-N ----------

def test_export_top_students(tmp_path, students):
    path = tmp_path / "top.csv"
    export_top_students_csv(students, 2, path)

    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows[0] == ["id", "name", "average", "grades"]
    assert len(rows) == 3  # заголовок + 2 студента
    assert rows[1] == ["1", "Петров Пётр", "90.00", "90 90"]  # оценки через пробел


def test_export_count_larger_than_group(tmp_path, students):
    path = tmp_path / "top.csv"
    export_top_students_csv(students, 100, path)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 4


def test_export_zero_students(tmp_path, students):
    path = tmp_path / "top.csv"
    export_top_students_csv(students, 0, path)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.parametrize("bad_count", [-1, "3", 2.5, True])
def test_export_invalid_count_raises(tmp_path, students, bad_count):
    with pytest.raises(ValidationError):
        export_top_students_csv(students, bad_count, tmp_path / "top.csv")
