local function check(value, message) assert(value, message) end
check(vim.fn.exists(':PixelInstall') == 2, 'Plugin command missing')
check(vim.fn.exists(':PixelTools') == 2, 'Tools command missing')
check(vim.fn.maparg('<Space>ff', 'n') ~= '', 'Find files mapping missing')
check(vim.fn.maparg('<Space>cf', 'n') ~= '', 'Format mapping missing')
check(vim.o.exrc == false, 'Project-local code execution must be disabled')
check(require('pixel.lsp').servers.python.cmd[1] == 'pyright-langserver', 'Python server missing')
check(require('pixel.lsp').servers.typescript.filetypes[4] == 'typescriptreact', 'TSX support missing')
local tools = require('pixel.tools')
local original = tools.format_command
local notify = vim.notify
vim.notify = function() end
vim.cmd.enew()
vim.bo.filetype = 'python'
vim.api.nvim_buf_set_lines(0, 0, -1, false, { 'hello' })
tools.format_command = function() return { 'python3', '-c', 'import sys;print(sys.stdin.read().upper(),end="")' } end
tools.format(false)
check(vim.wait(2000, function() return vim.api.nvim_get_current_line() == 'HELLO' end), 'Async formatting did not apply')
tools.format_command = function() return { 'python3', '-c', 'import sys,time;s=sys.stdin.read();time.sleep(.15);print(s.upper(),end="")' } end
vim.api.nvim_buf_set_lines(0, 0, -1, false, { 'original' })
tools.format(false)
vim.api.nvim_buf_set_lines(0, 0, -1, false, { 'edited while formatter runs' })
vim.wait(400, function() return false end)
check(vim.api.nvim_get_current_line() == 'edited while formatter runs', 'Formatter overwrote a newer edit')
vim.notify = notify; tools.format_command = original
vim.bo.modified = false
print('Neovim smoke: commands, mappings, language setup and formatter race protection passed')
