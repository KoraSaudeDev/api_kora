SELECT 
	me.cd_mvto_estoque
	, NULLIF(REGEXP_REPLACE(me.tp_mvto_estoque,'[''"!/:@;]', ''),'') as tp_mvto_estoque
	, me.cd_estoque
	, TO_CHAR(me.dt_mvto_estoque, 'YYYY-MM-DD hh24:mi:ss') as dt_mvto_estoque
	, TO_CHAR(me.hr_mvto_estoque, 'YYYY-MM-DD hh24:mi:ss') as hr_mvto_estoque
	, me.cd_atendimento
	, me.cd_unid_int
	, me.cd_setor
	, me.cd_produto_manipulado
	, me.cd_uni_pro
	, TO_CHAR(me.qt_produzida) as qt_produzida
	, TO_CHAR(me.dt_validade, 'YYYY-MM-DD hh24:mi:ss') as dt_validade
	, TO_CHAR(me.vl_adicional) as vl_adicional
	, TO_CHAR(me.vl_total) as vl_total
	, TO_CHAR(me.qt_perda) as qt_perda
	, me.cd_prestador
	, me.cd_estoque_destino
	, NULLIF(REGEXP_REPLACE(me.tp_venda,'[''"!/:@;]', ''),'') as tp_venda
	, me.cd_mot_dev
	, me.cd_custo_medio_mestre
	, me.cd_custo_medio
	, me.cd_mot_bai
	, NULLIF(REGEXP_REPLACE(me.nr_documento,'[''"!/:@;]', ''),'') as nr_documento
	, me.cd_solsai_pro
	, me.cd_ent_pro
	, NULLIF(REGEXP_REPLACE(me.sn_consolidada,'[''"!/:@;]', ''),'') as sn_consolidada
	, TO_CHAR(me.dt_prevista_recebimento, 'YYYY-MM-DD hh24:mi:ss') as dt_prevista_recebimento
	, NULLIF(REGEXP_REPLACE(me.tp_convenio_da_cirurgia,'[''"!/:@;]', ''),'') as tp_convenio_da_cirurgia
	, TO_CHAR(me.vl_percentual_desconto) as vl_percentual_desconto
	, TO_CHAR(me.vl_desconto) as vl_desconto
	, me.cd_con_rec
	, me.cd_mvto_estoque_dev
	, TO_CHAR(me.dt_consumo_inicial, 'YYYY-MM-DD hh24:mi:ss') as dt_consumo_inicial
	, TO_CHAR(me.dt_consumo_final, 'YYYY-MM-DD hh24:mi:ss') as dt_consumo_final
	, me.cd_kit
	, me.cd_tip_doc
	, me.cd_multi_empresa
	, NULLIF(REGEXP_REPLACE(me.tp_recebido,'[''"!/:@;]', ''),'') as tp_recebido
	, NULLIF(REGEXP_REPLACE(me.nm_recebido,'[''"!/:@;]', ''),'') as nm_recebido
	, NULLIF(REGEXP_REPLACE(me.tp_retroativo,'[''"!/:@;]', ''),'') as tp_retroativo
	, TO_CHAR(me.dt_faturamento, 'YYYY-MM-DD hh24:mi:ss') as dt_faturamento
	, TO_CHAR(me.dt_entrega, 'YYYY-MM-DD hh24:mi:ss') as dt_entrega
	, TO_CHAR(me.hr_entrega, 'YYYY-MM-DD hh24:mi:ss') as hr_entrega
	, me.cd_mvto_filha
	, me.cd_mvto_cme
	, me.cd_mvto_estoque_integra
	, NULLIF(REGEXP_REPLACE(me.tp_status_confirmacao,'[''"!/:@;]', ''),'') as tp_status_confirmacao
FROM mvto_estoque me
where 
	me.dt_mvto_estoque >= ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																then '-5' 
																ELSE '-4'
															END ))
	AND me.dt_mvto_estoque < ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																	then '-1' 
																	ELSE '0'
																END ))	