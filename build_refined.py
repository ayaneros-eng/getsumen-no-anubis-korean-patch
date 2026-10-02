"""Reproducible in-place punctuation font fix for the exact Anubis v1.10.
Two-byte glyph + period becomes two-byte compound glyph + half-width space.
Record sizes and paragraph/branch addresses are preserved.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,sys,re
import argparse
parser=argparse.ArgumentParser(description='Anubis v1.10 punctuation fix; source ROMs remain unchanged.')
parser.add_argument('--base-rom',required=True,type=Path)
parser.add_argument('--japanese-rom',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
source=args.base_rom
if args.output.exists():raise SystemExit('Output already exists')
if args.output.resolve() in (args.base_rom.resolve(),args.japanese_rom.resolve()):raise SystemExit('Output must differ from source')
rom=bytearray(source.read_bytes())
base_sha='8eecc2c6ca13ca3183cba819e048ca016b1a5aae25928f19ddf63ceb5a467ac2'
assert hashlib.sha256(rom).hexdigest()==base_sha,'Unexpected source ROM'
lo,hi=0x300000,0x372000
# The expanded area contains custom-encoded translated text. Validate byte
# boundaries so a glyph's low byte is never mistaken for a new lead byte.
used=set();matches=[];orphans=[];duplicate_period_offsets=[];i=lo;x=0
while i<hi:
    if 0xE9<=rom[i]<=0xEE and i+1<hi:
        code=(rom[i]<<8)|rom[i+1];used.add(code)
        if x+16>240:x=0
        x+=16
        if i+2<hi and rom[i+2]==2:
            matches.append((i,code))
            j=i+3
            while j<hi and rom[j]==0:j+=1
            if j>i+3 and j+1<hi and rom[j]==2 and rom[j+1] in (0xF7,0xFE):
                duplicate_period_offsets.append(j)
            if x==240:orphans.append((i,code))
        i+=2
    else:
        v=rom[i]
        if v in (0xF7,0xFE):x=0
        elif v<0xE9:
            if x+8>240:x=0
            x+=8
        i+=1
all_types=Counter(c for _,c in matches)
# Only allocate syllables that can end exactly at the normal 240px boundary.
# Replace those syllable/period pairs everywhere to cover the same syllables
# in branches with runtime-expanded names. Record lengths remain unchanged.
needed={c for _,c in orphans}
matches=[(at,c) for at,c in matches if c in needed]
types=Counter(c for _,c in matches)
# Preserve every glyph referenced by legacy text/UI as well as new text.
original=args.japanese_rom.read_bytes()
assert hashlib.sha256(original).hexdigest()=='4187f17b8095d510bc207a7ba36aeb011556be6885a42dc48704af3128e5166c','Unexpected Japanese ROM'
legacy_bytes=bytes(rom[:0x98000])+original[:0x98000]+bytes(rom[0x380000:0x380100])
free=[c for c in range(0xEEFF,0xE8FF,-1) if c not in used and c.to_bytes(2,'big') not in legacy_bytes]
assert len(free)>=len(types),f'Not enough unreferenced font slots: {len(free)} / {len(types)}'
def decode(code):
    off=0xA0000+(code-0xE900)*64
    g=[]
    for y in range(16):
        row=[]
        for x in range(16):
            at=off+(x//8*2+y//8)*16+(y%8)*2
            row.append(((rom[at]>>(7-x%8))&1)+(((rom[at+1]>>(7-x%8))&1)*2))
        g.append(row)
    return g
def encode(g):
    b=bytearray(64)
    for y in range(16):
        for x in range(16):
            at=(x//8*2+y//8)*16+(y%8)*2
            b[at]|=(g[y][x]&1)<<(7-x%8)
            b[at+1]|=((g[y][x]>>1)&1)<<(7-x%8)
    return b
mapping={};font_entries=[]
for old,new in zip(sorted(types),free):
    g=decode(old)
    # Add a small Korean full stop inside the empty right-hand margin.
    assert all(g[y][x]==0 for x in (14,15) for y in (12,13)), f'No punctuation margin in {old:04X}'
    for y in (12,13):
        for x in (14,15):g[y][x]=1
    off=0xA0000+(new-0xE900)*64
    assert 0xA0000<=off<0xB8000
    rom[off:off+64]=encode(g);mapping[old]=new
    font_entries.append({'source_code':f'{old:04X}','compound_code':f'{new:04X}','font_offset':hex(off),'uses':types[old]})
for at,old in matches:
    assert rom[at:at+3]==old.to_bytes(2,'big')+b'\x02'
    rom[at:at+3]=mapping[old].to_bytes(2,'big')+b'\x00'
assert len(duplicate_period_offsets)==44
# Native screenshots confirmed duplicated stops after page/wait and music
# controls. F8 consumes one operand, F9 two (81:C915 / 81:C937).
# Match complete source byte strings; never modify control operands.
control_duplicates=[]
source_bytes=source.read_bytes()
for pattern,expected in ((bytes.fromhex('e91002fef80ff80f02f7'),1),
                         (bytes.fromhex('e91002f901010002f7'),2),
                         (bytes.fromhex('e92aeb63e9c804fe02f7'),1)):
    found=[];start=lo
    while (at:=source_bytes.find(pattern,start,hi))!=-1:
        found.append(at+len(pattern)-2);start=at+len(pattern)
    assert len(found)==expected
    control_duplicates.extend(found)
duplicate_period_offsets.extend(control_duplicates)
assert len(set(duplicate_period_offsets))==len(duplicate_period_offsets)==48
for at in duplicate_period_offsets:
    assert rom[at]==2
    rom[at]=0  # Remove the extra separated terminal period; keep record size.
# Align malformed choice-introduction punctuation with the native comma form.
prompt_offsets=[]
for m in re.finditer(bytes.fromhex('e93de91c')+b'\x00*\x02\xf7\xff',source_bytes[lo:hi]):
    at=lo+m.end()-3
    assert rom[at]==2
    rom[at]=1
    prompt_offsets.append(at)
assert len(prompt_offsets)==14
rom[0x7FDC:0x7FE0]=b'\xff\xff\x00\x00'
checksum=sum(rom)&0xFFFF
rom[0x7FDC:0x7FDE]=(checksum^0xFFFF).to_bytes(2,'little')
rom[0x7FDE:0x7FE0]=checksum.to_bytes(2,'little')
assert sum(rom)&0xFFFF==checksum
target=args.output
assert hashlib.sha256(rom).hexdigest()=='fdd3e6804d640041af4f654b58a3ee1038e2fe4c8a8e6c73bb45374e77a7d5a5','Unexpected build output'
target.write_bytes(rom)
manifest={'base_sha256':base_sha,'fixed_sha256':hashlib.sha256(rom).hexdigest(),'size':len(rom),'checksum':hex(checksum),'replaced_sequences':len(matches),'potential_orphan_sequences':len(orphans),'all_period_syllables':len(all_types),'compound_glyphs':font_entries,'unused_slots_before':len(free),'text_offsets_unchanged':True,'branch_offsets_unchanged':True,'source_text_wording_unchanged':True,'period_graphic':'2x2 Korean full stop in existing glyph margin; original period advance replaced by blank half-width cell','runtime_verified':False,'choice_prompt_periods_to_commas':len(prompt_offsets),'choice_prompt_offsets':[hex(v) for v in prompt_offsets],'duplicate_terminal_periods_removed':len(duplicate_period_offsets),'duplicate_period_offsets':[hex(v) for v in duplicate_period_offsets]}
target.with_suffix('.build.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='compound_glyphs'},ensure_ascii=False))
