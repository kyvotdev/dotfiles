local M = {}
M.servers = {
  lua = { cmd = { 'lua-language-server' }, filetypes = { 'lua' }, root_markers = { '.luarc.json', '.luarc.jsonc', '.git' }, settings = { Lua = { diagnostics = { globals = { 'vim' } }, workspace = { checkThirdParty = false }, telemetry = { enable = false } } } },
  python = { cmd = { 'pyright-langserver', '--stdio' }, filetypes = { 'python' }, root_markers = { 'pyrightconfig.json', 'pyproject.toml', 'setup.py', '.git' }, settings = { python = { analysis = { typeCheckingMode = 'basic', autoSearchPaths = true, useLibraryCodeForTypes = true } } } },
  ruff = { cmd = { 'ruff', 'server' }, filetypes = { 'python' }, root_markers = { 'ruff.toml', '.ruff.toml', 'pyproject.toml', '.git' } },
  typescript = { cmd = { 'typescript-language-server', '--stdio' }, filetypes = { 'javascript', 'javascriptreact', 'typescript', 'typescriptreact' }, root_markers = { 'tsconfig.json', 'jsconfig.json', 'package.json', '.git' } },
  rust = { cmd = { 'rust-analyzer' }, filetypes = { 'rust' }, root_markers = { 'Cargo.toml', 'rust-project.json', '.git' }, settings = { ['rust-analyzer'] = { check = { command = 'clippy' } } } },
  go = { cmd = { 'gopls' }, filetypes = { 'go', 'gomod', 'gowork', 'gotmpl' }, root_markers = { 'go.work', 'go.mod', '.git' }, settings = { gopls = { gofumpt = true, staticcheck = true } } },
  clang = { cmd = { 'clangd', '--background-index', '--clang-tidy' }, filetypes = { 'c', 'cpp', 'objc', 'objcpp', 'cuda' }, root_markers = { '.clangd', 'compile_commands.json', 'compile_flags.txt', '.git' } },
  bash = { cmd = { 'bash-language-server', 'start' }, filetypes = { 'sh', 'bash' }, root_markers = { '.git' } },
  json = { cmd = { 'vscode-json-languageserver', '--stdio' }, filetypes = { 'json', 'jsonc' }, root_markers = { 'package.json', '.git' } },
  yaml = { cmd = { 'yaml-language-server', '--stdio' }, filetypes = { 'yaml', 'yaml.docker-compose' }, root_markers = { '.git' }, settings = { yaml = { keyOrdering = false } } },
  html = { cmd = { 'vscode-html-languageserver', '--stdio' }, filetypes = { 'html' }, root_markers = { 'package.json', '.git' } },
  css = { cmd = { 'vscode-css-languageserver', '--stdio' }, filetypes = { 'css', 'scss', 'less' }, root_markers = { 'package.json', '.git' } },
  toml = { cmd = { 'taplo', 'lsp', 'stdio' }, filetypes = { 'toml' }, root_markers = { 'taplo.toml', '.taplo.toml', 'Cargo.toml', '.git' } },
  markdown = { cmd = { 'marksman', 'server' }, filetypes = { 'markdown', 'markdown.mdx' }, root_markers = { '.marksman.toml', '.git' } },
  php = { cmd = { 'intelephense', '--stdio' }, filetypes = { 'php' }, root_markers = { 'composer.json', '.git' } },
  ruby = { cmd = { 'ruby-lsp' }, filetypes = { 'ruby' }, root_markers = { 'Gemfile', '.git' } },
  csharp = { cmd = { 'csharp-ls' }, filetypes = { 'cs' }, root_markers = { 'Directory.Build.props', 'global.json', '.git' } },
  java = { cmd = { 'jdtls' }, filetypes = { 'java' }, root_markers = { 'pom.xml', 'build.gradle', 'build.gradle.kts', '.git' } },
  docker = { cmd = { 'docker-langserver', '--stdio' }, filetypes = { 'dockerfile' }, root_markers = { 'Dockerfile', '.git' } },
  sql = { cmd = { 'sqls' }, filetypes = { 'sql' }, root_markers = { '.sqls.yml', '.git' } },
}
function M.enable(buf)
  buf = buf or vim.api.nvim_get_current_buf()
  if not vim.api.nvim_buf_is_valid(buf) then return end
  local filename = vim.api.nvim_buf_get_name(buf)
  local root = filename ~= '' and (vim.fs.root(filename, { 'pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod', '.git' }) or vim.fs.dirname(filename)) or vim.uv.cwd()
  local resolver = require('pixel.executables').resolve
  for name, template in pairs(M.servers) do
    if resolver(template.cmd[1], root) then
      local spec = vim.deepcopy(template)
      spec.capabilities = vim.lsp.protocol.make_client_capabilities()
      spec.capabilities.textDocument.completion.completionItem.snippetSupport = true
      local original = vim.deepcopy(spec.cmd)
      spec.cmd = function(dispatchers, config)
        local argv = vim.deepcopy(original)
        argv[1] = resolver(argv[1], config.root_dir or root) or argv[1]
        if name == 'java' then
          local workspace = vim.fn.stdpath('cache') .. '/jdtls/' .. vim.fn.sha256(config.root_dir or root)
          vim.fn.mkdir(workspace, 'p'); vim.list_extend(argv, { '-data', workspace })
        end
        return vim.lsp.rpc.start(argv, dispatchers, { cwd = config.root_dir })
      end
      vim.lsp.config('pixel_' .. name, spec)
      vim.lsp.enable('pixel_' .. name)
    end
  end
end
function M.setup()
  vim.diagnostic.config({ severity_sort = true, update_in_insert = false, virtual_text = { spacing = 2, prefix = '·' }, float = { border = 'single', source = true }, signs = { text = { [1] = 'E', [2] = 'W', [3] = 'I', [4] = 'H' } } })
  vim.api.nvim_create_autocmd('LspAttach', { group = vim.api.nvim_create_augroup('PixelLsp', { clear = true }), callback = function(ev)
    local client = vim.lsp.get_client_by_id(ev.data.client_id)
    if not client then return end
    if client.name == 'pixel_ruff' then client.server_capabilities.hoverProvider = false end
    if not _G.MiniCompletion and client:supports_method('textDocument/completion') then vim.lsp.completion.enable(true, client.id, ev.buf, { autotrigger = true }) end
    local function map(key, action, desc) vim.keymap.set('n', key, action, { buffer = ev.buf, desc = desc }) end
    map('gd', vim.lsp.buf.definition, 'Definition'); map('gD', vim.lsp.buf.declaration, 'Declaration')
    map('gr', vim.lsp.buf.references, 'References'); map('gi', vim.lsp.buf.implementation, 'Implementation')
    map('K', vim.lsp.buf.hover, 'Documentation'); map('<leader>cr', vim.lsp.buf.rename, 'Rename symbol')
    map('<leader>ca', vim.lsp.buf.code_action, 'Code actions'); map('<leader>cs', vim.lsp.buf.document_symbol, 'Document symbols')
    map('<leader>ct', vim.lsp.buf.type_definition, 'Type definition')
    vim.keymap.set('i', '<C-k>', vim.lsp.buf.signature_help, { buffer = ev.buf, desc = 'Signature help' })
  end })
  vim.api.nvim_create_user_command('PixelLspReload', function() M.enable() end, {})
  vim.api.nvim_create_autocmd('FileType', { group = 'PixelLsp', callback = function(ev) vim.schedule(function() M.enable(ev.buf) end) end })
  M.enable()
end
return M
