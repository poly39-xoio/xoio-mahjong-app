#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""數獨題庫生成器:產生 100 題(唯一解),依難度由易至難排序 → www/puzzles.json"""
import random, json, os

OUT = '/root/.openclaw/workspace/xoio-sudoku-app/www/puzzles.json'

def ok(g, r, c, v):
    for i in range(9):
        if g[r][i] == v or g[i][c] == v:
            return False
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if g[i][j] == v:
                return False
    return True

def full_grid(rng):
    g = [[0] * 9 for _ in range(9)]
    def fill(pos=0):
        if pos == 81:
            return True
        r, c = divmod(pos, 9)
        vals = list(range(1, 10)); rng.shuffle(vals)
        for v in vals:
            if ok(g, r, c, v):
                g[r][c] = v
                if fill(pos + 1):
                    return True
                g[r][c] = 0
        return False
    fill()
    return g

def count_solutions(g, limit=2):
    def rec():
        best = None; bestc = None
        for r in range(9):
            for c in range(9):
                if g[r][c] == 0:
                    cand = [v for v in range(1, 10) if ok(g, r, c, v)]
                    if bestc is None or len(cand) < len(bestc):
                        best = (r, c); bestc = cand
                        if len(cand) == 0:
                            return 0
                        if len(cand) == 1:
                            break
            else:
                continue
            break
        if best is None:
            return 1
        r, c = best; n = 0
        for v in bestc:
            g[r][c] = v
            n += rec()
            g[r][c] = 0
            if n >= limit:
                return n
        return n
    return rec()

def make_puzzle(rng, target_clues):
    sol = full_grid(rng)
    pz = [row[:] for row in sol]
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)
    clues = 81
    for (r, c) in cells:
        if clues <= target_clues:
            break
        v = pz[r][c]; pz[r][c] = 0
        if count_solutions(pz, 2) != 1:
            pz[r][c] = v
        else:
            clues -= 1
    return pz, sol, clues

def grade(pz):
    g = [row[:] for row in pz]
    def cands(g, r, c):
        used = set(g[r]) | set(g[i][c] for i in range(9)) | set(
            g[i][j] for i in range(3 * (r // 3), 3 * (r // 3) + 3)
            for j in range(3 * (c // 3), 3 * (c // 3) + 3))
        return [v for v in range(1, 10) if v not in used]
    naked = hidden = 0
    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if g[r][c] == 0:
                    cd = cands(g, r, c)
                    if len(cd) == 1:
                        g[r][c] = cd[0]; naked += 1; changed = True
        for i in range(9):
            for v in range(1, 10):
                pos = [c for c in range(9) if g[i][c] == 0 and v in cands(g, i, c)]
                if len(pos) == 1:
                    g[i][pos[0]] = v; hidden += 1; changed = True
                pos = [r for r in range(9) if g[r][i] == 0 and v in cands(g, r, i)]
                if len(pos) == 1:
                    g[pos[0]][i] = v; hidden += 1; changed = True
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                for v in range(1, 10):
                    pos = [(r, c) for r in range(br, br + 3) for c in range(bc, bc + 3)
                           if g[r][c] == 0 and v in cands(g, r, c)]
                    if len(pos) == 1:
                        g[pos[0][0]][pos[0][1]] = v; hidden += 1; changed = True
    solved = all(g[r][c] != 0 for r in range(9) for c in range(9))
    return {'solved': solved, 'naked': naked, 'hidden': hidden}

def label(clues, solved):
    if clues >= 38 and solved:
        return 'easy'
    if clues >= 32:
        return 'medium'
    if clues >= 27:
        return 'hard'
    return 'expert'

def main():
    from collections import Counter
    rng = random.Random(20261003)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    QUOTA = {'easy': 30, 'medium': 30, 'hard': 30, 'expert': 10}
    counts = Counter()
    out = []
    seen = set()
    tries = 0
    while len(out) < 100 and tries < 4000:
        tries += 1
        target = rng.choice([44, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22])
        pz, sol, clues = make_puzzle(rng, target)
        key = ''.join(str(pz[r][c]) for r in range(9) for c in range(9))
        if key in seen:
            continue
        seen.add(key)
        gr = grade(pz)
        diff = label(clues, gr['solved'])
        if counts[diff] >= QUOTA.get(diff, 0):
            continue
        counts[diff] += 1
        out.append({'p': pz, 's': sol, 'clues': clues, 'diff': diff,
                    'solved': gr['solved'], 'naked': gr['naked'], 'hidden': gr['hidden']})
        if len(out) % 10 == 0:
            print('...', len(out), flush=True)
    order = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3}
    out.sort(key=lambda x: (order[x['diff']], 0 if x['solved'] else 1, -x['clues']))
    for i, x in enumerate(out, start=1):
        x['n'] = i
    json.dump(out, open(OUT, 'w'), separators=(',', ':'))
    from collections import Counter
    print('generated', len(out), Counter(x['diff'] for x in out),
          'clues', min(x['clues'] for x in out), '-', max(x['clues'] for x in out))

if __name__ == '__main__':
    main()
