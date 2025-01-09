SELECT
	cd_tip_doc as cd_tip_doc,
	NULLIF(REGEXP_REPLACE(ds_tip_doc,'[''"!/:@;]', ''),'') as ds_tip_doc,
	NULLIF(REGEXP_REPLACE(tp_documento,'[''"!/:@;]', ''),'') as tp_documento,
	NULLIF(REGEXP_REPLACE(tp_entrada,'[''"!/:@;]', ''),'') as tp_entrada
FROM
	DBAMV.TIP_DOC