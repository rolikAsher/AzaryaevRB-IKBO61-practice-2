#!/usr/bin/env python3
"""
dep_viz_cli.py — минимальный прототип CLI для визуализатора графа зависимостей (Этап 1).

Требования реализованы:
- параметры через командную строку
- параметры: имя пакета, URL/путь репозитория, режим тестового репозитория, подстрока фильтрации
- вывод всех переданных параметров в формате ключ=значение
- обработка ошибок для всех параметров
"""

import argparse
import os
import re
import sys
from urllib.parse import urlparse

VERSION = "0.1"

PACKAGE_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")  # простая проверка имени пакета

def validate_package(name: str) -> str:
    if not name:
        raise ValueError("Имя пакета не может быть пустым.")
    if not PACKAGE_RE.match(name):
        raise ValueError(
            f"Некорректное имя пакета '{name}'. Допустимые символы: буквы, цифры, '_', '-' и '.'."
        )
    return name

def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https", "git", "ssh") and bool(parsed.netloc)

def is_file_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "file" and bool(parsed.path)

def validate_repo(repo: str) -> str:
    if not repo:
        raise ValueError("Параметр репозитория не задан.")
    # локальный путь
    if os.path.exists(repo):
        # путь существует на FS
        return os.path.abspath(repo)
    # file:// URI
    if is_file_url(repo):
        path = urlparse(repo).path
        if os.path.exists(path):
            return os.path.abspath(path)
        raise ValueError(f"file:// путь указан, но файл/папка не найдены: {path}")
    # URL-проверка (http/https/git/ssh)
    if is_url(repo):
        return repo
    # не распознано
    raise ValueError(
        f"Параметр репозитория '{repo}' не распознан как существующий путь или корректный URL."
    )

def validate_test_mode(mode: str, repo_value: str) -> str:
    valid = ("none", "readonly", "simulate")
    if mode not in valid:
        raise ValueError(f"Некорректный режим тестового репозитория '{mode}'. Допустимые: {valid}")
    # если режим тестовый — требуем локальный репозиторий (не http URL)
    if mode != "none":
        # treat repo_value is local path if it's an absolute path
        parsed = urlparse(repo_value)
        if parsed.scheme in ("http", "https", "git", "ssh"):
            raise ValueError("Тестовый режим требует локального пути к тестовому репозиторию, а не URL.")
        # also if repo_value is a file://, it's ok (we converted earlier to abs path)
        if not os.path.exists(repo_value):
            raise ValueError(f"Тестовый режим включен, но локальный репозиторий не найден: {repo_value}")
    return mode

def validate_filter(substr: str) -> str:
    # фильтр может быть пустым (тогда означает "не фильтровать")
    if substr is None:
        return ""
    # optionally enforce minimal length (e.g., не пустая строка если передана)
    if substr != "" and len(substr.strip()) == 0:
        raise ValueError("Пустая строка передана как подстрока фильтра.")
    return substr

def parse_args(argv):
    p = argparse.ArgumentParser(description="Минимальный CLI визуализатора зависимостей — Этап 1")
    p.add_argument("--package", "-p", required=True, help="Имя анализируемого пакета (например my_pkg).")
    p.add_argument("--repo", "-r", required=True,
                   help="URL репозитория или путь к файлу/папке тестового репозитория.")
    p.add_argument("--test-mode", "-t", default="none",
                   choices=["none", "readonly", "simulate"],
                   help="Режим работы с тестовым репозиторием: none / readonly / simulate.")
    p.add_argument("--filter", "-f", default=None,
                   help="Подстрока для фильтрации пакетов (опционально).")
    p.add_argument("--version", action="version", version=VERSION)
    return p.parse_args(argv)

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        args = parse_args(argv)
    except SystemExit:
        # argparse уже напечатает help/ошибку; просто выйти с кодом 2
        return 2

    # Валидация параметров с обработкой ошибок
    errors = []
    validated = {}
    # package
    try:
        validated["package"] = validate_package(args.package)
    except Exception as e:
        errors.append(f"package: {e}")

    # repo
    repo_value = None
    try:
        repo_value = validate_repo(args.repo)
        validated["repo"] = repo_value
    except Exception as e:
        errors.append(f"repo: {e}")

    # test-mode
    try:
        # для проверки может понадобиться repo_value; если repo_value невалиден — всё равно сообщим об ошибке repo
        rm = args.test_mode
        # если repo_value is None (еще не валидирован) — передаём оригинал args.repo
        repo_for_mode = repo_value if repo_value is not None else args.repo
        validated["test_mode"] = validate_test_mode(rm, repo_for_mode)
    except Exception as e:
        errors.append(f"test_mode: {e}")

    # filter
    try:
        validated["filter"] = validate_filter(args.filter)
    except Exception as e:
        errors.append(f"filter: {e}")

    # Если есть ошибки — вывести и завершить с кодом 1
    if errors:
        print("Обнаружены ошибки при обработке параметров:", file=sys.stderr)
        for err in errors:
            print("  -", err, file=sys.stderr)
        return 1

    # Вывести все параметры в формате ключ=значение (требование)
    print("Запущено приложение с параметрами:")
    for k in ("package", "repo", "test_mode", "filter"):
        v = validated.get(k, "")
        print(f"{k}={v}")

    # Здесь на следующих этапах будет основной алгоритм анализа зависимостей и визуализации.
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

"""
python dep_viz_cli.py -p mypkg -r .\test_repo -t readonly -f util
python dep_viz_cli.py -p "bad name!" -r .\test_repo
python dep_viz_cli.py -p mypkg -r https://git.example.com/repo.git -t readonly
python dep_viz_cli.py --help

"""