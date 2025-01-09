SELECT
	p.cd_produto as cd_produto,
	p.cd_especie as cd_especie,
	NULLIF(REGEXP_REPLACE(p.ds_produto,'[''"!/:@;]', ''),'') as ds_produto,
	TO_CHAR(p.dt_ultima_entrada, 'YYYY-MM-DD hh24:mi:ss') as dt_ultima_entrada,
	to_char(p.vl_custo_medio) as vl_custo_medio,
	NULLIF(REGEXP_REPLACE(p.sn_movimentacao,'[''"!/:@;]', ''),'') as sn_movimentacao,
	NULLIF(REGEXP_REPLACE(p.cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	p.sn_fracionado,
	to_char(p.vl_fator_pro_fat) as vl_fator_pro_fat,
	to_char(p.vl_ultima_entrada) as vl_ultima_entrada
FROM
	DBAMV.PRODUTO p