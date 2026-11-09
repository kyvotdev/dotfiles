-- Verify the tree adapter never sends virtual buffers to its filesystem API.
local root=assert(vim.env.PIXEL_IDE_TEST_ROOT)
vim.cmd.cd(vim.fn.fnameescape(root));vim.cmd.enew();vim.bo.buftype='nofile'
vim.api.nvim_buf_set_name(0,'ministarter:/1/welcome')
local captured,opened,revealed,closed=nil,nil,nil,false
package.loaded['nvim-tree']={setup=function(opts)captured=opts end}
package.loaded['nvim-tree.api']={tree={
 is_visible=function()return false end,
 open=function(opts)opened=opts end,
 find_file=function(opts)revealed=opts end,
 close=function()closed=true end,
}}
local explorer=require('pixel.explorer');explorer.ready=false;explorer.setup();explorer.toggle()
assert(opened.path==root,'Starter URI leaked into tree root')
assert(revealed==nil,'Virtual buffer was treated as a file')
assert(captured.renderer.icons.show.file and captured.renderer.icons.show.folder,'Tree icons disabled')
assert(captured.renderer.icons.web_devicons.file.enable,'Real file icon provider disabled')
vim.cmd.edit(vim.fn.fnameescape(root..'/main.py'));explorer.reveal()
assert(revealed.buf==root..'/main.py','Normal file was not revealed')
assert(vim.fn.maparg('<Space>E','n')~='','Reveal keymap missing')
print('Explorer adapter: virtual buffers, normal files, icon configuration and reveal mapping passed')
