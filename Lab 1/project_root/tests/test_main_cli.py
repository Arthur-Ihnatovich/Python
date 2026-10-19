"""Тесты консольного меню: «вводим» текст через monkeypatch, читаем вывод через capsys."""

import builtins

from lab import main as cli


def run_with_inputs(monkeypatch, inputs):
    """Запустить меню, подменив input() заранее заготовленными ответами."""
    answers = iter(inputs)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    cli.run_cli()


def test_exit(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["0"])
    assert "Работа завершена" in capsys.readouterr().out


def test_unknown_menu_item_does_not_crash(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["99", "abc", "0"])
    assert capsys.readouterr().out.count("Неизвестный пункт меню") == 2


def test_load_and_show(monkeypatch, capsys, csv_file):
    # 1 — загрузить (путь), 3 — показать, 0 — выход
    run_with_inputs(monkeypatch, ["1", str(csv_file), "3", "0"])
    out = capsys.readouterr().out
    assert "Загружено студентов: 3" in out
    assert "Иванов Иван" in out


def test_add_student_and_show(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["4", "7", "Сидоров Сидор", "80, 100", "3", "0"])
    out = capsys.readouterr().out
    assert "Студент добавлен" in out
    assert "Сидоров Сидор" in out
    assert "90.00" in out


def test_add_duplicate_shows_error(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["4", "1", "А", "", "4", "1", "Б", "", "0"])
    assert "уже существует" in capsys.readouterr().out


def test_remove_missing_student_shows_error(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["5", "42", "0"])
    out = capsys.readouterr().out
    assert "Ошибка" in out and "не найден" in out


def test_invalid_number_shows_error(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["5", "не число", "0"])
    assert "Введите целое число" in capsys.readouterr().out


def test_invalid_grade_shows_error(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["4", "1", "Иванов", "80, abc", "0"])
    assert "не является целой оценкой" in capsys.readouterr().out


def test_load_missing_file_shows_error(monkeypatch, capsys, tmp_path):
    run_with_inputs(monkeypatch, ["1", str(tmp_path / "net.csv"), "0"])
    assert "Файл не найден" in capsys.readouterr().out


def test_statistics_on_empty_list(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["7", "0"])
    out = capsys.readouterr().out
    assert "Количество студентов: 0" in out
    assert "нет данных" in out


def test_save_and_export(monkeypatch, capsys, csv_file, tmp_path):
    saved = tmp_path / "saved.csv"
    top = tmp_path / "top.csv"
    run_with_inputs(
        monkeypatch,
        ["1", str(csv_file), "2", str(saved), "8", "2", str(top), "0"],
    )
    assert saved.exists() and top.exists()
    assert "ТОП-2 экспортирован" in capsys.readouterr().out


def test_sort_with_wrong_key_shows_error(monkeypatch, capsys):
    run_with_inputs(monkeypatch, ["9", "weight", "0"])
    assert "avg, name или id" in capsys.readouterr().out


def test_filter_menu(monkeypatch, capsys, csv_file):
    # Фильтр по фрагменту «олег»; границы среднего пропускаем (Enter)
    run_with_inputs(monkeypatch, ["1", str(csv_file), "10", "олег", "", "", "0"])
    out = capsys.readouterr().out
    assert "Иванов Олег" in out


def test_ctrl_d_ends_program_without_crash(monkeypatch, capsys):
    # Если ввод закончился (EOF), программа не падает, а завершается
    def raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr(builtins, "input", raise_eof)
    cli.run_cli()
    assert "Работа завершена" in capsys.readouterr().out
