"""Quarantine historical sec_path=error records, keeping the original metadata for review.

Dry run by default. This command never collects data or writes private runtime state.
"""
import argparse
import csv
import io
import json
import os
import re
from pathlib import Path

from build_dashboard import atomic_text, build_dashboard


def repair_snapshots(base, apply=False):
    base = Path(base)
    pending = []
    updates = {}
    counts = {}
    for file in sorted((base / '厂商').glob('*/repos.json')):
        records = json.loads(file.read_text(encoding='utf-8'))
        rejected = [r for r in records if r.get('sec_path') == 'error']
        valid = [r for r in records if r.get('sec_path') != 'error']
        pending.extend(rejected)
        for record in valid:
            vendor = record.get('vendor') or record['org']
            counts[vendor] = counts.get(vendor, 0) + 1
        if rejected:
            updates[file] = json.dumps(valid,ensure_ascii=False,indent=1)
            markdown = file.with_name('清单.md')
            if markdown.exists():
                names = {r['full_name'] for r in rejected}
                lines = markdown.read_text(encoding='utf-8').splitlines()
                lines = [line for line in lines if not (line.startswith('| ') and line.split('|')[1].strip() in names)]
                content = '\n'.join(lines) + '\n'
                updates[markdown] = re.sub(r'(收录仓库数：\*\*)\d+(\*\*)',lambda m:m[1]+str(len(valid))+m[2],content)
    if not pending:
        return 0
    stats_file = base / '索引/统计.json'
    stats = json.loads(stats_file.read_text(encoding='utf-8'))
    stats['totals']['sec_repos'] = sum(counts.values())
    for vendor in stats['vendors']:
        vendor['sec_repos'] = counts.get(vendor['vendor'],0)
    updates[stats_file] = json.dumps(stats,ensure_ascii=False,indent=1)
    csv_file = base / '索引/总表.csv'
    if csv_file.exists():
        with csv_file.open(encoding='utf-8-sig',newline='') as file:
            rows = list(csv.reader(file))
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer,lineterminator='\n')
        writer.writerows(row for row in rows if len(row) < 8 or row[7] != 'error')
        updates[csv_file] = '\ufeff'+buffer.getvalue()
    quarantine = base / '索引/retry-candidates.json'
    previous = json.loads(quarantine.read_text(encoding='utf-8')) if quarantine.exists() else []
    archived = {r['full_name']: r for r in previous + pending}
    updates[quarantine] = json.dumps(sorted(archived.values(),key=lambda r:r['full_name']),ensure_ascii=False,indent=1)+'\n'
    if apply:
        for path, content in updates.items():
            atomic_text(path,content)
        build_dashboard(base)
    return len(pending)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(os.environ.get('SECMD_BASE') or Path(__file__).resolve().parents[1]))
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    print('%s: %s network-error records' % ('Quarantined' if args.apply else 'Dry run',repair_snapshots(args.base,args.apply)))
