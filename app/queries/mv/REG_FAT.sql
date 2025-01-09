SELECT
	cd_reg_fat as cd_reg_fat,
	cd_remessa as cd_remessa,
	cd_convenio as cd_convenio,
	cd_multi_empresa as cd_multi_empresa
FROM
	DBAMV.REG_FAT
WHERE
	CD_REG_FAT IN (
		SELECT
			CD_REG_FAT
		FROM
			DBAMV.ITREG_FAT ia
		WHERE
			ia.DT_LANCAMENTO >= ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																	then '-5' 
																	ELSE '-4'
																END ))
			AND ia. DT_LANCAMENTO < ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																		then '-1' 
																		ELSE '0'
																	END ))	
		)
