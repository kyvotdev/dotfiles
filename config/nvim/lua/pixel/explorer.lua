local M = { ready = false }
function M.setup()
  local ok, tree = pcall(require, 'nvim-tree')
  if not ok then return end
  vim.g.loaded_netrw = 1
  vim.g.loaded_netrwPlugin = 1
  tree.setup({
    disable_netrw = true,
    hijack_netrw = true,
    sync_root_with_cwd = true,
    view = { width = 34, side = 'left', signcolumn = 'yes' },
    update_focused_file = { enable = true, update_root = false },
    renderer = {
      group_empty = true,
      highlight_opened_files = 'name',
      indent_markers = { enable = true },
      icons = {
        show = { file = true, folder = true, folder_arrow = true, git = true, diagnostics = true },
        web_devicons = { file = { enable = true, color = false }, folder = { enable = false, color = false } },
        glyphs = {
          default = '', symlink = '',
          folder = { arrow_closed = '', arrow_open = '', default = '', open = '', empty = '', empty_open = '', symlink = '', symlink_open = '' },
        },
      },
    },
    filters = { dotfiles = false },
    git = { enable = true, ignore = true },
    diagnostics = { enable = true, show_on_dirs = true, icons = { hint = '', info = '', warning = '', error = '' } },
    on_attach = function(buf)
      local api = require('nvim-tree.api')
      api.map.on_attach.default(buf)
      local function map(key, action, desc) vim.keymap.set('n', key, action, { buffer = buf, silent = true, nowait = true, desc = desc }) end
      map('l', api.node.open.edit, 'Open file / folder')
      map('h', api.node.navigate.parent_close, 'Close folder / go to parent')
      map('v', api.node.open.vertical, 'Open in vertical split')
      map('s', api.node.open.horizontal, 'Open in horizontal split')
      map('?', api.tree.toggle_help, 'Tree keymap help')
    end,
  })
  M.ready = true
end
function M.target()
  local tools = require('pixel.tools')
  local path = tools.file_target()
  local stat = vim.uv.fs_stat(path)
  if stat and stat.type == 'file' then return tools.root(), path end
  return path, nil
end
function M.toggle()
  if not M.ready then M.setup() end
  if not M.ready then
    -- Keep file navigation usable while the new plugin is awaiting download.
    vim.notify('nvim-tree is not downloaded yet. Run :PixelExplorerInstall, then restart Neovim.',vim.log.levels.WARN)
    local extra_ok,extra=pcall(require,'mini.extra')
    if extra_ok then local root=M.target();extra.pickers.explorer({cwd=root});return end
    vim.cmd.packadd('netrw')
    vim.cmd('Explore '..vim.fn.fnameescape(require('pixel.tools').file_target()))
    return
  end
  local api = require('nvim-tree.api')
  if api.tree.is_visible() then api.tree.close();return end
  local root,file = M.target()
  api.tree.open({ path = root, focus = true })
  if file then api.tree.find_file({ buf = file, open = true, focus = true, update_root = false }) end
end
function M.reveal()
  if not M.ready then M.setup() end
  if not M.ready then M.toggle();return end
  local root,file=M.target()
  local api=require('nvim-tree.api')
  api.tree.open({path=root,focus=true})
  if file then api.tree.find_file({buf=file,open=true,focus=true,update_root=false}) end
end
return M
