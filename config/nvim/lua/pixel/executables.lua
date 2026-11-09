local M = {}
function M.resolve(name, root)
  if root then
    for _, directory in ipairs({ '/.venv/bin/', '/venv/bin/', '/node_modules/.bin/' }) do
      local candidate = root .. directory .. name
      if vim.fn.executable(candidate) == 1 then return candidate end
    end
  end
  if vim.fn.executable(name) == 1 then return vim.fn.exepath(name) end
  for _, directory in ipairs({ '~/.local/bin/', '~/.cargo/bin/', '~/go/bin/' }) do
    local candidate = vim.fn.expand(directory .. name)
    if vim.fn.executable(candidate) == 1 then return candidate end
  end
end
return M
