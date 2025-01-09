SELECT
	to_char(lp.cd_produto) as cd_produto,
	NULLIF(REGEXP_REPLACE(lp.cd_laborator,'[''"!/:@;]', ''),'') as cd_laborator,
	TO_CHAR(lp.dt_validade_registro, 'YYYY-MM-DD hh24:mi:ss') as dt_validade_registro,
	NULLIF(REGEXP_REPLACE(lp.cd_registro,'[''"!/:@;]', ''),'') as cd_registro
FROM
	DBAMV.LAB_PRO lp