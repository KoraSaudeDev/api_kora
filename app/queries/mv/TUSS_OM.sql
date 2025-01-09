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
	DBAMV.TUSS
WHERE

	CD_PRO_FAT IN (
		SELECT
			CD_PRO_FAT
		FROM
			DBAMV.ITREG_AMB
		WHERE
			HR_LANCAMENTO >= ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																	then '-5' 
																	ELSE '-4'
																END ))
			AND HR_LANCAMENTO < ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																		then '-1' 
																		ELSE '0'
																	END ))	
		UNION
		SELECT
			CD_PRO_FAT
		FROM
			DBAMV.ITREG_FAT
		WHERE
			DT_LANCAMENTO >= ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																	then '-5' 
																	ELSE '-4'
																END ))
			AND DT_LANCAMENTO < ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																		then '-1' 
																		ELSE '0'
																	END ))	
		UNION
		SELECT
			CD_PRO_FAT
		FROM
			DBAMV.PRODUTO
	)
