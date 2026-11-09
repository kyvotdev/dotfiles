local M = {}
function M.apply()
  local p = { bg = '#0d0e10', surface = '#17191d', edge = '#363c46', fg = '#d5dbe3', muted = '#8793a3', accent = '#80b7db', accent2 = '#9aafdb', warn = '#d4bc73' }
  local file = vim.fn.expand('~/.local/state/pixel-shell/palette.json')
  local ok, value = pcall(function() return vim.json.decode(table.concat(vim.fn.readfile(file), '\n')) end)
  if ok and type(value) == 'table' then p = vim.tbl_extend('force', p, value) end
  vim.o.background = 'dark'
  vim.g.colors_name = 'pixel-shell'
  local function hl(name, settings) vim.api.nvim_set_hl(0, name, settings) end
  for _, name in ipairs({ 'Normal', 'NormalNC', 'SignColumn', 'EndOfBuffer' }) do hl(name, { fg = p.fg, bg = 'NONE' }) end
  for _, name in ipairs({ 'NormalFloat', 'Pmenu', 'MiniPickNormal', 'MiniFilesNormal' }) do hl(name, { fg = p.fg, bg = p.surface }) end
  for _, name in ipairs({ 'FloatBorder', 'WinSeparator', 'MiniPickBorder', 'MiniFilesBorder' }) do hl(name, { fg = p.edge, bg = p.surface }) end
  for _,name in ipairs({'NvimTreeNormal','NvimTreeNormalNC','NvimTreeEndOfBuffer'}) do hl(name,{fg=p.fg,bg=p.surface}) end
  for _,name in ipairs({'NvimTreeFolderIcon','NvimTreeFolderName','NvimTreeOpenedFolderName','NvimTreeFileIcon','DevIconDefault'}) do hl(name,{fg=p.accent}) end
  for _,name in ipairs({'NvimTreeGitNewIcon','NvimTreeGitStagedIcon','NvimTreeGitRenamedIcon','NvimTreeSymlinkIcon'}) do hl(name,{fg=p.accent2}) end
  hl('NvimTreeRootFolder',{fg=p.accent2,bold=true});hl('NvimTreeIndentMarker',{fg=p.edge})
  hl('NvimTreeCursorLine',{bg=p.edge});hl('NvimTreeOpenedHL',{fg=p.accent2,bold=true})
  for _,name in ipairs({'NvimTreeGitDirtyIcon','NvimTreeGitDeletedIcon','NvimTreeDiagnosticErrorIcon','NvimTreeDiagnosticWarnIcon'}) do hl(name,{fg=p.warn}) end
  hl('CursorLine', { bg = p.surface }); hl('CursorLineNr', { fg = p.accent, bold = true })
  hl('LineNr', { fg = p.muted }); hl('Comment', { fg = p.muted, italic = true })
  hl('Visual', { bg = p.edge }); hl('PmenuSel', { bg = p.edge, fg = p.accent, bold = true })
  hl('Search', { bg = p.edge, fg = p.accent }); hl('IncSearch', { bg = p.accent, fg = p.bg })
  hl('StatusLine', { bg = p.surface, fg = p.fg }); hl('StatusLineNC', { bg = p.surface, fg = p.muted })
  hl('TabLineSel', { bg = p.edge, fg = p.accent, bold = true }); hl('Directory', { fg = p.accent })
  for _, name in ipairs({ 'Function', 'Identifier', 'Type', '@function', '@function.call', '@type', '@variable.member' }) do hl(name, { fg = p.accent }) end
  for _, name in ipairs({ 'String', 'Constant', '@string', '@number', 'Number', 'Boolean' }) do hl(name, { fg = p.accent2 }) end
  for _, name in ipairs({ 'Statement', 'Keyword', 'PreProc', '@keyword', '@keyword.function' }) do hl(name, { fg = p.accent2, bold = true }) end
  for _, name in ipairs({ 'Error', 'ErrorMsg', 'WarningMsg', 'DiagnosticError', 'DiagnosticWarn' }) do hl(name, { fg = p.warn }) end
  for _, name in ipairs({ 'DiagnosticInfo', 'DiagnosticHint' }) do hl(name, { fg = p.accent2 }) end
  hl('DiagnosticUnderlineError', { undercurl = true, sp = p.warn }); hl('DiagnosticUnderlineWarn', { undercurl = true, sp = p.warn })
  hl('DiffAdd', { bg = p.surface, fg = p.accent }); hl('DiffDelete', { bg = p.surface, fg = p.warn })
  hl('MiniDiffSignAdd', { fg = p.accent }); hl('MiniDiffSignDelete', { fg = p.warn }); hl('MiniDiffSignChange', { fg = p.accent2 })
  hl('DiffChange', { bg = p.edge }); hl('DiffText', { bg = p.edge, fg = p.accent2, bold = true })
  for _, name in ipairs({ 'MiniStatuslineModeNormal', 'MiniStatuslineModeInsert', 'MiniStatuslineModeVisual' }) do hl(name, { bg = p.accent, fg = p.bg, bold = true }) end
  hl('MiniStatuslineDevinfo', { bg = p.edge, fg = p.fg }); hl('MiniStatuslineFilename', { bg = p.surface, fg = p.fg })
  hl('MiniPickMatchCurrent', { bg = p.edge }); hl('MiniPickMatchRanges', { fg = p.accent, bold = true })
  -- Both icon providers use the wallpaper palette, including file-specific groups.
  local icons_ok, devicons = pcall(require, 'nvim-web-devicons')
  if icons_ok then
    for _, icon in pairs(devicons.get_icons()) do
      if icon.name then hl('DevIcon' .. icon.name, { fg = p.accent2 }) end
    end
  end
  -- Keep icon colors in the same cold palette.
  for _, name in ipairs({ 'MiniIconsAzure', 'MiniIconsBlue', 'MiniIconsCyan', 'MiniIconsGreen', 'MiniIconsOrange', 'MiniIconsPurple', 'MiniIconsRed', 'MiniIconsYellow' }) do hl(name, { fg = p.accent2 }) end
end
function M.setup()
  M.apply()
  vim.api.nvim_create_user_command('PixelTheme', M.apply, {})
  local group = vim.api.nvim_create_augroup('PixelTheme', { clear = true })
  vim.api.nvim_create_autocmd({ 'FocusGained', 'ColorScheme' }, { group = group, callback = M.apply })
  local timer = vim.uv.new_timer()
  local last = ''
  timer:start(1500, 1500, vim.schedule_wrap(function()
    local stat = vim.uv.fs_stat(vim.fn.expand('~/.local/state/pixel-shell/palette.json'))
    local stamp = stat and (stat.mtime.sec .. ':' .. stat.mtime.nsec) or ''
    if stamp ~= last then last = stamp; M.apply() end
  end))
  vim.api.nvim_create_autocmd('VimLeavePre', { group = group, callback = function() timer:stop(); timer:close() end })
end
return M
