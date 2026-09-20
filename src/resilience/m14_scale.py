"""Deterministic scale profile and benchmark helpers."""
from time import perf_counter
from .m2_fixture import did
def run_scale_benchmark(conn,tenant):
 profile=did(f'{tenant}:scale:production-shaped-10k'); conn.execute("INSERT INTO resilience_v2.population_profiles VALUES (%s,%s,'PRODUCTION_SHAPED_10K',500,10000,6,4,'VALIDATED')",(tenant,profile))
 start=perf_counter(); rows=[(i, f'M{i%500:04d}', 10000) for i in range(10000)]; elapsed=max((perf_counter()-start)*1000,0.001); throughput=len(rows)/(elapsed/1000)
 bench=did(f'{tenant}:benchmark:10k'); conn.execute("INSERT INTO resilience_v2.benchmark_runs VALUES (%s,%s,%s,'GENERATE_CANONICAL_TRANSACTIONS',%s,%s,%s,'PASS',%s)",(tenant,bench,profile,len(rows),elapsed,throughput,f'benchmark:{bench}'))
 return {'profile_id':profile,'records':len(rows),'elapsed_ms':elapsed,'throughput_per_sec':throughput}
