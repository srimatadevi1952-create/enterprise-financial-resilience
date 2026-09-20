"""Deterministic board pack generator."""
import json
from .m2_fixture import did,T0
def generate_board_pack(conn,tenant,branches):
 run=branches['intervention']; pack=did(f'{run}:board-pack:2026-09'); refs=json.dumps([f'run:{run}',f'stressed:{branches["stressed"]}',f'capital:{branches["stressed"]}',f'liquidity:{branches["stressed"]}'])
 conn.execute("INSERT INTO resilience_v2.board_pack_runs VALUES (%s,%s,%s,'EXECUTIVE_RESILIENCE','2026-09','RECOVERY',100,95,'REVIEW',%s)",(tenant,run,pack,T0))
 sections=[('executive_summary','Recovery achieved','Intervention restores modeled completion to 100%; stress without action remains at 90%.','INFO'),('financial_capacity','Capital and liquidity','Capital restores within the modeled horizon; minimum liquidity is tight but no shortfall is recorded.','WATCH'),('risk_exposure','Risk and corridor exposure','Merchant concentration, regulatory review, and corridor disruption remain the main monitored exposures.','HIGH'),('decision','Decision required','Approve a read-only production shadow run with no live financial actions.','HIGH')]
 for key,headline,content,severity in sections: conn.execute("INSERT INTO resilience_v2.board_pack_sections VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,pack,did(f'{pack}:section:{key}'),key,headline,content,severity,refs))
 actions=[('Approve read-only production shadow run','BOARD','NOW','PROPOSED'),('Review unresolved feed-quality incidents','OPERATIONS','NEXT','PROPOSED'),('Monitor corridor and regulatory exposure','RISK','MONITOR','PROPOSED')]
 for i,(text,owner,priority,status) in enumerate(actions): conn.execute("INSERT INTO resilience_v2.board_pack_actions VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,pack,did(f'{pack}:action:{i}'),text,owner,priority,status,refs))
 return {'pack_id':pack,'sections':4,'actions':3,'status':'REVIEW'}
