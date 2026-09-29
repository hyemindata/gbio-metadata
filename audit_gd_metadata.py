import json, glob, os, re, filecmp
import OpenEXR, Imath

ROOT="/raid/hyemin/Projects/gbio-metadata"
GD=os.path.join(ROOT,"gd_metadata")
EXPECT_KEYS=[str(i) for i in range(0,1441,96)]   # 0,96,...,1440  (16)

# expected dispositions from the reports
EXP_COPIED={ "sl01":"F05","sl03":"O03","sl04":"R03","sl06":"B04","sl07":"F04","sl08":"B03",
 "dk02":"F01","dk03":"F02","dk04":"B01","dk05":"R01","dk06":"F03","dk07":"B02","dk08":"O01",
 "dm02":"F03","dm03":"O03","dm05":"B04","dm07":"R03","dm12":"B01"}
EXP_GEN={"sl02","sl05","sl09","dk01","dk09","dm01","dm04","dm06","dm08","dm09","dm10","dm11","dm13"}
EXP_15of16={"dk04","dm12"}   # California-fuchsia curated edit

# load references
refs={}
for dj in glob.glob(ROOT+"/reference/03_DataPigmentation/*/*/*-DATA-*.json"):
    sid=re.search(r"-SCE-([A-Z]\d+)-",os.path.basename(dj)).group(1)
    d=json.load(open(dj))
    refs[sid]={"json":dj,"exr":dj[:-5]+".exr",
               "prompts":[d[k]["text"] for k in sorted(d,key=int)]}

def exr_info(p):
    f=OpenEXR.InputFile(p); h=f.header()
    dw=h["dataWindow"]; w=dw.max.x-dw.min.x+1; hh=dw.max.y-dw.min.y+1
    ch=tuple(sorted(h["channels"].keys())); f.close()
    return w,hh,ch

problems=[]
rows=[]
folders=sorted(glob.glob(GD+"/*/"))
print(f"folders found: {len(folders)}\n")
exr_dims=set()
for g in folders:
    name=os.path.basename(g.rstrip("/"))
    sid=re.search(r"_(sl|dk|dm)\d+",name).group(0).lstrip("_")
    jp=os.path.join(g,name+"_DATA.json"); xp=os.path.join(g,name+"_DATA.exr")
    files=sorted(os.path.basename(x) for x in glob.glob(g+"*"))
    # file presence + naming
    if not os.path.exists(jp): problems.append(f"{name}: missing {name}_DATA.json")
    if not os.path.exists(xp): problems.append(f"{name}: missing {name}_DATA.exr")
    extra=[f for f in files if f not in (name+"_DATA.json",name+"_DATA.exr")]
    if extra: problems.append(f"{name}: unexpected files {extra}")
    # json schema
    d=json.load(open(jp))
    keys=list(d.keys())
    if keys!=EXPECT_KEYS: problems.append(f"{name}: key set mismatch -> {keys}")
    toklens=set()
    for k,v in d.items():
        if set(v)!={"text","tokens_int","tokens_text"}:
            problems.append(f"{name}[{k}]: field set {set(v)}")
        if not v.get("text","").strip(): problems.append(f"{name}[{k}]: empty text")
        toklens.add(len(v["tokens_int"]))
    # classify
    ptext=[v["text"].strip() for v in d.values()]
    best,bn=None,-1
    for s,r in refs.items():
        n=sum(1 for a,b in zip(ptext,[t.strip() for t in r["prompts"]]) if a==b)
        if n>bn: bn,best=n,s
    disp="copied" if bn>=15 else "generated"
    # cmp for copied
    cmpres=""
    if disp=="copied":
        jok=filecmp.cmp(jp,refs[best]["json"],shallow=False)
        xok=filecmp.cmp(xp,refs[best]["exr"],shallow=False)
        cmpres=f"json={'OK' if jok else 'DIFF'} exr={'OK' if xok else 'DIFF'}"
        if not jok and not (sid in EXP_15of16): problems.append(f"{name}: copied json NOT identical to {best}")
        if not xok: problems.append(f"{name}: copied exr NOT identical to {best}")
    # exr
    w,h,ch=exr_info(xp); exr_dims.add((w,h,ch))
    # cross-check expectations
    if sid in EXP_COPIED:
        if disp!="copied": problems.append(f"{name}: expected COPIED({EXP_COPIED[sid]}) but classified {disp}")
        elif best!=EXP_COPIED[sid]: problems.append(f"{name}: copied from {best}, expected {EXP_COPIED[sid]}")
    elif sid in EXP_GEN:
        if disp!="generated": problems.append(f"{name}: expected GENERATED but matched {best} {bn}/16")
    else:
        problems.append(f"{name}: shot id {sid} not in expected lists")
    rows.append((name,sid,disp,(best if disp=='copied' else '-'),f"{bn}/16",cmpres,f"{w}x{h}{ch}",sorted(toklens)))

w1=max(len(r[0]) for r in rows)
print(f"{'folder':{w1}}  shot disp      ref  match  cmp                 exr            toklen")
for r in rows:
    print(f"{r[0]:{w1}}  {r[1]:4} {r[2]:9} {r[3]:4} {r[4]:6} {r[5]:19} {r[6]:14} {r[7]}")

print("\n=== distinct exr (w,h,channels) ===")
for d in exr_dims: print("  ",d)
print(f"\n=== counts ===  copied={sum(1 for r in rows if r[2]=='copied')}  generated={sum(1 for r in rows if r[2]=='generated')}")
print(f"\n=== PROBLEMS ({len(problems)}) ===")
for p in problems: print("  !",p)
if not problems: print("  none")
