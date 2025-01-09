SELECT
	cd_estoque as cd_estoque,
	NULLIF(REGEXP_REPLACE(ds_estoque,'[''"!/:@;]', ''),'') as ds_estoque,
	cd_multi_empresa as cd_multi_empresa
FROM
	DBAMV.ESTOQUE