SELECT
	rl.cd_regra_lancamento as cd_regra_lancamento,
	NULLIF(REGEXP_REPLACE(rl.cd_pro_fat,'[''"!/:-@[-`{-~]', ''),'') as cd_pro_fat,
	NULLIF(REGEXP_REPLACE(rl.cd_pro_fat_subordinado,'[''"!/:-@[-`{-~]', ''),'') as cd_pro_fat_subordinado
FROM
	DBAMV.REGRA_LANCAMENTO rl