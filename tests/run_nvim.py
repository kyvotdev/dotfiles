#!/usr/bin/env python3
"""Run editor tests after VimEnter, failing the process on any Lua assertion."""
import os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(test,env):
    name=str(ROOT/'tests'/test)
    # The filename is controlled by this test runner, never project text.
    import json
    command='vim.api.nvim_create_autocmd("VimEnter",{once=true,callback=function()vim.schedule(function()local ok,err=pcall(dofile,'+json.dumps(name)+');if not ok then print(err);vim.cmd("cquit 1") else vim.cmd("qa!") end end)end})'
    result=subprocess.run(['nvim','--headless','+lua '+command],env={**os.environ,**env},text=True,capture_output=True,timeout=15)
    print((result.stdout+result.stderr).strip())
    if result.returncode:raise SystemExit(result.returncode)
with tempfile.TemporaryDirectory(prefix='pixel-editor-test-') as tmp:
    root=Path(tmp);(root/'pyproject.toml').touch();(root/'main.py').write_text('x = 1\n')
    run('nvim_smoke.lua',{})
    run('nvim_ide.lua',{'PIXEL_IDE_TEST_ROOT':tmp})
    run('nvim_explorer.lua',{'PIXEL_IDE_TEST_ROOT':tmp})
    (root/'.venv/bin').mkdir(parents=True)
    (root/'.venv/bin/pyright-langserver').symlink_to(ROOT/'tests/lsp_fixture.py')
    run('nvim_lsp.lua',{'PIXEL_LSP_TEST_ROOT':tmp})
