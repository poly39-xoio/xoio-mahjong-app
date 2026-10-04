#!/usr/bin/env python3
"""由 www/_template.html + www/puzzles.json 產生 www/index.html(注入題庫)"""
import os
tpl=open('www/_template.html',encoding='utf-8').read()
data=open('www/puzzles.json',encoding='utf-8').read().strip()
assert '__PUZZLES_JSON__' in tpl, 'template missing placeholder'
out=tpl.replace('__PUZZLES_JSON__', data)
open('www/index.html','w',encoding='utf-8').write(out)
print('built www/index.html', len(out), 'bytes')
