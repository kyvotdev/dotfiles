# Neovim / Pixel IDE

Конфигурация для Neovim 0.12+; проверена на 0.12.6 и установленном mini.nvim 0.18. Код находится в `config/nvim`, данные плагинов и сессий — в стандартных data/state-каталогах Neovim. Цвета автоматически следуют за обоями.

## Что исправлено

- mini.files заменён на nvim-tree: служебные URI стартового экрана не передаются в файловый менеджер; конфликт автокоманд netrw исключён.
- Автодополнение теперь работает через mini.completion: LSP, snippets и запасное дополнение словами буфера. Два разных движка одновременно не запускаются.
- Серверы и форматтеры обнаруживаются не только в PATH, но и в `.venv/bin`, `venv/bin`, `node_modules/.bin` проекта, `~/.local/bin`, `~/.cargo/bin`, `~/go/bin`.
- При отсутствии форматтера выводится конкретная подсказка, а не ошибка о несуществующем LSP-клиенте.
- Установщик плагинов работает в фоне, не скачивает заново уже установленный mini.nvim, блокирует параллельные установки и сохраняет revisions.
- Обязательное отсутствие языковых серверов видно в `:PixelTools`. Необязательные Python/Node/Ruby/Perl remote providers отключены: Lua-плагины, LSP и debugpy не требуют pynvim или node provider.

## Установка компонентов

В редакторе уже есть интерфейс mini.nvim, но **LSP-серверы и SDK устанавливаются отдельно**. Подготовлен один установщик Arch:

```bash
bash ~/dotfiles/tools/install-dev-tools.sh all
```

Он выполняет `pacman -Syu --needed`, затем устанавливает недостающие плагины. Установка требует sudo в обычном терминале; из sandbox редактора она не выполнялась. Можно выбрать меньший профиль:

```bash
bash ~/dotfiles/tools/install-dev-tools.sh core
bash ~/dotfiles/tools/install-dev-tools.sh python
bash ~/dotfiles/tools/install-dev-tools.sh web
bash ~/dotfiles/tools/install-dev-tools.sh systems
bash ~/dotfiles/tools/install-dev-tools.sh all --print
```

После установки перезапусти Neovim и выполни `:PixelParsers`. Затем открой проект через `nvim /path/to/project` или Space+fp. `:PixelTools` показывает готовность компонентов, активные LSP и путь к журналу.

Плагины из [plugins.json](../config/nvim/plugins.json):

- [mini.nvim](https://github.com/nvim-mini/mini.nvim), stable: стартовый экран, fuzzy pickers, автодополнение, Git, сессии, notifications, statusline, surround и подсказки клавиш.
- [nvim-dap](https://github.com/mfussenegger/nvim-dap): интерфейс отладки, breakpoints, шаги, stack, scopes и REPL.
- [nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter), main: установка синтаксических parsers для Neovim 0.12.

[nvim-tree](https://github.com/nvim-tree/nvim-tree.lua) заменяет mini.files: слева дерево шириной 34 колонки с Git, диагностикой и подсветкой открытого файла. [nvim-web-devicons](https://github.com/nvim-tree/nvim-web-devicons) — настоящий поставщик filetype-иконок; подмена его API через MiniIcons отключена. Значки папок заданы стабильными Nerd Font glyphs, цвета соответствуют общей палитре.

Установить только новый explorer и значки:

```bash
python3 ~/.config/nvim/scripts/install-plugins.py --only nvim-web-devicons nvim-tree.lua
```

Либо после перечитывания конфигурации выполнить `:PixelExplorerInstall`. Затем перезапустить Neovim. Пока плагины не скачаны, Space+e открывает временный файловый picker, без возврата к mini.files. Из sandbox скачать плагины не удалось из-за DNS; конфигурация сама по себе не означает, что файлы плагина уже установлены.

`:PixelInstall` ставит недостающие плагины; `:PixelUpdate` явно обновляет установленные. Редактор при каждом запуске ничего не скачивает. `:PixelParsers python rust` устанавливает только выбранные parsers; без аргументов — основной набор. Нужны tree-sitter-cli, curl, tar и компилятор C. Ошибка загрузки не удаляет рабочие плагины. В sandbox DNS недоступен, поэтому новые DAP/Treesitter-плагины здесь не удалось скачать; mini.nvim уже установлен пользователем и проверен.

## Языки

| Стек | Серверы / SDK в профиле | Форматтер |
| --- | --- | --- |
| Python | Python, Pyright, Ruff, pytest, debugpy | Ruff |
| JS/TS, JSX/TSX | Node, npm, TypeScript, typescript-language-server | Prettier |
| C/C++/Objective-C/CUDA | clangd / Clang, GDB | clang-format |
| Rust | Rust toolchain, rust-analyzer | rustfmt через LSP |
| Go | Go, gopls, Delve | gofmt |
| Lua / Neovim | lua-language-server | StyLua |
| HTML / CSS / SCSS / Less | VSCode language servers | Prettier |
| JSON/JSONC / YAML | VSCode JSON / yaml-language-server | Prettier |
| Markdown/MDX | Marksman | Prettier |
| TOML | Taplo | LSP |
| Bash/sh | bash-language-server | shfmt |
| Dockerfile / Ruby | docker-langserver / ruby-lsp | LSP, если доступен |

Также есть конфигурации PHP/Intelephense, Java/jdtls, C#/csharp-ls, SQL/sqls. Они включаются при наличии executables; эти серверы и их SDK не включены в основной профиль. Java получает отдельный cache workspace для каждого проекта.

Для C/C++ экспортируй compile_commands.json, например `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`. Python-проекту настрой `.venv` / pyrightconfig.json; TypeScript — tsconfig.json. Для нестандартного монорепозитория можно уточнить root_markers в `lua/pixel/lsp.lua`. После установки сервера в уже открытом редакторе: `:PixelLspReload`.

## Интерфейс и рабочий процесс

Стартовый экран позволяет открыть проект, найти файл, перейти к недавним файлам и проверить инструменты. Fuzzy pickers показывают preview. Дерево nvim-tree создаёт, переименовывает и перемещает файлы; удаление требует подтверждения. Git показывает изменения, ветки, историю и hunks. Сессии сохраняются только по явной команде и не исполняются автоматически при входе в произвольный репозиторий.

Leader = **Space**. Win-комбинации остаются у niri.

| Клавиши | Действие |
| --- | --- |
| Space+w / Space+q | Сохранить / закрыть с проверкой несохранённого |
| Space+e / Space+E / Space+fp | Переключить дерево / показать текущий файл / открыть проект |
| Space+ff / Space+fg | Найти файл / искать текст проекта |
| Space+fr / Space+fb / Space+fh | Недавние файлы / буферы / справка |
| Space+/ | Поиск строк текущего буфера |
| Shift+H / Shift+L | Предыдущий / следующий буфер |
| Space+bd | Закрыть буфер |
| Ctrl+H/J/K/L | Перейти между split-окнами |
| Space+sv / Space+sh | Вертикальный / горизонтальный split |
| Space+t | Терминал проекта; Esc Esc — выйти из режима ввода |
| Space+rr / Space+rt | Запустить файл / выбрать задачу проекта |
| gd / gD / gr / gi | Определение / объявление / ссылки / реализации |
| K / Ctrl+K в insert | Документация / сигнатура |
| Space+cr / Space+ca | Переименование символа / code actions |
| Space+cs / Space+ct / Space+co | Символы / определение типа / fuzzy outline |
| Space+cf | Форматировать буфер |
| Space+uf | Включить форматирование при сохранении для буфера |
| Space+xx / Space+cd | Диагностика проекта / детали строки |
| Space+ud | Включить / выключить диагностику |
| [d / ]d, [q / ]q | Диагностики / quickfix-результаты |
| Space+gb / Space+gc / Space+gh | Git branches / commits / hunks |
| Space+go | Включить overlay изменений |
| Space+ss / Space+sl | Сохранить / загрузить сессию проекта |
| Space+un / Space+cl | История уведомлений / статус инструментов |
| Space+ut | Перечитать палитру |
| Ctrl+Space / Enter | Вызвать / принять автодополнение |
| Tab / Shift+Tab | Выбрать кандидата или поле snippet |
| gcc / gc, sa/sd/sr | Комментарий / surround |

Автодополнение появляется при вводе, без LSP дополняет словами из буфера. Snippets поддерживаются через vim.snippet. Форматирование при сохранении по умолчанию выключено. Ручной внешний форматтер работает асинхронно и не затирает правки, сделанные после его запуска. При сохранении / fallback на LSP используется ограниченный синхронный вызов.

## Отладчик

После `:PixelInstall` доступны DAP-профили Python, C/C++/Rust и Go. Python использует debugpy; код запускается в `.venv/bin/python`, если такая среда есть. C/C++/Rust — GDB с DAP (современная версия GDB с Python; профили собирай с debug symbols). Go — Delve.

| Клавиши | Действие |
| --- | --- |
| F5 | Запуск / продолжение |
| F10 / F11 / Shift+F11 | Шаг поверх / внутрь / наружу |
| Space+db / Space+dB | Обычная / условная точка останова |
| Space+dq / Space+dr | Остановить / REPL |
| Space+de / Space+ds / Space+df | Значение под курсором / scopes / stack |
| Space+dd | Встроенный GDB termdebug — работает без скачивания DAP-плагина |

Для DAP нужны отдельные адаптеры: python-debugpy, gdb, delve входят в профиль all. Конфигурации VSCode launch.json могут содержать произвольные команды, поэтому не импортируются автоматически.

## Проверка и границы

```bash
python3 ~/dotfiles/tests/run_nvim.py
```

Проверки запускаются после VimEnter и возвращают ненулевой код при ошибке. Проверены: отсутствие startup errors, реальный поиск mini.pick, безопасный адаптер nvim-tree, бинды/форматирование с защитой от гонки и LSP-сеанс с локальным тестовым сервером (project-local discovery, initialize, diagnostics, completion, keymaps). Тестовый сервер не используется редактором для реальных проектов.

Реальные серверы, SDK, parsers и DAP-адаптеры всё равно нужно установить; их готовность показывает `:PixelTools`. Новый конфиг не выдаёт отсутствующие зависимости за рабочие. Внешние процессы и GUI отладки требуют проверки в пользовательской сессии. Журналы: `:messages`, Space+un, `:checkhealth vim.lsp` и путь LSP log из PixelTools.

## Стартовый экран и значки

Исправлен E5108 при открытии файлового менеджера со стартового экрана: URI `ministarter:/...`, terminal/help/quickfix и другие служебные буферы не передаются в mini.files как файловые пути. Для нового несохранённого файла открывается существующий родительский каталог, для стартового экрана — текущий проект. Регрессия проверена на `ministarter:/1/welcome`.

В mini.pick явно включён show_icons. В nvim-tree включены file/folder/git/diagnostic icons и реальный nvim-web-devicons, MiniIcons остаётся для pickers и statusline. `:PixelIcons` показывает проверочную таблицу. Kitty сопоставляет Symbols Nerd Font Mono всем private-use диапазонам Nerd Fonts, включая старые и новые значки. После изменения font mapping перезапусти терминал (или перечитай конфиг Kitty через Ctrl+Shift+F5) и Neovim. MiniIcons работают со style=glyph, односимвольной шириной; квадраты в PixelIcons указывают на проблему шрифта терминала, а не отсутствие пакета mini.nvim.

### Клавиши в дереве nvim-tree

| Клавиша | Действие |
| --- | --- |
| Enter / l | Открыть файл или папку |
| h | Закрыть папку / к родителю |
| v / s | Открыть файл в вертикальном / горизонтальном split |
| a / r / d | Создать / переименовать / удалить |
| c / x / p | Копировать / вырезать / вставить |
| H / R | Скрытые файлы / обновить дерево |
| q / ? | Закрыть дерево / подсказка клавиш |

`Space+e` работает и со стартового экрана, `Space+E` показывает текущий файл. Font mapping терминала остаётся Symbols Nerd Font Mono для всех Nerd Font диапазонов. Проверка символов — `:PixelIcons`. Само окно nvim-tree требует проверки после фактического скачивания плагина; локальные тесты проверяют его адаптер и настройки значков, не подменяя этим проверку upstream UI.
