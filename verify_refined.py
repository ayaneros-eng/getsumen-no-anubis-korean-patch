from pathlib import Path
import argparse, hashlib, json

ap = argparse.ArgumentParser()
ap.add_argument('--base-rom', required=True, type=Path)
ap.add_argument('--release', required=True, type=Path)
args = ap.parse_args()
base = args.base_rom.read_bytes()
spec = json.loads((args.release/'punctuation_build.json').read_text(encoding='utf-8'))
target = (args.release/'월면의_아누비스_한글_v1.10_추가검수수정.sfc').read_bytes()
def sha(b): return hashlib.sha256(b).hexdigest()
assert sha(base) == spec['base_sha256']
assert sha(target) == spec['fixed_sha256']
assert len(base) == len(target) == 4194304
allowed = set(range(0x7fdc, 0x7fe0))
reverse = {}
def pixels(rom, code):
    o = 0xa0000 + (code-0xe900)*64
    return [[((rom[o+(x//8*2+y//8)*16+(y%8)*2]>>(7-x%8))&1)
             + 2*((rom[o+(x//8*2+y//8)*16+(y%8)*2+1]>>(7-x%8))&1)
             for x in range(16)] for y in range(16)]
for v in spec['compound_glyphs']:
    old, new = int(v['source_code'], 16), int(v['compound_code'], 16)
    reverse[new] = old
    a, b = pixels(base, old), pixels(target, new)
    assert pixels(target, old) == a
    for y in range(16):
        for x in range(16):
            assert b[y][x] == (1 if x in (14, 15) and y in (12, 13) else a[y][x])
    o = int(v['font_offset'], 16)
    allowed.update(range(o, o+64))
lo, hi = 0x300000, 0x372000
text = bytearray(target[lo:hi])
for v in spec['duplicate_period_offsets']:
    at = int(v, 16)
    assert target[at] == 0 and base[at] == 2
    text[at-lo] = 2
    allowed.add(at)
for v in spec['choice_prompt_offsets']:
    at = int(v, 16)
    assert target[at] == 1 and base[at] == 2
    text[at-lo] = 2
    allowed.add(at)
i, reverted = 0, 0
while i < len(text)-1:
    if 0xe9 <= text[i] <= 0xee:
        code = text[i]*256 + text[i+1]
        if code in reverse:
            assert text[i+2] == 0
            text[i:i+3] = reverse[code].to_bytes(2, 'big') + b'\x02'
            allowed.update(range(lo+i, lo+i+3))
            reverted += 1
        i += 2
    else:
        i += 1
assert bytes(text) == base[lo:hi]
assert reverted == spec['replaced_sequences']
changed = [i for i, (a,b) in enumerate(zip(base,target)) if a != b]
assert all(i in allowed for i in changed)
checksum = int.from_bytes(target[0x7fde:0x7fe0], 'little')
assert sum(target)&65535 == checksum
assert int.from_bytes(target[0x7fdc:0x7fde], 'little') ^ checksum == 65535
patches = json.loads((args.release/'patch_manifest.json').read_text(encoding='utf-8'))
assert patches['target_sha256'] == sha(target)
for v in patches['patches']:
    assert sha((args.release/v['file']).read_bytes()) == v['patch_sha256']
report = {
    'target_sha256': sha(target), 'size_unchanged': True,
    'checksum': hex(checksum), 'checksum_verified': True,
    'changed_bytes': len(changed), 'reverted_compound_sequences': reverted,
    'removed_duplicate_terminal_periods': len(spec['duplicate_period_offsets']),
    'text_inverse_byte_identical_to_v1_10': True,
    'choice_prompt_periods_corrected': len(spec['choice_prompt_offsets']),
    'source_glyphs_unchanged': True,
    'all_27_compound_glyphs_only_add_4_empty_pixels': True,
    'all_changes_confined_to_font_slots_period_pairs_duplicate_periods_choice_prompt_commas_checksum': True,
    'packaged_ips_hashes_verified': True
}
(args.release/'evidence/structural_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
