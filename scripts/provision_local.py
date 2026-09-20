"""Create only the named M0 V2 container and new development/test databases.

Credentials stay in ignored .local files. No V1 connection is made.
Refuses existing resources to avoid accidental reinitialization.
"""
import json, pathlib, secrets, subprocess, time, uuid
import psycopg
from psycopg import sql

ROOT=pathlib.Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local'
IMAGE='postgres@sha256:dfbbb0ad8cab91d41e99123664e37a9b25d0413426d4fb3154e4d668e5d35246'
NAME='efrco-v2-postgres-20260919'
VOLUME='efrco-v2-data-20260919'

def main():
    LOCAL.mkdir(exist_ok=True)
    if (LOCAL/'profiles.json').exists(): raise RuntimeError('Local profiles already exist; refusing reprovision')
    for kind,name in [('container',NAME),('volume',VOLUME)]:
        if subprocess.run(['docker',kind,'inspect',name],capture_output=True).returncode==0:
            raise RuntimeError('Resource exists; refusing reprovision: '+name)
    admin=secrets.token_urlsafe(36)
    (LOCAL/'postgres.env').write_text(f'POSTGRES_USER=efrco_admin\nPOSTGRES_PASSWORD={admin}\nPOSTGRES_DB=postgres\n',encoding='utf-8')
    subprocess.run(['docker','volume','create','--label','codex.project=efrco-v2',VOLUME],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['docker','run','-d','--name',NAME,'--label','codex.project=efrco-v2',
                    '--restart','unless-stopped','-p','127.0.0.1:56432:5432','--env-file',str(LOCAL/'postgres.env'),
                    '--mount',f'type=volume,source={VOLUME},target=/var/lib/postgresql/data',IMAGE],check=True,stdout=subprocess.DEVNULL)
    for _ in range(30):
        try:
            conn=psycopg.connect(host='127.0.0.1',port=56432,dbname='postgres',user='efrco_admin',password=admin,connect_timeout=2,autocommit=True)
            break
        except psycopg.OperationalError: time.sleep(1)
    else: raise RuntimeError('V2 database readiness failed')
    profiles={}
    with conn:
        for environment,suffix in [('development','dev'),('test','test')]:
            db=f'efrco_v2_{suffix}'; runtime=f'efrco_{suffix}_runtime'; migration=f'efrco_{suffix}_migrator'
            rp,mp=secrets.token_urlsafe(36),secrets.token_urlsafe(36)
            identity=str(uuid.uuid4())
            for role,password in [(runtime,rp),(migration,mp)]:
                conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS').format(sql.Identifier(role),sql.Literal(password)))
            conn.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(db),sql.Identifier(migration)))
            conn.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(db)))
            conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(db),sql.Identifier(runtime)))
            conn.execute(sql.SQL('COMMENT ON DATABASE {} IS {}').format(sql.Identifier(db),sql.Literal(f'efrco-v2:{environment}:{identity}')))
            with psycopg.connect(host='127.0.0.1',port=56432,dbname=db,user=migration,password=mp,autocommit=True) as setup:
                setup.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
                setup.execute('CREATE SCHEMA resilience_v2')
                setup.execute(sql.SQL('GRANT USAGE ON SCHEMA resilience_v2 TO {}').format(sql.Identifier(runtime)))
                setup.execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA resilience_v2 GRANT SELECT ON TABLES TO {}').format(sql.Identifier(runtime)))
            profiles[environment]=dict(environment=environment,host='127.0.0.1',port=56432,dbname=db,instance_id=identity,
                                        runtime_user=runtime,runtime_password=rp,migration_user=migration,migration_password=mp)
    (LOCAL/'profiles.json').write_text(json.dumps(profiles,indent=2),encoding='utf-8')
    print(json.dumps({'status':'provisioned','container':NAME,'volume':VOLUME,'databases':[p['dbname'] for p in profiles.values()],'bind':'127.0.0.1:56432','image':IMAGE}))

if __name__=='__main__': main()
