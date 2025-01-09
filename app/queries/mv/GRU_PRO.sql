SELECT
	to_char(cd_gru_pro) as cd_gru_pro,
	NULLIF(REGEXP_REPLACE(ds_gru_pro,'[''"!/:@;]', ''),'') as ds_gru_pro
FROM
	DBAMV.GRU_PRO