SELECT
	cd_reg_amb as cd_reg_amb,
	cd_remessa as cd_remessa,
	cd_convenio as cd_convenio,
	cd_multi_empresa as cd_multi_empresa
FROM
	DBAMV.REG_AMB
WHERE
	CD_REG_AMB IN (
		SELECT
			CD_REG_AMB
		FROM
			DBAMV.ITREG_AMB ia
		WHERE
			ia.HR_LANCAMENTO >= ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																	then '-5' 
																	ELSE '-4'
																END ))
			AND ia.HR_LANCAMENTO < ADD_MONTHS(TRUNC(SYSDATE, 'mm'), (CASE WHEN EXTRACT(DAY FROM sysdate) < 20 
																		then '-1' 
																		ELSE '0'
																	END ))
		)
	
