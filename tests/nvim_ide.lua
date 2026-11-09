assert(vim.v.errmsg == '', 'Startup error: '..vim.v.errmsg)
assert(#require('pixel.plugins').errors==0,'Plugin setup errors')
assert(_G.MiniCompletion,'Automatic completion module is not loaded')
assert(_G.MiniPick and _G.MiniStarter,'Editor UI is not loaded')
local root=assert(vim.env.PIXEL_IDE_TEST_ROOT)
vim.cmd.cd(vim.fn.fnameescape(root))
vim.cmd.enew()
vim.bo.buftype='nofile'
vim.api.nvim_buf_set_name(0,'ministarter:/1/welcome')
assert(require('pixel.tools').file_target()==root,'Virtual starter path was treated as a real file')
local explorer=require('pixel.explorer')
if explorer.ready then
  require('pixel.tools').files()
  assert(require('nvim-tree.api').tree.is_visible(),'Tree did not open from starter')
  require('nvim-tree.api').tree.close()
else
  -- A real file picker remains usable while the tree awaits its download.
  local notify=vim.notify;vim.notify=function()end
  local fallback_items=0
  vim.defer_fn(function()local items=MiniPick.get_picker_items();fallback_items=items and #items or 0;MiniPick.stop()end,150)
  require('pixel.tools').files()
  vim.notify=notify
  assert(fallback_items>0,'Temporary file navigation did not open')
end
local count=0
vim.defer_fn(function()
  local items=MiniPick.get_picker_items()
  count=items and #items or 0
  MiniPick.stop()
end,250)
require('pixel.tools').find_files()
assert(count>0,'Project file search returned no files')
assert(vim.v.errmsg == '', 'UI error: '..vim.v.errmsg)
assert(vim.fn.maparg('<F5>','n')~='','Debug keymaps missing')
assert(vim.fn.maparg('<Space>ss','n')~='','Session keymaps missing')
assert(vim.fn.exists(':PixelParsers')==2,'Parser install command missing')
assert(vim.fn.exists(':PixelExplorerInstall')==2,'Explorer installation command missing')
print('IDE integration: startup, explorer, actual file picker, completion and keymaps passed')

local term=require('pixel.terminal')
term.toggle()
local terminal=term.buffers[root]
assert(terminal and vim.bo[terminal].buftype=='terminal','Project terminal did not start')
term.toggle()
assert(vim.fn.bufwinid(terminal)==-1,'Terminal was not hidden')
term.toggle()
assert(vim.api.nvim_get_current_buf()==terminal,'Terminal session was not reused')
term.toggle()
require('pixel.debug').panel()
require('pixel.debug').panel()
print('Terminal persistence and debugger panels passed')
