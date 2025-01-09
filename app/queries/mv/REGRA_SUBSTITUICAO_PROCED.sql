SELECT
	rsp.cd_regra_substituicao_proced as cd_regra_substituicao_proced,
	rsp.cd_multi_empresa as cd_multi_empresa,
	rsp.cd_convenio as cd_convenio,
	NULLIF(REGEXP_REPLACE(rsp.cd_pro_fat,'[''"!/:@;]', ''),'') as cd_pro_fat,
	NULLIF(REGEXP_REPLACE(rsp.cd_pro_fat_substituto,'[''"!/:@;]', ''),'') as cd_pro_fat_substituto,
	TO_CHAR(rsp.dt_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_vigencia,
	rsp.cd_setor as cd_setor,
	NULLIF(REGEXP_REPLACE(rsp.tp_atendimento,'[''"!/:@;]', ''),'') as tp_atendimento,
	to_char(rsp.vl_fator_multiplicacao) as vl_fator_multiplicacao,
	to_char(rsp.vl_fator_divisao) as vl_fator_divisao,
	NULLIF(REGEXP_REPLACE(rsp.tp_fator,'[''"!/:@;]', ''),'') as tp_fator
FROM
	dbamv.regra_substituicao_proced rsp