local M = { buffers = {} }
local function open_window(buf, vertical)
  vim.cmd(vertical and 'botright vsplit' or 'botright 14split')
  vim.api.nvim_win_set_buf(0, buf)
  vim.wo.number = false
  vim.wo.relativenumber = false
  vim.wo.signcolumn = 'no'
  vim.cmd.startinsert()
end
function M.toggle(vertical)
  local root = vim.b.pixel_terminal_root or require('pixel.tools').root()
  local buf = M.buffers[root]
  if buf and vim.api.nvim_buf_is_valid(buf) then
    local win = vim.fn.bufwinid(buf)
    if win ~= -1 then
      if #vim.api.nvim_list_wins() > 1 then vim.api.nvim_win_close(win, false) end
      return
    end
    open_window(buf, vertical)
    return
  end
  buf = vim.api.nvim_create_buf(false, true)
  M.buffers[root] = buf
  vim.b[buf].pixel_terminal_root = root
  open_window(buf, vertical)
  vim.bo[buf].bufhidden = 'hide'
  local shell = vim.fn.executable('fish') == 1 and 'fish' or vim.o.shell
  local job = vim.fn.jobstart({ shell }, { term = true, cwd = root, on_exit = function()
    vim.schedule(function() if M.buffers[root] == buf then M.buffers[root] = nil end end)
  end })
  if job <= 0 then M.buffers[root] = nil;vim.notify('Failed to start project shell', vim.log.levels.ERROR) end
end
function M.setup()
  vim.api.nvim_create_user_command('PixelTerminal', function(args) M.toggle(args.bang) end, { bang = true })
  vim.keymap.set({'n','t'}, '<C-\\>', function() M.toggle() end, { desc = 'Toggle project terminal' })
  vim.keymap.set('t','<C-h>','<C-\\><C-n><C-w>h',{desc='Left split'})
  vim.keymap.set('t','<C-j>','<C-\\><C-n><C-w>j',{desc='Lower split'})
  vim.keymap.set('t','<C-k>','<C-\\><C-n><C-w>k',{desc='Upper split'})
  vim.keymap.set('t','<C-l>','<C-\\><C-n><C-w>l',{desc='Right split'})
end
return M
