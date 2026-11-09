local M = {}
function M.setup()
  local path = vim.fn.stdpath('data') .. '/site/pack/pixel/start/mini.nvim'
  vim.api.nvim_create_user_command('PixelInstall', function()
    if vim.fn.isdirectory(path) == 1 then vim.notify('mini.nvim is installed; use :PixelUpdate to update it'); return end
    vim.fn.mkdir(vim.fs.dirname(path), 'p')
    local staging = path .. '.download-' .. vim.fn.getpid()
    if vim.fn.isdirectory(staging) == 1 then vim.notify('Plugin download already running', vim.log.levels.WARN); return end
    vim.notify('Downloading mini.nvim…')
    vim.system({ 'git', 'clone', '--filter=blob:none', '--branch', 'stable', 'https://github.com/nvim-mini/mini.nvim', staging }, { text = true }, function(result)
      vim.schedule(function()
        if result.code ~= 0 then vim.fn.delete(staging, 'rf'); vim.notify(result.stderr, vim.log.levels.ERROR); return end
        if vim.fn.isdirectory(path) == 1 then vim.fn.delete(staging, 'rf'); return end
        vim.uv.fs_rename(staging, path)
        vim.notify('Installed mini.nvim. Restart Neovim to load the plugins.')
      end)
    end)
  end, {})
  vim.api.nvim_create_user_command('PixelUpdate', function()
    if vim.fn.isdirectory(path) == 0 then vim.notify('Run :PixelInstall first'); return end
    vim.system({ 'git', '-C', path, 'pull', '--ff-only' }, { text = true }, function(result) vim.schedule(function() vim.notify(result.code == 0 and 'Updated mini.nvim. Restart Neovim.' or result.stderr) end) end)
  end, {})
  -- Core editing, LSP, completion, formatting and colors work without plugins.
  if vim.fn.isdirectory(path) == 0 then return end
  vim.cmd.packadd('mini.nvim')
  for _, name in ipairs({ 'icons', 'pick', 'extra', 'files', 'pairs', 'surround', 'comment', 'ai', 'diff', 'git', 'statusline', 'clue' }) do
    local ok, module = pcall(require, 'mini.' .. name)
    if ok then
      local options = name == 'clue' and { triggers = { { mode = 'n', keys = '<Leader>' }, { mode = 'x', keys = '<Leader>' }, { mode = 'n', keys = 'g' }, { mode = 'n', keys = '<C-w>' } } } or {}
      local success, err = pcall(module.setup, options)
      if not success then vim.schedule(function() vim.notify('mini.' .. name .. ': ' .. err, vim.log.levels.WARN) end) end
    end
  end
  require('pixel.theme').apply()
end
return M
