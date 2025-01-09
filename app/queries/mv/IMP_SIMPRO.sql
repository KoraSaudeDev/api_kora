SELECT
	NULLIF(REGEXP_REPLACE(ips.cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	to_char(ips.cd_imp_simpro) as cd_imp_simpro,
	NULLIF(REGEXP_REPLACE(ips.cd_simpro,'[''"!/:@;]', ''),'') as cd_simpro,
	NULLIF(REGEXP_REPLACE(ips.cd_tuss,'[''"!/:@;]', ''),'') as cd_tuss
FROM
	DBAMV.IMP_SIMPRO ips