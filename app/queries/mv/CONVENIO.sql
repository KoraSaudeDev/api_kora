SELECT
	to_char(cd_convenio) as cd_convenio,
	NULLIF(REGEXP_REPLACE(nm_convenio,'[''"!/:@;]', ''),'') as nm_convenio,
	NULLIF(REGEXP_REPLACE(sn_ativo,'[''"!/:@;]', ''),'') as sn_ativo
FROM
	DBAMV.CONVENIO