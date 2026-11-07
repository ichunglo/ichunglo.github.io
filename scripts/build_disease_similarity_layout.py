"""Build a reproducible network of disease terms sharing drug records."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from build_unified_historical_dataset import ROOT

INPUT=ROOT/'data/generated/audited-landscape-analysis.json'
OUTPUT=ROOT/'data/generated/disease-similarity-layout.json'
MAX_POINTS=120
MIN_SHARED=3
MIN_JACCARD=.03


def main():
    raw=INPUT.read_bytes();data=json.loads(raw)
    linked={r['d'] for r in data['links']}
    terms=defaultdict(set)
    for row in data['diseases']:
        if row['d'] in linked:terms[(row['group'],row['term'])].add(row['d'])
    ordered=sorted(terms,key=lambda key:(-len(terms[key]),key[0],key[1]))[:MAX_POINTS]
    drugs=sorted(set().union(*(terms[key] for key in ordered)))
    index={drug:i for i,drug in enumerate(drugs)}
    binary=np.zeros((len(ordered),len(drugs)),dtype=np.int32)
    for i,key in enumerate(ordered):
        for drug in terms[key]:binary[i,index[drug]]=1
    intersections=binary@binary.T
    sizes=np.diag(intersections).copy()
    unions=sizes[:,None]+sizes[None,:]-intersections
    similarity=np.divide(intersections,unions,out=np.zeros(unions.shape,dtype=float),where=unions!=0)
    original_edges=[(i,j) for i in range(len(ordered)) for j in range(i)
                    if intersections[i,j]>=MIN_SHARED and similarity[i,j]>=MIN_JACCARD]
    included=sorted({node for edge in original_edges for node in edge})
    local={original:i for i,original in enumerate(included)}
    edges=[{'a':local[i],'b':local[j],'shared_drugs':int(intersections[i,j]),
            'jaccard':round(float(similarity[i,j]),6)} for i,j in original_edges]
    # Fixed-seed force layout: edges encode evidence; 2D positions only aid
    # readability and are not an estimate of biological or semantic distance.
    n=len(included);rng=np.random.default_rng(42);coords=rng.uniform(-.5,.5,(n,2));k=np.sqrt(4/n)
    for step in range(400):
        delta=coords[:,None,:]-coords[None,:,:]
        dist=np.maximum(np.linalg.norm(delta,axis=2),.001)
        force=np.sum(delta*(k*k/dist**2)[:,:,None],axis=1)
        for edge in edges:
            a,b=edge['a'],edge['b'];vec=coords[a]-coords[b];length=max(float(np.linalg.norm(vec)),.001)
            attraction=vec*(length/k)*(.35+min(edge['jaccard'],.25)*2)
            force[a]-=attraction;force[b]+=attraction
        force-=coords*.04
        norm=np.maximum(np.linalg.norm(force,axis=1),.001);temperature=.09*(1-step/400)+.002
        coords+=force/norm[:,None]*np.minimum(norm,temperature)[:,None]
    adjacency=[set() for _ in range(n)]
    for edge in edges:
        adjacency[edge['a']].add(edge['b']);adjacency[edge['b']].add(edge['a'])
    visited=set();components=[]
    for start in range(n):
        if start in visited:continue
        stack=[start];visited.add(start);component=[]
        while stack:
            item=stack.pop();component.append(item)
            for other in sorted(adjacency[item]-visited):visited.add(other);stack.append(other)
        components.append(sorted(component))
    components.sort(key=lambda c:(-len(c),c[0]))
    packed=np.zeros_like(coords)
    for ci,component in enumerate(components):
        pos=coords[component];span=np.maximum(np.ptp(pos,axis=0),.001)
        normalized=2*(pos-pos.min(axis=0))/span-1
        if ci==0:packed[component]=normalized*np.array([.64,.91])+np.array([-.32,0])
        else:
            slot=ci-1;cx=.46+(slot%2)*.37;cy=.76-(slot//2)*.5
            packed[component]=normalized*np.array([.13,.15])+np.array([cx,cy])
    coords=packed
    points=[{'group':ordered[i][0],'term':ordered[i][1],'x':round(float(coords[local[i],0]),8),
             'y':round(float(coords[local[i],1]),8),'broad_drug_count':int(sizes[i])} for i in included]
    result={'method':'Force-directed network of disease terms sharing drug records',
      'input_sha256':hashlib.sha256(raw).hexdigest(),'points':points,'edges':edges,
      'min_shared_drugs':MIN_SHARED,'min_jaccard':MIN_JACCARD,
      'selection':'Connected terms among the 120 most frequently recorded disease term/group pairs in the broad source view',
      'limits':'Edges mean shared drug records, not shared clinical trials, validated indications or biological distance.'}
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    print(json.dumps({'terms':len(points),'edges':len(edges),'distinct_drugs':len(drugs),'output':str(OUTPUT)},indent=2))


if __name__=='__main__':main()
