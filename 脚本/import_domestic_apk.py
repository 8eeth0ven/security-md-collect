"""Import reviewed domestic SRC Android evidence; unresolved products stay separate."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from build_apk_board import PACKAGE, safe_url, write


def import_rows(base, evidence_path, source_manifest=None):
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    confirmed, pending = [], []
    for raw in evidence:
        if raw.get('scope_status') != 'confirmed':
            pending.append(raw)
            continue
        scope = safe_url(raw.get('scope_url'))
        page = safe_url(raw.get('download_page'))
        apk = safe_url(raw.get('apk_direct'))
        if not scope or not (page or apk):
            raise ValueError('Confirmed Android rows need scope evidence and an official entry')
        package = raw.get('package') or ''
        if package and (not PACKAGE.fullmatch(package) or not safe_url(raw.get('package_source_url'))):
            raise ValueError('Package mappings require a valid ID and an evidence URL')
        confirmed.append({
            'handle':raw['src_name'], 'program':raw['vendor']+' · '+raw['src_name'], 'vendor':raw['vendor'],
            'program_url':scope,'target':raw['product'], 'package':package or None,
            'package_source':'scope包名' if package else None,
            'package_source_url':safe_url(raw.get('package_source_url')),
            'scope_source':scope,'scope_review_source':scope,'scope_status':'in_scope',
            'scope_observation':'observed','scope_observed_at':raw['observed_at'],
            'scope_evidence':raw['scope_evidence'],'bounty_type':raw.get('reward_status','unknown'),
            'reward_conditions':raw.get('reward_conditions',''), 'reward_url':safe_url(raw.get('reward_url')),
            'download_page':page,'apk_direct':apk,'download_state':raw.get('download_state','unverified'),
            'download_notes':str(raw.get('download_notes') or ''),
            'download_metadata':raw.get('download_metadata'),
            'download_verified':False,
        })
    # A repeated import replaces exact vendor/product identities, rather than duplicating them.
    confirmed = list({(r['vendor'],r['target']):r for r in confirmed}.values())
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    out = base/'赏金APK'
    existing = json.loads((out/'src-backlog.json').read_text(encoding='utf-8')) if (out/'src-backlog.json').exists() else {}
    existing.update(observed_at=stamp,confirmed_android_targets=len(confirmed),pending_products=pending,
                    status='partial_android_inventory_with_separate_unresolved_products')
    write(out/'src_android.json',json.dumps(confirmed,ensure_ascii=False,indent=2)+'\n')
    write(out/'src-backlog.json',json.dumps(existing,ensure_ascii=False,indent=2)+'\n')
    write(out/'src-evidence.json',json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    previous = json.loads((out/'snapshot.json').read_text(encoding='utf-8')) if (out/'snapshot.json').exists() else {}
    previous.update(generated_at=stamp,domestic_sources_at=stamp)
    write(out/'snapshot.json',json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
    if source_manifest:
        manifest = json.loads(source_manifest.read_text(encoding='utf-8'))
        write(out/'src-sources.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return {'confirmed':len(confirmed),'pending':len(pending),'vendors':sorted({r['vendor'] for r in confirmed})}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--source-manifest',type=Path)
    args = parser.parse_args()
    print(json.dumps(import_rows(args.base,args.evidence,args.source_manifest),ensure_ascii=False))
