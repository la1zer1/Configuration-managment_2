import json
import os
import subprocess
from datetime import datetime


def load_config(config_path):
    """Считывает конфигурационный файл."""
    with open(config_path, "r") as f:
        config = json.load(f)
    return config


def get_git_commits(repo_path, since_date):
    """
    Получает список коммитов из репозитория, начиная с указанной даты.
    Возвращает список [(commit_hash, [parent_hashes])].
    """
    os.chdir(repo_path)
    cmd = ["git", "log", "--since", since_date, "--pretty=format:%H %P"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
    commits = result.stdout.strip().split("\n")
    return [(line.split()[0], line.split()[1:]) for line in commits if line.strip()]


def build_mermaid_graph(commits):
    """
    Формирует Mermaid-граф зависимостей.
    Узлы - коммиты, рёбра - зависимости между ними.
    """
    graph_lines = ["graph TD"]
    for commit_hash, parent_hashes in commits:
        for parent in parent_hashes:
            graph_lines.append(f"    {commit_hash} --> {parent}")
    return "\n".join(graph_lines)


def save_graph_as_png(mermaid_code, output_path, mermaid_cli_path):
    """
    Сохраняет Mermaid-граф в формате PNG.
    Использует Mermaid CLI.
    """
    temp_mermaid_file = "temp_graph.mmd"
    with open(temp_mermaid_file, "w") as f:
        f.write(mermaid_code)
    
    # Генерация PNG
    cmd = [mermaid_cli_path, "-i", temp_mermaid_file, "-o", output_path]
    try:
        subprocess.run(cmd, check=True, text=True)
        print(f"Граф успешно сохранен: {output_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ошибка при выполнении Mermaid CLI: {e}")
    finally:
        os.remove(temp_mermaid_file)


def main(config_path):
    """Основная функция скрипта."""
    config = load_config(config_path)
    
    # Проверка обязательных полей в конфиге
    required_fields = ["repo_path", "mermaid_cli_path", "output_path", "since_date"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Отсутствует обязательное поле в конфиге: {field}")
    
    repo_path = config["repo_path"]
    mermaid_cli_path = config["mermaid_cli_path"]
    output_path = config["output_path"]
    since_date = config["since_date"]

    # Проверка путей
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Репозиторий не найден: {repo_path}")
    if not os.path.isfile(mermaid_cli_path):
        raise FileNotFoundError(f"Mermaid CLI не найден: {mermaid_cli_path}")
    
    # Получение списка коммитов
    print("Получение списка коммитов...")
    commits = get_git_commits(repo_path, since_date)
    if not commits:
        print("Нет коммитов для указанной даты.")
        return
    
    # Построение графа
    print("Построение графа...")
    mermaid_graph = build_mermaid_graph(commits)
    
    # Сохранение графа
    print("Сохранение графа в PNG...")
    save_graph_as_png(mermaid_graph, output_path, mermaid_cli_path)
    print("Готово.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Инструмент для визуализации графа зависимостей коммитов.")
    parser.add_argument("config", help="Путь к конфигурационному файлу JSON.")
    args = parser.parse_args()

    try:
        main(args.config)
    except Exception as e:
        print(f"Ошибка: {e}")
