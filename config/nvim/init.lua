vim.g.mapleader = ' '
vim.g.maplocalleader = ','
-- All configured plugins are Lua-based; optional legacy providers are unnecessary.
vim.g.loaded_node_provider = 0
vim.g.loaded_python3_provider = 0
vim.g.loaded_ruby_provider = 0
vim.g.loaded_perl_provider = 0
require('pixel.options')
require('pixel.theme').setup()
require('pixel.tools').setup()
require('pixel.plugins').setup()
require('pixel.lsp').setup()
require('pixel.debug').setup()
require('pixel.ide').setup()
require('pixel.terminal').setup()
require('pixel.keys')
