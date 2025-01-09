SELECT
	NULLIF(REGEXP_REPLACE(cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	NULLIF(REGEXP_REPLACE(ds_pro_fat,'[''"!/:@;]', ''),'') as ds_pro_fat,
	cd_gru_pro as cd_gru_pro,
	NULLIF(REGEXP_REPLACE(ds_unidade,'[''"!/:@;]', ''),'') as ds_unidade,
	sn_ativo,
	fator,
	vl_custo
FROM
	DBAMV.PRO_FAT pf