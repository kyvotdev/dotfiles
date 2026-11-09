local M = { panels = {} }
function M.panel()
  local widgets = require('dap.ui.widgets')
  if not M.panels.scopes then
    M.panels.scopes = widgets.sidebar(widgets.scopes, {width=40}, 'botright vsplit')
    M.panels.frames = widgets.sidebar(widgets.frames, {height=9}, 'botright split')
  end
  M.panels.scopes.toggle()
  M.panels.frames.toggle()
end
function M.load_launch()
  local path = require('pixel.tools').root() .. '/.vscode/launch.json'
  if vim.fn.filereadable(path) == 1 then
    require('dap.ext.vscode').load_launchjs(path, {gdb={'c','cpp','rust'}, python={'python'}, delve={'go'}})
    vim.notify('Loaded project debug configurations')
  else vim.notify('No .vscode/launch.json in this project', vim.log.levels.INFO) end
end
local function dap_module()
  local ok, dap = pcall(require, 'dap')
  if not ok then vim.notify('Debugger plugin is missing. Run :PixelInstall and restart Neovim.', vim.log.levels.WARN); return end
  return dap
end
function M.native()
  if vim.fn.executable('gdb') == 0 then vim.notify('Install gdb first',vim.log.levels.WARN); return end
  vim.cmd.packadd('termdebug')
  vim.ui.input({prompt='Executable for GDB: ',default=require('pixel.tools').root()..'/',completion='file'},function(path)
    if path and path~='' and vim.fn.isdirectory(path)==0 then vim.cmd('Termdebug '..vim.fn.fnameescape(path)) end
  end)
end
function M.setup()
  local ok, dap = pcall(require, 'dap')
  if ok then
    dap.adapters.python = function(callback)
      local root = require('pixel.tools').root()
      local candidates = { root .. '/.venv/bin/python', root .. '/venv/bin/python', vim.fn.exepath('python3') }
      for _, python in ipairs(candidates) do
        if vim.fn.executable(python) == 1 then
          local result = vim.system({python, '-c', 'import debugpy'}, {text=true}):wait(3000)
          if result.code == 0 then
            callback({type='executable',command=python,args={'-m','debugpy.adapter'}})
            return
          end
        end
      end
      vim.notify('Python debugger missing: install python-debugpy or debugpy in the project virtualenv.', vim.log.levels.ERROR)
      return
    end
    dap.configurations.python = { { name = 'Debug current Python file', type = 'python', request = 'launch', program = '${file}', cwd = '${workspaceFolder}', console = 'integratedTerminal', justMyCode = false, pythonPath = function()
      local localpython = require('pixel.tools').root() .. '/.venv/bin/python'
      return vim.fn.executable(localpython) == 1 and localpython or vim.fn.exepath('python3')
    end } }
    dap.adapters.gdb = { type = 'executable', command = 'gdb', args = { '-i', 'dap' } }
    local function executable()
      local file = vim.fn.input('Executable: ', require('pixel.tools').root() .. '/', 'file')
      if file == '' or vim.fn.isdirectory(file) == 1 then return dap.ABORT end
      return vim.fn.fnamemodify(file, ':p')
    end
    dap.configurations.c = { { name = 'Launch executable (GDB)', type = 'gdb', request = 'launch', program = executable, cwd = '${workspaceFolder}', stopAtBeginningOfMainSubprogram = false } }
    dap.configurations.cpp = vim.deepcopy(dap.configurations.c)
    dap.configurations.rust = vim.deepcopy(dap.configurations.c)
    dap.adapters.delve = { type = 'server', port = '${port}', executable = { command = 'dlv', args = { 'dap', '-l', '127.0.0.1:${port}' } } }
    dap.configurations.go = { { name = 'Debug Go package', type = 'delve', request = 'launch', program = '${fileDirname}' }, { name = 'Debug Go tests', type = 'delve', request = 'launch', mode = 'test', program = '${fileDirname}' } }
    vim.fn.sign_define('DapBreakpoint', { text = '●', texthl = 'DiagnosticWarn' })
    vim.fn.sign_define('DapStopped', { text = '▶', texthl = 'DiagnosticInfo', linehl = 'Visual' })
  end
  vim.keymap.set('n','<leader>dd',M.native,{desc='Native GDB debugger (no plugin download)'})
  local function map(key, action, desc)
    vim.keymap.set('n', key, function() local d = dap_module(); if d then action(d) end end, { desc = desc })
  end
  map('<F5>', function(d) d.continue() end, 'Debug: start / continue')
  map('<F10>', function(d) d.step_over() end, 'Debug: step over')
  map('<F11>', function(d) d.step_into() end, 'Debug: step into')
  map('<S-F11>', function(d) d.step_out() end, 'Debug: step out')
  map('<leader>du', function() M.panel() end, 'Debug: variables and stack panel')
  map('<leader>dl', function() M.load_launch() end, 'Debug: load project launch.json')
  map('<leader>dc', function(d) d.run_to_cursor() end, 'Debug: run to cursor')
  map('<leader>dx', function(d) d.clear_breakpoints() end, 'Debug: clear breakpoints')
  map('<leader>db', function(d) d.toggle_breakpoint() end, 'Debug: breakpoint')
  map('<leader>dB', function(d) vim.ui.input({ prompt = 'Breakpoint condition: ' }, function(value) if value then d.set_breakpoint(value) end end) end, 'Debug: conditional breakpoint')
  map('<leader>dq', function(d) d.terminate() end, 'Debug: stop')
  map('<leader>dr', function(d) d.repl.toggle() end, 'Debug: console')
  map('<leader>de', function() require('dap.ui.widgets').hover() end, 'Debug: inspect value')
  map('<leader>ds', function() local w = require('dap.ui.widgets'); w.sidebar(w.scopes, {}, 'botright 45vsplit').open() end, 'Debug: variable scopes')
  map('<leader>df', function() local w = require('dap.ui.widgets'); w.sidebar(w.frames, {}, 'botright 45vsplit').open() end, 'Debug: stack frames')
end
return M
