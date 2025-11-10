#!/usr/bin/env python3
"""
Этап 2. Сбор данных о зависимостях пакетов Alpine Linux
"""
import argparse
import tarfile
import urllib.request
import tempfile
import os
import sys

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Stage 2: get Alpine package dependencies")
    parser.add_argument("--package", "-p", required=True, help="Имя пакета для анализа")
    parser.add_argument("--repo-url", "-r", required=True, help="URL репозитория Alpine (например, http://dl-cdn.alpinelinux.org/alpine/v3.18/main/x86_64/)")
    return parser.parse_args(argv)

def download_apkindex(repo_url: str) -> str:
    """
    Скачивает APKINDEX.tar.gz с репозитория в временный файл
    """
    index_url = repo_url.rstrip("/") + "/APKINDEX.tar.gz"
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".tar.gz")
    os.close(tmp_fd)
    print(f"Скачивание {index_url} ...")
    try:
        urllib.request.urlretrieve(index_url, tmp_path)
    except Exception as e:
        os.remove(tmp_path)
        raise RuntimeError(f"Ошибка скачивания APKINDEX: {e}")
    return tmp_path

def extract_dependencies(apkindex_path: str, package_name: str):
    """
    Извлекает прямые зависимости заданного пакета из APKINDEX.tar.gz
    """
    dependencies = []
    with tarfile.open(apkindex_path, "r:gz") as tar:
        # Внутри tar могут быть несколько файлов (обычно APKINDEX)
        for member in tar.getmembers():
            f = tar.extractfile(member)
            if not f:
                continue
            content = f.read().decode("utf-8", errors="ignore")
            # Пакет разделяется блоками, каждый блок начинается с P: (package name)
            blocks = content.split("\n\n")
            for block in blocks:
                lines = block.strip().split("\n")
                pkg_name = None
                depends = []
                for line in lines:
                    if line.startswith("P:"):
                        pkg_name = line[2:].strip()
                    elif line.startswith("D:"):
                        depends = line[2:].strip().split()
                if pkg_name == package_name:
                    dependencies = depends
                    return dependencies
    return dependencies

def main(argv=None):
    args = parse_args(argv)
    try:
        apkindex_file = download_apkindex(args.repo_url)
        deps = extract_dependencies(apkindex_file, args.package)
        os.remove(apkindex_file)
        if deps:
            print(f"Прямые зависимости пакета '{args.package}':")
            for dep in deps:
                print(" -", dep)
        else:
            print(f"Пакет '{args.package}' не найден или зависимостей нет.")
    except Exception as e:
        print("Ошибка:", e, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
"""
python dep_viz_stage2.py -p bash -r http://dl-cdn.alpinelinux.org/alpine/v3.18/main/x86_64/

"""
