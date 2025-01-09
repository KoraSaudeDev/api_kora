SELECT
	nr_seq_protocolo
	, REGEXP_REPLACE(ds_kit_material,'[''"!/:@;]', '') as ds_kit_material
	, REGEXP_REPLACE(ds_observacao,'[''"!/:@;]', '') as ds_observacao
	, REGEXP_REPLACE(ie_forma_baixa,'[''"!/:@;]', '') as ie_forma_baixa
	, REGEXP_REPLACE(ie_gerar_remontagem,'[''"!/:@;]', '') as ie_gerar_remontagem
	, REGEXP_REPLACE(ie_gerar_solucao,'[''"!/:@;]', '') as ie_gerar_solucao
	, REGEXP_REPLACE(ie_material_pai,'[''"!/:@;]', '') as ie_material_pai
	, REGEXP_REPLACE(ie_situacao,'[''"!/:@;]', '') as ie_situacao
	, REGEXP_REPLACE(ie_tipo,'[''"!/:@;]', '') as ie_tipo
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, REGEXP_REPLACE(nm_usuario_revisao,'[''"!/:@;]', '') as nm_usuario_revisao
	, cd_empresa
	, cd_especialidade_medica
	, cd_estab_exclusivo
	, cd_kit_material
	, cd_local_exclusivo
	, cd_setor_exclusivo
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_revisao, 'YYYY-MM-DD hh24:mi:ss') as dt_revisao
FROM
	TASY.KIT_MATERIAL