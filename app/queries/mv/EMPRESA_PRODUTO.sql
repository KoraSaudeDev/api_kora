SELECT
	ep.cd_produto as cd_produto,
	ep.cd_multi_empresa as cd_multi_empresa,
	TO_CHAR(ep.dt_ultima_entrada, 'YYYY-MM-DD hh24:mi:ss') as dt_ultima_entrada,
	to_char(ep.vl_custo_medio) as vl_custo_medio,
	TO_CHAR(ep.hr_ultima_entrada, 'YYYY-MM-DD hh24:mi:ss') as hr_ultima_entrada,
	to_char(ep.vl_ultima_entrada) as vl_ultima_entrada,
	NULLIF(REGEXP_REPLACE(ep.sn_ativo,'[''"!/:@;]', ''),'') as sn_ativo
FROM
	DBAMV.EMPRESA_PRODUTO ep