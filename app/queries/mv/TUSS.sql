SELECT
	cd_tip_tuss as cd_tip_tuss,
	NULLIF(REGEXP_REPLACE(cd_tuss,'[''"!/:@;]', ''),'') as cd_tuss,
	TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia,
	TO_CHAR(dt_fim_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_fim_vigencia,
	cd_seq_tuss as cd_seq_tuss,
	cd_multi_empresa as cd_multi_empresa,
	cd_convenio as cd_convenio,
	NULLIF(REGEXP_REPLACE(cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	NULLIF(REGEXP_REPLACE(cd_referencia,'[''"!/:@;]', ''),'') as cd_referencia
FROM
	DBAMV.TUSS t