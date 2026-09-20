import hashlib, importlib.metadata as md, json, pathlib, platform, sys
root=pathlib.Path(__file__).resolve().parents[1]
packages=sorted([(d.metadata['Name'],d.version) for d in md.distributions() if d.metadata['Name'].lower()!='enterprise-financial-resilience'],key=lambda x:x[0].lower())
(root/'requirements.lock').write_text('\n'.join(f'{n}=={v}' for n,v in packages)+'\n',encoding='utf-8')
record={'python':platform.python_version(),'platform':platform.platform(),'postgres_image':'postgres@sha256:dfbbb0ad8cab91d41e99123664e37a9b25d0413426d4fb3154e4d668e5d35246','postgres_version':'15.19','packages':dict(packages),'requirements_sha256':hashlib.sha256((root/'requirements.lock').read_bytes()).hexdigest()}
(root/'runtime-lock.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'python':record['python'],'package_count':len(packages),'postgres':record['postgres_version']}))
