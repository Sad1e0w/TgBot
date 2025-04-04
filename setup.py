from cx_Freeze import setup, Executable
# Настройки сборки
build_options = {
    "packages": ["telebot", "sqlite3", "logging", "datetime", "random"],
    "excludes": [],
    "include_files": ["dbODIN.db"]  # Добавьте другие файлы, если нужны
}

# Конфигурация исполняемого файла
executables = [
    Executable(
        "0.4.8 PB.py",
        base="Win32GUI",  # Скрывает консоль
        target_name="BotApp.exe"
    )
]

setup(
    name="BotApp",
    version="0.4.8",
    description="Telegram Bot",
    options={"build_exe": build_options},
    executables=executables
)