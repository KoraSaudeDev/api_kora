SELECT
	ib.CD_TAB_FAT,
	NULLIF(REGEXP_REPLACE(ib.cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	NULLIF(REGEXP_REPLACE(ib.cd_laboratorio,'[''"!/:@;]', ''),'') as cd_laboratorio,
	NULLIF(REGEXP_REPLACE(ib.cd_medicamento,'[[''"!/:@;]', ''),'') as cd_medicamento,
	NULLIF(REGEXP_REPLACE(ib.cd_apresentacao,'[''"!/:@;]', ''),'') as cd_apresentacao,
	to_char(ib.vl_fator_divisao) as vl_fator_divisao,
	ib.cd_imp_bra as cd_imp_bra,
	ib.CD_TISS,
	ib.CD_TUSS	
FROM
	DBAMV.IMP_BRA ib