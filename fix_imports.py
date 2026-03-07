import os

def fix_imports():
    targets = ['common', 'cognitive', 'trading', 'evolution']
    base_dir = '/home/noogh/projects/noogh_unified_system/src/proto_generated'
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith('.py') or f.endswith('.pyi'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                changed = False
                for t in targets:
                    new_val_from = f'from proto_generated.{t} import'
                    old_val_from = f'from {t} import'
                    if old_val_from in content:
                        content = content.replace(old_val_from, new_val_from)
                        changed = True
                        
                    old_val_imp = f'import {t}_pb2'
                    new_val_imp = f'from proto_generated import {t}_pb2'
                    if old_val_imp in content:
                        content = content.replace(old_val_imp, new_val_imp)
                        changed = True

                if changed:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(content)

fix_imports()
