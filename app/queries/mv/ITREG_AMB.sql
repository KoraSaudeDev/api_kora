SELECT
	ia.cd_reg_amb as cd_reg_amb,
	ia.cd_lancamento as cd_lancamento,
	TO_CHAR(ia.hr_lancamento, 'YYYY-MM-DD hh24:mi:ss') as hr_lancamento,
	ia.qt_lancamento as qt_lancamento,
	NULLIF(REGEXP_REPLACE(ia.cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	to_char(ia.vl_total_conta) as vl_total_conta,
	NULLIF(REGEXP_REPLACE(ia.sn_pertence_pacote,'[''"!/:@;]', ''),'') as sn_pertence_pacote,
	ia.cd_regra_lancamento as cd_regra_lancamento
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
