SELECT
	e.cd_ent_pro as cd_ent_pro,
	e.cd_estoque as cd_estoque,
	TO_CHAR(e.dt_entrada, 'YYYY-MM-DD hh24:mi:ss') as dt_entrada,
	NULLIF(REGEXP_REPLACE(e.nr_documento,'[''"!/:@;]', ''),'') as nr_documento,
	e.cd_tip_doc as cd_tip_doc
FROM
	DBAMV.ENT_PRO e
WHERE
	e.DT_ENTRADA >= TO_DATE('2019-01-01', 'YYYY-MM-DD')