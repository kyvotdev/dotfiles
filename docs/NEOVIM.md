# Neovim / Pixel Development

Конфигурация для Neovim 0.11+ (проверена на установленном 0.12.6). Код — `config/nvim/`, подключён ссылкой в `~/.config/nvim`. Настройки рассчитаны на разработку в разных проектах без автоматического запуска проектных скриптов.

## Быстрый старт

```bash
sudo pacman -S --needed neovim git ripgrep fd
nvim
```

В Neovim:

```vim
:PixelTools
:PixelInstall
```

`PixelTools` показывает, какие серверы и форматтеры установлены. `PixelInstall` скачивает **один** пакет [mini.nvim](https://github.com/nvim-mini/mini.nvim), ветка stable: поиск файлов / текста, файловый менеджер, иконки, Git, statusline, пары, surround, comment и подсказки клавиш. После установки перезапусти редактор; обновление — `:PixelUpdate`. Плагин хранится в `~/.local/share/nvim/site/pack/pixel/start/mini.nvim`, не в dotfiles. Загрузка при первом старте не запускается автоматически.

База работает без плагинов: LSP, автодополнение, диагностика, форматирование, терминал, задачи, поиск через rg, netrw и палитра от обоев. В среде редактора DNS недоступен, поэтому mini.nvim отсюда скачать не удалось. Команда PixelInstall выполнит загрузку из твоей сессии.

## Языки и инструменты

Используется современный встроенный API `vim.lsp.config` / `vim.lsp.enable`, без старого `require('lspconfig').setup`. Отсутствующие серверы не запускаются и не скачиваются молча. Установи нужные пакеты и выполни `:PixelLspReload` или перезапусти Neovim.

Основной набор из официальных репозиториев Arch (можно выбрать только нужное):

```bash
sudo pacman -S --needed lua-language-server pyright typescript-language-server \
  rust-analyzer gopls clang bash-language-server yaml-language-server \
  vscode-json-languageserver vscode-html-languageserver vscode-css-languageserver \
  marksman taplo-cli ruff stylua prettier shfmt
```

| Язык | LSP | Форматирование |
| --- | --- | --- |
| Lua / Neovim Lua | lua-language-server | stylua |
| Python | pyright + ruff | ruff format |
| JavaScript, TypeScript, JSX, TSX | typescript-language-server | prettier |
| Rust | rust-analyzer | LSP/rustfmt |
| Go | gopls | gofmt |
| C/C++, Objective-C, CUDA | clangd | clang-format |
| Bash/sh | bash-language-server | shfmt |
| JSON/JSONC | vscode-json-languageserver | prettier |
| YAML | yaml-language-server | prettier |
| HTML | vscode-html-languageserver | prettier |
| CSS/SCSS/Less | vscode-css-languageserver | prettier |
| TOML | taplo | LSP |
| Markdown/MDX | marksman | prettier |

Дополнительно подготовлены команды для PHP (`intelephense --stdio`), Ruby (`ruby-lsp`), C# (`csharp-ls`), Java (`jdtls`), Dockerfile (`docker-langserver --stdio`) и SQL (`sqls`). Они включаются только при наличии соответствующего executable в PATH. Для Ruby и Docker есть пакеты `ruby-lsp` и `dockerfile-language-server`; остальные установи способом своего стека. Для Java создаётся отдельный cache workspace по корню проекта. Для C# корень ищется по Directory.Build.props, global.json или .git.

Нужны сами компиляторы/runtime: например Node.js/TypeScript для web, Go для gopls, Rust toolchain/rustfmt/clippy для Rust, Python/venv для Python и JDK для Java. LSP не заменяет SDK. Для clangd экспортируй compile_commands.json (например CMake с `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`), Python-проекту настрой .venv/pyrightconfig, TypeScript — tsconfig. Для нестандартных монорепозиториев поправь root_markers в `lua/pixel/lsp.lua`.

Автодополнение использует встроенный LSP: срабатывает на trigger characters сервера, Ctrl+Space вызывает его вручную. LSP snippets поддержаны встроенным vim.snippet. Tab/Shift+Tab выбирают кандидатов либо поля snippet.

## Клавиши

Leader = **Space**. Эти сочетания работают внутри Neovim; Win-комбинации остаются у niri.

| Клавиши | Действие |
| --- | --- |
| Space+w / Space+q | Сохранить / закрыть с проверкой несохранённого |
| Space+e | Файловый менеджер |
| Space+ff / Space+fg | Найти файл / искать текст в проекте |
| Space+fb / Space+fh | Буферы / справка |
| Shift+H / Shift+L | Предыдущий / следующий буфер |
| Space+bd | Закрыть буфер с проверкой несохранённого |
| Ctrl+H/J/K/L | Перейти между split-окнами |
| Space+sv / Space+sh | Вертикальный / горизонтальный split |
| Space+t | Терминал в корне проекта |
| Esc Esc в терминале | Выйти из режима терминального ввода |
| Space+rr | Запустить сохранённый Python/Lua/JS/Bash-файл |
| Space+rt | Выбрать задачу Cargo/Go/npm/Python-проекта |
| gd / gD / gr / gi | Определение / объявление / ссылки / реализации |
| K / Ctrl+K в insert | Документация / сигнатура |
| Space+cr / Space+ca | Переименовать символ / code actions |
| Space+cs / Space+ct | Символы документа / определение типа |
| Space+cf | Форматировать текущий буфер |
| Space+uf | Включить / выключить форматирование при сохранении для буфера |
| Space+ud / Space+cd | Переключить диагностику / показать детали строки |
| [d / ]d | Предыдущая / следующая диагностика |
| [q / ]q | Предыдущий / следующий результат поиска |
| Space+cl | Статус серверов и форматтеров |
| Space+ut | Перечитать палитру обоев |
| Ctrl+Space / Enter | Вызвать / принять автодополнение |
| Tab / Shift+Tab | Кандидаты автодополнения или поля snippet |
| Esc в normal | Убрать подсветку поиска |

Если mini.nvim установлен: обычные `gcc`/`gc` для комментариев, `sa`/`sd`/`sr` для surround; файловый менеджер применяет изменения файлов после подтверждения. Подробности встроены в `:help MiniFiles`, `:help MiniSurround`, `:help MiniPick`.

## Поведение и проверки

- Форматирование при сохранении **выключено по умолчанию**. Space+uf включает его для текущего буфера.
- Внешний форматтер работает асинхронно при ручном вызове и не перезаписывает более свежие правки. При сохранении и fallback на LSP используется короткий синхронный вызов.
- npm/Cargo/Go/Python-задачи запускаются только после явного выбора. Никакой автозапуск `.nvim.lua` или проектных shell-команд при открытии.
- Git-проекты определяются автоматически. Для одиночного файла используется текущий каталог.
- Палитра читается из общего palette.json и обновляется при возврате фокуса и по таймеру; фон редактора сохраняет прозрачность терминала.
- Treesitter включается только при уже доступном parser; без него остаётся штатная подсветка. Parser-пакеты не скачиваются автоматически.
- Undo/shada/plugin data находятся в стандартных state/data-каталогах Neovim, не в Git.

Проверка базовой конфигурации:

```bash
nvim --headless '+luafile ~/dotfiles/tests/nvim_smoke.lua' +qa
```

Проверены запуск, команды и бинды, конфигурации языков, применение асинхронного форматирования и защита от перезаписи новой правки. Сервера, SDK и optional mini.nvim требуют установки и проверки на реальном проекте. `:checkhealth vim.lsp`, `:PixelTools` и `:messages` помогают диагностировать состояние.
