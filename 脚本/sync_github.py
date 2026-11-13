"""Sync public snapshots only; never overwrite the destination's application code.

Use --dry-run to inspect, and --push to explicitly commit and publish.
The source and destination must be different directories.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path


def public_files(base):
    """Keep runtime state, credentials, caches and application code outside the manifest."""
    base = Path(base)
    for pattern in ('厂商/*/repos.json', '厂商/*/清单.md', '厂商/*/*/SECURITY.md',
                    '资产/vendors*.json', '资产/厂商映射-*.json',
                    '赏金APK/*.json', '赏金APK/*.md', '赏金APK/*.html',
                    '索引/统计.json', '索引/总表.csv'):
        yield from sorted(base.glob(pattern))


def sync_public_data(base, destination):
    base, destination = Path(base).resolve(), Path(destination).resolve()
    if base == destination or base in destination.parents or destination in base.parents:
        raise ValueError('Source and destination must be separate, non-nested directories')
    changed = 0
    for file in public_files(base):
        if not file.is_file() or file.is_symlink():
            continue
        relative = file.relative_to(base)
        if any(part.startswith('.') for part in relative.parts) or not file.resolve().is_relative_to(base):
            continue
        target = destination / relative
        if not target.resolve().is_relative_to(destination):
            raise ValueError('Destination symlink escapes repository: %s' % relative)
        if target.is_file() and filecmp.cmp(file, target, shallow=False):
            continue
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.with_name(target.name+'.tmp')
        shutil.copyfile(file,temporary)
        temporary.replace(target)
        changed += 1
    return changed


def git(destination, *args):
    result = subprocess.run(['git',*args],cwd=destination,capture_output=True,text=True,
                            encoding='utf-8',errors='replace',timeout=180)
    if result.returncode:
        # Git errors can include credential-bearing remote URLs, so print only the operation.
        raise RuntimeError('git %s failed (exit %s); inspect the checkout locally' % (args[0],result.returncode))
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(os.environ.get('SECMD_BASE') or Path(__file__).resolve().parents[1]))
    parser.add_argument('--repo',type=Path,default=Path(os.environ.get('SECMD_REPO') or Path.home() / 'Desktop/security-md-collect'))
    parser.add_argument('--branch',default='main')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--push',action='store_true')
    args = parser.parse_args()
    base, destination = args.base.resolve(), args.repo.resolve()
    if not (base / '索引/统计.json').is_file() or not (base / '厂商').is_dir():
        parser.error('Source is missing public snapshots')
    if base == destination or base in destination.parents or destination in base.parents:
        parser.error('Source and destination must be separate, non-nested directories')
    if not (destination / '.git').exists():
        parser.error('Destination must be an existing Git checkout')
    if args.dry_run:
        print('DRY RUN: %s public files; no writes, commit or push' % sum(1 for _ in public_files(base)))
        return
    if git(destination,'branch','--show-current') != args.branch:
        parser.error('Destination is not on the requested branch')
    if git(destination,'status','--porcelain'):
        parser.error('Destination has local changes; commit or resolve them first')
    if args.push:
        git(destination,'pull','--ff-only','origin',args.branch)
    builder = destination / '脚本/build_dashboard.py'
    if not builder.is_file():
        parser.error('Update the destination checkout to the new dashboard version first')
    changed = sync_public_data(base,destination)
    subprocess.run([sys.executable,str(builder),'--base',str(destination)],check=True,timeout=120)
    if args.push:
        git(destination,'add','--','厂商','赏金APK','资产','索引/统计.json','索引/总表.csv','索引/dashboard.json','index.html')
        if git(destination,'diff','--cached','--name-only'):
            git(destination,'commit','-m','data: refresh public policy snapshots')
        # Retry previously unpushed data commits as well; never force-push.
        git(destination,'push','origin',args.branch)
        print('PUSHED: public snapshots (%s changed files)' % changed)
    else:
        print('SYNCED: %s changed files; review git diff before committing' % changed)


if __name__ == '__main__':
    main()
