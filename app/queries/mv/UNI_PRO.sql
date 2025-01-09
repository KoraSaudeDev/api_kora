SELECT
	up.cd_uni_pro as cd_uni_pro,
	NULLIF(REGEXP_REPLACE(up.cd_unidade,'[''"!/:@;]', ''),'') as cd_unidade,
	up.cd_produto as cd_produto,
	NULLIF(REGEXP_REPLACE(up.ds_unidade,'[''"!/:@;]', ''),'') as ds_unidade,
	to_char(up.vl_fator) as vl_fator,
	NULLIF(REGEXP_REPLACE(up.tp_relatorios,'[''"!/:@;]', ''),'') as tp_relatorios,
	NULLIF(REGEXP_REPLACE(up.cd_codigo_de_barras,'[''"!/:@;]', ''),'') as cd_codigo_de_barras,
	NULLIF(REGEXP_REPLACE(up.sn_ativo,'[''"!/:@;]', ''),'') as sn_ativo,
	up.cd_itunidade as cd_itunidade,
	NULLIF(REGEXP_REPLACE(up.ds_unidade_presc,'[''"!/:@;]', ''),'') as ds_unidade_presc,
	NULLIF(REGEXP_REPLACE(up.sn_prescricao,'[''"!/:@;]', ''),'') as sn_prescricao,
	NULLIF(REGEXP_REPLACE(up.tp_tempo,'[''"!/:@;]', ''),'') as tp_tempo,
	NULLIF(REGEXP_REPLACE(up.cd_uni_pro_integra,'[''"!/:@;]', ''),'') as cd_uni_pro_integra,
	TO_CHAR(up.dt_integra, 'YYYY-MM-DD hh24:mi:ss') as dt_integra,
	up.cd_seq_integra as cd_seq_integra,
	NULLIF(REGEXP_REPLACE(up.cd_uni_pro_maxima,'[''"!/:@;]', ''),'') as cd_uni_pro_maxima
FROM
	DBAMV.UNI_PRO up