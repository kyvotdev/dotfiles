local o = vim.opt
o.number = true
o.relativenumber = true
o.mouse = 'a'
o.termguicolors = true
o.signcolumn = 'yes'
o.cursorline = true
o.scrolloff = 8
o.sidescrolloff = 6
o.splitright = true
o.splitbelow = true
o.ignorecase = true
o.smartcase = true
o.incsearch = true
o.hlsearch = true
o.expandtab = true
o.shiftwidth = 2
o.tabstop = 2
o.softtabstop = 2
o.smartindent = true
o.breakindent = true
o.wrap = false
o.undofile = true
o.updatetime = 250
o.timeoutlen = 400
o.completeopt = { 'menu', 'menuone', 'noselect', 'popup' }
o.pumheight = 12
o.laststatus = 3
o.showmode = false
o.statusline = ' %{mode()}  %<%f %m%r%=%y  %l:%c  %p%% '
o.clipboard = 'unnamedplus'
o.confirm = true
o.list = true
o.listchars = { tab = '→ ', trail = '·', nbsp = '␣' }
o.fillchars = { eob = ' ' }
o.grepprg = 'rg --vimgrep --smart-case'
o.grepformat = '%f:%l:%c:%m'
o.wildignore:append({ '*/node_modules/*', '*/.git/*', '*/target/*', '*/.venv/*' })
local group = vim.api.nvim_create_augroup('PixelEditor', { clear = true })
vim.api.nvim_create_autocmd('TextYankPost', { group = group, callback = function() vim.hl.on_yank({ timeout = 150 }) end })
vim.api.nvim_create_autocmd('FileType', { group = group, pattern = { 'python' }, callback = function() vim.bo.shiftwidth = 4; vim.bo.softtabstop = 4 end })
vim.api.nvim_create_autocmd('BufReadPost', { group = group, callback = function(ev)
  local mark = vim.api.nvim_buf_get_mark(ev.buf, '"')
  if mark[1] > 0 and mark[1] <= vim.api.nvim_buf_line_count(ev.buf) then pcall(vim.api.nvim_win_set_cursor, 0, mark) end
end })
vim.api.nvim_create_autocmd('FileType', { group = group, callback = function(ev)
  if vim.bo[ev.buf].buftype == '' then pcall(vim.treesitter.start, ev.buf) end
end })
-- No automatic project-local Lua or shell execution.
o.exrc = false
