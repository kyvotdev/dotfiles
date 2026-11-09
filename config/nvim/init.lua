vim.g.mapleader = ' '
vim.g.maplocalleader = ','
require('pixel.options')
require('pixel.theme').setup()
require('pixel.tools').setup()
require('pixel.lsp').setup()
require('pixel.plugins').setup()
require('pixel.keys')
