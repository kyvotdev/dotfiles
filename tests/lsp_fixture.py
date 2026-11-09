#!/usr/bin/env python3
"""A deterministic, local LSP test peer; never used by the editor configuration."""
import sys,json
reader=sys.stdin.buffer;writer=sys.stdout.buffer

def send(message):
    data=json.dumps(message).encode();writer.write(f'Content-Length: {len(data)}\r\n\r\n'.encode()+data);writer.flush()
while True:
    size=0
    while True:
        line=reader.readline()
        if not line:sys.exit(0)
        if line in (b'\r\n',b'\n'):break
        if line.lower().startswith(b'content-length:'):size=int(line.split(b':',1)[1])
    msg=json.loads(reader.read(size));method=msg.get('method')
    if method=='exit':break
    if method=='textDocument/didOpen':
        send({'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':msg['params']['textDocument']['uri'],'diagnostics':[{'range':{'start':{'line':0,'character':0},'end':{'line':0,'character':1}},'severity':2,'source':'PixelTest','message':'fixture diagnostic'}]}})
    if 'id' not in msg:continue
    result=None
    if method=='initialize':result={'capabilities':{'textDocumentSync':1,'completionProvider':{'triggerCharacters':['.']},'hoverProvider':True},'serverInfo':{'name':'PixelFixture'}}
    elif method=='textDocument/completion':result={'isIncomplete':False,'items':[{'label':'print','kind':3,'insertText':'print(${1:value})','insertTextFormat':2}]}
    elif method=='textDocument/hover':result={'contents':{'kind':'plaintext','value':'fixture documentation'}}
    send({'jsonrpc':'2.0','id':msg['id'],'result':result})
