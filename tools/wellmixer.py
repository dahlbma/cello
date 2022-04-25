import math
import sys, cProfile, re, argparse, time
from timeit import timeit
import numpy as np
from numpy import random as rng
import networkx as nx
from tqdm import tqdm

def put_ok(G, w, id):
    ids = [sub for sub in w]#[sub[0] for sub in w]
    if all(id not in G[i] for i in ids) and (id not in ids):
        return True
    else:
        return False

def add_to_subs(subs, well):
    add = []
    for well_sub in well:
        index = -1
        if len(subs) > 0:
            for i in range(len(subs)):
                sub = subs[i]
                if sub[0] == well_sub:
                    index = i
        if index != -1:
            subs[index][1] = subs[index][1] + 1
        else: # re-add substance
            add.append([well_sub, 1])
    
    for s in add:
        subs = np.append(subs, np.empty(1, dtype=object))
        subs[-1] = s
    return subs


def mixer(inp=False, n=15000, m=5, k=5):
    threshold = 100
    if not inp:
        print(f"n: {n}\nm: {m}\nk: {k}")
    else:
        try:
            n = int(input("# of substances n: "))
            m = int(input("# of substances/well m: "))
            k = int(input("# of occurences/substance k: "))
        except:
            print("Please input an integer. Exitting")
            return
    t0 = time.time()
    subs = np.empty(n, dtype=object)
    for id in range(n):
        subs[id] = [id, k]#[id, f"{id}", k] # serial, id, occs left

    wells = []
    G = nx.Graph()
    G.add_nodes_from([sub[0] for sub in subs])
    t1 = time.time()
    pbar = tqdm(total=int((k/m)*n))
    subcount = 0
    spins = 0
    th_hit = 0
    reshuffles = 0
    while subs.size > 0:
        w = []
        del_list = []
        loops = 0
        for m_i in range(min(m, len(subs))):
            subcount += 1
            found = False # get sub
            while not found:
                spins += 1
                if (loops > threshold):
                    print(f"hit threshold, subs left: {subs.size}")
                    th_hit += 1
                    found = True
                    continue
                if subs.size == 0:
                    found = True
                    continue
                index = rng.choice(np.arange(subs.size)) # choose index
                loops += 1
                s = subs[index] # get triple
                id = s[0]
                num = s[1]
                if put_ok(G, w, s[0]) and (s[1] > 0): # check if chosen tup has no edges to subs already "in well"
                    # also check if it should occur again
                    w.append((s[0])) # append id and desc in a tuple to w
                    num = num - 1 # decrement
                    subs[index][1] = num # put value
                    if num == 0: # should be deleted
                        del_list.append(index)
                    found = True
            loops = 0
        

        wells.append(w) # commit well
        for i in range(len(w) - 1):
            for j in range(i + 1, len(w)):
                G.add_edge(w[i], w[j])
        
        subs = np.delete(subs, del_list)

        if len(wells) > int(math.ceil((k/m)*n)) or \
            (len(wells) > k and (len(wells[-1]) < m and len(wells[-2]) < m)):
            reshuffles += 1
            print(f"reshuffle #: {reshuffles}")
            extra = len(wells) - int(math.ceil((k/m)*n))
            # redo extra + m*reshuffles finished wells
            put_back = wells[-(extra + (m*reshuffles)):]
            wells = wells[:-(extra + (m*reshuffles))]
            for well in put_back:
                for i in range(len(well) - 1):
                    for j in range(i + 1, len(well)):
                        G.remove_edge(well[i], well[j])
                subs = add_to_subs(subs, well)
            
            
        pbar.update()
    pbar.close()
    t2 = time.time()
    
    p1 = t1 - t0
    p2 = t2 - t1
    tott = t2 - t0

    print(f"# of wells generated: {len(wells)}") 
    #p = len(wells) if (len(wells) < 100) else min(len(wells), 10)
    #print(f"last {p} wells:")
    #for w in wells[-p:]:
    #    print(w)

    print(f"setup time: {p1:.4f}s\nloop time: {p2:.4f}s\ntotal time: {tott:.4f}s")
    hitrate = int((k/m)*n*m)/spins
    print(f"iterations={subcount}, spins={spins}, hitrate={hitrate:.4%}")
    print(f"avg. spins per well: {spins/len(wells)}")
    print(f"threshhold hit # times: {th_hit}\n# of reshuffles: {reshuffles}")
    stats = {'dims':{n, m, k}, 'time':p2, 'ef':hitrate}
    return wells, stats

n = 15000
m = 5
k = 5

parser = argparse.ArgumentParser()
parser.add_argument('-p', action="store_true", dest='p', default=False)
parser.add_argument('-i', action="store_true", dest='i', default=False)
parser.add_argument('-s', action="store_true", dest='s', default=False)
parser.add_argument('-c', action="store", dest="c", type=int, default=1)
parser.add_argument('-n', action="store", dest="n", type=int, default=n)
parser.add_argument('-m', action="store", dest="m", type=int, default=m)
parser.add_argument('-k', action="store", dest="k", type=int, default=k)

res = parser.parse_args()
if res.p:
    print("Run with profiler\n")
    for i in range(res.c):
        cProfile.run(f'mixer(inp={res.i})')
else:
    print("Run without profiler:\n")
    data = []
    for i in range(res.c):
        wells, stats = mixer(inp=res.i, n=res.n, m=res.m, k=res.k)
        data.append(stats)
    if res.s:
        # save data
        print(data)
