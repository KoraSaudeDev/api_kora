SELECT
	to_char(cd_especie) as cd_especie,
	NULLIF(REGEXP_REPLACE(ds_especie,'[''"!/:@;]', ''),'') as ds_especie
FROM
	DBAMV.ESPECIE