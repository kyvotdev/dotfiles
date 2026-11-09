local M = {}
function M.root()
  local name = vim.api.nvim_buf_get_name(0)
  if vim.bo.buftype ~= '' or name:match('^%a[%w+.-]*:') then return vim.uv.cwd() end
  return vim.fs.root(0, { '.git', 'Cargo.toml', 'go.mod', 'pyproject.toml', 'package.json', 'Makefile' }) or vim.uv.cwd()
end
function M.open_terminal(argv, cwd)
  vim.cmd('botright 14new')
  vim.fn.jobstart(argv or { vim.o.shell }, { term = true, cwd = cwd or M.root() })
  vim.cmd.startinsert()
end
function M.format_command(ft, file)
  local map = {
    lua = { 'stylua', '--stdin-filepath', file, '-' },
    python = { 'ruff', 'format', '--stdin-filename', file, '-' },
    go = { 'gofmt' },
    c = { 'clang-format', '--assume-filename=' .. file },
    cpp = { 'clang-format', '--assume-filename=' .. file },
    sh = { 'shfmt', '-i', '2' },
    bash = { 'shfmt', '-i', '2' },
  }
  for _, language in ipairs({ 'javascript', 'javascriptreact', 'typescript', 'typescriptreact', 'json', 'jsonc', 'yaml', 'html', 'css', 'scss', 'less', 'markdown', 'markdown.mdx' }) do map[language] = { 'prettier', '--stdin-filepath', file } end
  local command = map[ft]
  if command then
    local path = require('pixel.executables').resolve(command[1], M.root())
    if path then command[1] = path; return command end
  end
end
function M.format(sync)
  local buf = vim.api.nvim_get_current_buf()
  if not vim.bo[buf].modifiable or vim.bo[buf].buftype ~= '' then return end
  local file = vim.api.nvim_buf_get_name(buf)
  local argv = M.format_command(vim.bo[buf].filetype, file)
  if not argv then
    local clients = vim.lsp.get_clients({ bufnr = buf, method = 'textDocument/formatting' })
    if #clients == 0 then vim.notify('No formatter for ' .. vim.bo[buf].filetype .. '. Install one with install-dev-tools.sh; see :PixelTools', vim.log.levels.WARN); return end
    vim.lsp.buf.format({ bufnr = buf, async = false, timeout_ms = 1500, filter = function(c) return c.name ~= 'pixel_typescript' end })
    return
  end
  local tick = vim.api.nvim_buf_get_changedtick(buf)
  local text = table.concat(vim.api.nvim_buf_get_lines(buf, 0, -1, false), '\n') .. (vim.bo[buf].endofline and '\n' or '')
  local function apply(result)
    if result.code ~= 0 then vim.notify(result.stderr ~= '' and result.stderr or 'Formatter failed', vim.log.levels.WARN); return end
    if not vim.api.nvim_buf_is_valid(buf) or not vim.bo[buf].modifiable or vim.api.nvim_buf_get_changedtick(buf) ~= tick then vim.notify('Buffer changed; formatter output skipped', vim.log.levels.WARN); return end
    local lines = vim.split(result.stdout:gsub('\n$', ''), '\n', { plain = true })
    local view = vim.api.nvim_get_current_buf() == buf and vim.fn.winsaveview() or nil
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
    if view then vim.fn.winrestview(view) end
  end
  if sync then
    local ok, result = pcall(function() return vim.system(argv, { text = true, stdin = text, cwd = M.root() }):wait(1500) end)
    if ok then apply(result) else vim.notify('Formatter timed out: ' .. argv[1], vim.log.levels.WARN) end
  else
    vim.system(argv, { text = true, stdin = text, cwd = M.root() }, function(result) vim.schedule(function() apply(result) end) end)
  end
end
function M.find_files()
  local ok, pick = pcall(require, 'mini.pick')
  if ok then pick.builtin.files({}, { source = { cwd = M.root() } }); return end
  if vim.fn.executable('rg') == 0 then vim.cmd.Explore(); return end
  local root = M.root()
  vim.system({ 'rg', '--files', '--hidden', '-g', '!.git' }, { cwd = root, text = true }, function(result)
    vim.schedule(function()
      if result.code ~= 0 then vim.notify(result.stderr, vim.log.levels.WARN); return end
      vim.ui.select(vim.split(vim.trim(result.stdout), '\n'), { prompt = 'Project files' }, function(choice) if choice then vim.cmd.edit(vim.fn.fnameescape(root .. '/' .. choice)) end end)
    end)
  end)
end
function M.grep()
  local ok, pick = pcall(require, 'mini.pick')
  if ok then pick.builtin.grep_live({}, { source = { cwd = M.root() } }); return end
  vim.ui.input({ prompt = 'Search project: ' }, function(query)
    if not query or query == '' then return end
    vim.system({ 'rg', '--json', '--smart-case', '--', query, M.root() }, { cwd = M.root(), text = true }, function(result)
      vim.schedule(function()
        if result.code > 1 then vim.notify(result.stderr, vim.log.levels.WARN); return end
        local items = {}
        for line in result.stdout:gmatch('[^\n]+') do
          local parsed, event = pcall(vim.json.decode, line)
          if parsed and event.type == 'match' and event.data.path.text then
            table.insert(items, { filename = event.data.path.text, lnum = event.data.line_number, col = event.data.submatches[1].start + 1, text = event.data.lines.text:gsub('\n$', '') })
          end
        end
        vim.fn.setqflist({}, ' ', { title = query, items = items })
        vim.cmd.copen()
      end)
    end)
  end)
end
function M.buffers()
  local ok, pick = pcall(require, 'mini.pick')
  if ok then pick.builtin.buffers(); return end
  local buffers = vim.tbl_filter(function(buf) return vim.bo[buf].buflisted end, vim.api.nvim_list_bufs())
  vim.ui.select(buffers, { prompt = 'Buffers', format_item = function(buf) return vim.api.nvim_buf_get_name(buf) end }, function(buf) if buf then vim.api.nvim_set_current_buf(buf) end end)
end
function M.file_target()
  local name = vim.api.nvim_buf_get_name(0)
  if vim.bo.buftype == '' and name ~= '' and not name:match('^%a[%w+.-]*:') then
    local stat = vim.uv.fs_stat(name)
    if stat and (stat.type == 'file' or stat.type == 'directory') then return name end
    local parent = vim.fs.dirname(name)
    if parent and vim.fn.isdirectory(parent) == 1 then return parent end
  end
  local root = M.root()
  return vim.fn.isdirectory(root) == 1 and root or vim.uv.cwd()
end
function M.files()
  require('pixel.explorer').toggle()
end
function M.run()
  if vim.bo.modified then vim.notify('Save the file before running it', vim.log.levels.WARN); return end
  local file = vim.api.nvim_buf_get_name(0)
  local commands = { python = { 'python3', file }, lua = { 'lua', file }, javascript = { 'node', file }, sh = { 'bash', file }, bash = { 'bash', file } }
  local cmd = commands[vim.bo.filetype]
  if not cmd then vim.notify('Use project tasks or the integrated terminal for this language', vim.log.levels.INFO); return end
  if vim.fn.executable(cmd[1]) == 0 then vim.notify('Missing runtime: ' .. cmd[1], vim.log.levels.WARN); return end
  M.open_terminal(cmd)
end
function M.tasks()
  local root = M.root()
  local tasks = {}
  if vim.fn.filereadable(root .. '/Cargo.toml') == 1 then tasks = { { 'Cargo check', { 'cargo', 'check' } }, { 'Cargo test', { 'cargo', 'test' } }, { 'Cargo clippy', { 'cargo', 'clippy' } } }
  elseif vim.fn.filereadable(root .. '/go.mod') == 1 then tasks = { { 'Go test', { 'go', 'test', './...' } }, { 'Go vet', { 'go', 'vet', './...' } } }
  elseif vim.fn.filereadable(root .. '/package.json') == 1 then
    local ok, data = pcall(function() return vim.json.decode(table.concat(vim.fn.readfile(root .. '/package.json'), '\n')) end)
    if ok then for name in pairs(data.scripts or {}) do table.insert(tasks, { 'npm run ' .. name, { 'npm', 'run', name } }) end end
    table.sort(tasks, function(a, b) return a[1] < b[1] end)
  elseif vim.fn.filereadable(root .. '/pyproject.toml') == 1 then tasks = { { 'Pytest', { 'python3', '-m', 'pytest' } }, { 'Ruff check', { 'ruff', 'check', '.' } } }
  end
  if #tasks == 0 then vim.notify('No preset tasks found. Open the terminal with Space+t', vim.log.levels.INFO); return end
  vim.ui.select(tasks, { prompt = 'Run project task', format_item = function(t) return t[1] end }, function(task) if task then M.open_terminal(task[2], root) end end)
end
function M.health()
  local lines = { 'PIXEL / DEVELOPMENT TOOLS', '', 'LSP servers (enabled only when installed):' }
  local servers = require('pixel.lsp').servers
  for _, name in ipairs(vim.fn.sort(vim.tbl_keys(servers))) do local spec = servers[name]; table.insert(lines, string.format('  %-14s %s  %s', name, require('pixel.executables').resolve(spec.cmd[1], M.root()) and 'READY' or 'MISSING', spec.cmd[1])) end
  table.insert(lines, ''); table.insert(lines, 'Active LSP clients:')
  for _, client in ipairs(vim.lsp.get_clients({ bufnr = 0 })) do table.insert(lines, '  ' .. client.name .. ' · ' .. (client.root_dir or 'single file')) end
  table.insert(lines, ''); table.insert(lines, 'Formatters:')
  for _, tool in ipairs({ 'ruff', 'stylua', 'prettier', 'gofmt', 'clang-format', 'shfmt' }) do table.insert(lines, '  ' .. tool .. ': ' .. (vim.fn.executable(tool) == 1 and 'READY' or 'MISSING')) end
  table.insert(lines, ''); table.insert(lines, 'Debug / highlighting:')
  for _, tool in ipairs({ 'gdb', 'dlv', 'tree-sitter' }) do table.insert(lines, '  ' .. tool .. ': ' .. (vim.fn.executable(tool) == 1 and 'READY' or 'MISSING')) end
  table.insert(lines, ''); table.insert(lines, 'Install tools: bash ~/dotfiles/tools/install-dev-tools.sh all')
  table.insert(lines, 'Install plugins: :PixelInstall   |   Syntax parsers: :PixelParsers')
  table.insert(lines, 'LSP log: ' .. vim.lsp.log.get_filename())
  vim.cmd('botright new'); vim.bo.buftype = 'nofile'; vim.bo.bufhidden = 'wipe'; vim.bo.swapfile = false
  vim.api.nvim_buf_set_lines(0, 0, -1, false, lines); vim.bo.modifiable = false
end
function M.icons()
  local ok,icons=pcall(require,'mini.icons')
  if not ok then vim.notify('Install mini.nvim first with :PixelInstall',vim.log.levels.WARN);return end
  local lines={'NERD FONT / ICON CHECK','','The left column should contain symbols, not squares.','Terminal font: JetBrainsMono Nerd Font Mono + Symbols Nerd Font Mono.',''}
  for _,name in ipairs({'main.py','app.ts','main.rs','main.go','init.lua','main.cpp','README.md','package.json'}) do
    local glyph=icons.get('file',name)
    local found,devicons=pcall(require,'nvim-web-devicons')
    if found then glyph=devicons.get_icon(name,vim.fn.fnamemodify(name,':e'),{default=true}) or glyph end
    table.insert(lines,glyph..'  '..name)
  end
  vim.cmd('botright new');vim.bo.buftype='nofile';vim.bo.bufhidden='wipe';vim.bo.swapfile=false
  vim.api.nvim_buf_set_lines(0,0,-1,false,lines);vim.bo.modifiable=false
end
function M.setup()
  vim.api.nvim_create_user_command('PixelTools', M.health, {})
  vim.api.nvim_create_user_command('PixelIcons', M.icons, {})
  vim.api.nvim_create_user_command('PixelFormat', function() M.format(false) end, {})
  vim.api.nvim_create_user_command('PixelRun', M.run, {})
  vim.api.nvim_create_user_command('PixelTasks', M.tasks, {})
  vim.api.nvim_create_autocmd('BufWritePre', { group = vim.api.nvim_create_augroup('PixelFormat', { clear = true }), callback = function() if vim.b.pixel_autoformat then M.format(true) end end })
end
return M
