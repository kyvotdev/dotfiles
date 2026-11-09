local M = {}
local function extra(name, options)
  local ok, module = pcall(require, 'mini.extra')
  if not ok then vim.notify('Install the editor UI with :PixelInstall', vim.log.levels.WARN); return end
  module.pickers[name](options or {}, { source = { cwd = require('pixel.tools').root() } })
end
function M.project()
  vim.ui.input({ prompt = 'Project directory: ', default = vim.uv.cwd() .. '/', completion = 'dir' }, function(value)
    if not value or value == '' then return end
    local path = vim.fn.expand(value)
    if vim.fn.isdirectory(path) == 0 then vim.notify('Directory not found', vim.log.levels.WARN); return end
    vim.cmd.cd(vim.fn.fnameescape(path));require('pixel.tools').files()
  end)
end
function M.setup()
  local map = function(key, action, desc) vim.keymap.set('n', key, action, { desc = desc }) end
  map('<leader>fp', M.project, 'Open project')
  map('<leader>fr', function() extra('oldfiles') end, 'Recent files')
  map('<leader>/', function() extra('buf_lines', { scope = 'current' }) end, 'Search current buffer')
  map('<leader>xx', function() extra('diagnostic', { scope = 'all' }) end, 'Workspace diagnostics')
  map('<leader>co', function() extra('lsp', { scope = 'document_symbol' }) end, 'Document outline')
  map('<leader>gb', function() extra('git_branches') end, 'Git branches')
  map('<leader>gc', function() extra('git_commits') end, 'Git commits')
  map('<leader>gh', function() extra('git_hunks') end, 'Git hunks')
  map('<leader>go', function() local ok,diff=pcall(require,'mini.diff');if ok then diff.toggle_overlay() end end, 'Git diff overlay')
  map('<leader>ss', function()
    local ok,sessions=pcall(require,'mini.sessions');if not ok then return end
    local root=require('pixel.tools').root();sessions.write(vim.fs.basename(root)..'-'..vim.fn.sha256(root):sub(1,8))
  end, 'Save project session')
  map('<leader>sl', function() local ok,s=pcall(require,'mini.sessions');if ok then s.select('read') end end, 'Load saved session')
  map('<leader>un', function() local ok,n=pcall(require,'mini.notify');if ok then n.show_history() end end, 'Notification history')
end
return M
