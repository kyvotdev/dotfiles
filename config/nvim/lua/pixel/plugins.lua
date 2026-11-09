local M = { errors = {}, busy = false }
M.specs = vim.json.decode(table.concat(vim.fn.readfile(vim.fn.stdpath('config') .. '/plugins.json'), '\n'))
function M.path(spec) return vim.fn.stdpath('data') .. '/site/pack/pixel/start/' .. spec.name end
function M.sync(update)
  if M.busy then vim.notify('Plugin operation already running', vim.log.levels.WARN); return end
  M.busy = true
  local command = { 'python3', vim.fn.stdpath('config') .. '/scripts/install-plugins.py' }
  if update then table.insert(command, '--update') end
  vim.notify('Installing editor plugins in the background…')
  return vim.system(command, { text = true }, function(result)
    vim.schedule(function()
      M.busy = false
      local ok, data = pcall(vim.json.decode, result.stdout or '')
      if not ok then vim.notify(result.stderr ~= '' and result.stderr or 'Plugin installer failed', vim.log.levels.ERROR); return end
      M.errors = data.errors or {}
      if #M.errors > 0 then vim.notify(table.concat(M.errors, '\n'), vim.log.levels.ERROR)
      else vim.notify('Plugins ready. Restart Neovim, then run :PixelParsers.') end
    end)
  end)
end
function M.setup()
  vim.api.nvim_create_user_command('PixelInstall', function() vim.schedule(function() M.sync(false) end) end, {})
  vim.api.nvim_create_user_command('PixelUpdate', function() vim.schedule(function() M.sync(true) end) end, {})
  vim.api.nvim_create_user_command('PixelParsers', function(args)
    local ok, ts = pcall(require, 'nvim-treesitter')
    if not ok then vim.notify('Run :PixelInstall and restart Neovim first', vim.log.levels.WARN); return end
    if vim.fn.executable('tree-sitter') == 0 then vim.notify('Install tree-sitter-cli first; see :PixelTools', vim.log.levels.WARN); return end
    local langs = #args.fargs > 0 and args.fargs or { 'python', 'javascript', 'typescript', 'tsx', 'rust', 'go', 'cpp', 'bash', 'json', 'yaml', 'html', 'css', 'toml' }
    ts.install(langs)
  end, { nargs = '*' })
  -- mini.files clears netrw's group on startup; it must exist even when netrw is optional.
  vim.api.nvim_create_augroup('FileExplorer', { clear = false })
  local function setup(name, opts)
    local ok, module = pcall(require, 'mini.' .. name)
    if not ok then return end
    local success, err = pcall(module.setup, opts or {})
    if not success then table.insert(M.errors, 'mini.' .. name .. ': ' .. tostring(err)) end
  end
  if vim.fn.isdirectory(M.path(M.specs[1])) == 1 then
    vim.cmd.packadd('mini.nvim')
    setup('notify', { window = { config = { border = 'single' }, winblend = 0 }, lsp_progress = { duration_last = 1200 } })
    for _, name in ipairs({ 'icons', 'pick', 'extra', 'files', 'pairs', 'surround', 'comment', 'ai', 'diff', 'git', 'statusline' }) do setup(name) end
    setup('completion', { delay = { completion = 120, info = 120, signature = 70 }, window = { info = { border = 'single' }, signature = { border = 'single' } } })
    setup('starter', { header = 'PIXEL / DEVELOPMENT', footer = 'Space: commands   /   :PixelTools: language tools', items = {
      { name = 'Find project file', action = function() require('pixel.tools').find_files() end, section = 'Project' },
      { name = 'Open project directory', action = function() require('pixel.ide').project() end, section = 'Project' },
      { name = 'Recent files', action = function() require('mini.extra').pickers.oldfiles() end, section = 'Project' },
      { name = 'Language tools and health', action = function() require('pixel.tools').health() end, section = 'Setup' },
      { name = 'Install missing plugins', action = 'PixelInstall', section = 'Setup' },
      { name = 'Quit', action = 'qa', section = 'Editor' },
    } })
    setup('sessions', { directory = vim.fn.stdpath('state') .. '/sessions', file = '', autoread = false, autowrite = false })
    setup('clue', { triggers = { { mode = 'n', keys = '<Leader>' }, { mode = 'x', keys = '<Leader>' }, { mode = 'n', keys = 'g' }, { mode = 'n', keys = '<C-w>' } }, window = { delay = 300, config = { width = 'auto' } } })
  end
  for _, spec in ipairs({ M.specs[2], M.specs[3] }) do
    if vim.fn.isdirectory(M.path(spec)) == 1 then vim.cmd.packadd(spec.name) end
  end
  if pcall(require, 'nvim-treesitter') then require('nvim-treesitter').setup({ install_dir = vim.fn.stdpath('data') .. '/site' }) end
  if #M.errors > 0 then vim.schedule(function() vim.notify(table.concat(M.errors, '\n'), vim.log.levels.ERROR) end) end
  require('pixel.theme').apply()
end
return M
