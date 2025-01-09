SELECT
	REGEXP_REPLACE(cd_categoria,'[''"!/:@;]', '') as cd_categoria
	, REGEXP_REPLACE(cd_classif_setor,'[''"!/:@;]', '') as cd_classif_setor
	, REGEXP_REPLACE(cd_doenca,'[''"!/:@;]', '') as cd_doenca
	, REGEXP_REPLACE(cd_plano,'[''"!/:@;]', '') as cd_plano
	, REGEXP_REPLACE(ds_mascara_carteira,'[''"!/:@;]', '') as ds_mascara_carteira
	, REGEXP_REPLACE(ds_observacao,'[''"!/:@;]', '') as ds_observacao
	, REGEXP_REPLACE(ie_autor_kit,'[''"!/:@;]', '') as ie_autor_kit
	, REGEXP_REPLACE(ie_autor_particular,'[''"!/:@;]', '') as ie_autor_particular
	, REGEXP_REPLACE(ie_carater_inter_sus,'[''"!/:@;]', '') as ie_carater_inter_sus
	, REGEXP_REPLACE(ie_classificacao,'[''"!/:@;]', '') as ie_classificacao
	, REGEXP_REPLACE(ie_consignado,'[''"!/:@;]', '') as ie_consignado
	, REGEXP_REPLACE(ie_exige_just_medica,'[''"!/:@;]', '') as ie_exige_just_medica
	, REGEXP_REPLACE(ie_final_vig_dose_dia_prescr,'[''"!/:@;]', '') as ie_final_vig_dose_dia_prescr
	, REGEXP_REPLACE(ie_gerar_mat_esp,'[''"!/:@;]', '') as ie_gerar_mat_esp
	, REGEXP_REPLACE(ie_gerar_vl_zerado,'[''"!/:@;]', '') as ie_gerar_vl_zerado
	, REGEXP_REPLACE(ie_mat_conta,'[''"!/:@;]', '') as ie_mat_conta
	, REGEXP_REPLACE(ie_nova_autorizacao,'[''"!/:@;]', '') as ie_nova_autorizacao
	, REGEXP_REPLACE(ie_regra_quantidade_solic,'[''"!/:@;]', '') as ie_regra_quantidade_solic
	, REGEXP_REPLACE(ie_resp_autor,'[''"!/:@;]', '') as ie_resp_autor
	, REGEXP_REPLACE(ie_tipo_material,'[''"!/:@;]', '') as ie_tipo_material
	, REGEXP_REPLACE(ie_tiss_tipo_anexo,'[''"!/:@;]', '') as ie_tiss_tipo_anexo
	, REGEXP_REPLACE(ie_tiss_tipo_etapa_autor,'[''"!/:@;]', '') as ie_tiss_tipo_etapa_autor
	, REGEXP_REPLACE(ie_valor,'[''"!/:@;]', '') as ie_valor
	, REGEXP_REPLACE(ie_valor_dia,'[''"!/:@;]', '') as ie_valor_dia
	, REGEXP_REPLACE(ie_valor_unitario,'[''"!/:@;]', '') as ie_valor_unitario
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, REGEXP_REPLACE(nm_usuario_nrec,'[''"!/:@;]', '') as nm_usuario_nrec
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao_nrec
	, TO_CHAR(dt_fim_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_fim_vigencia
	, TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia
	, TO_CHAR(cd_classe_material) as cd_classe_material
	, TO_CHAR(cd_convenio) as cd_convenio
	, TO_CHAR(cd_empresa_conv) as cd_empresa_conv
	, TO_CHAR(cd_estabelecimento) as cd_estabelecimento
	, TO_CHAR(cd_grupo_material) as cd_grupo_material
	, TO_CHAR(cd_material) as cd_material
	, TO_CHAR(cd_material_estoque) as cd_material_estoque
	, TO_CHAR(cd_perfil) as cd_perfil
	, TO_CHAR(cd_setor_atendimento) as cd_setor_atendimento
	, TO_CHAR(cd_subgrupo_material) as cd_subgrupo_material
	, TO_CHAR(cd_tipo_acomodacao) as cd_tipo_acomodacao
	, TO_CHAR(ie_clinica) as ie_clinica
	, TO_CHAR(ie_regra) as ie_regra
	, TO_CHAR(ie_tipo_atendimento) as ie_tipo_atendimento
	, TO_CHAR(nr_seq_classif) as nr_seq_classif
	, TO_CHAR(nr_seq_cobertura) as nr_seq_cobertura
	, TO_CHAR(nr_seq_estrutura) as nr_seq_estrutura
	, TO_CHAR(nr_seq_familia) as nr_seq_familia
	, TO_CHAR(nr_sequencia) as nr_sequencia
	, TO_CHAR(qt_maxima) as qt_maxima
	, TO_CHAR(qt_minima) as qt_minima
	, TO_CHAR(vl_material_max) as vl_material_max
	, TO_CHAR(vl_material_min) as vl_material_min
FROM
	TASY.REGRA_CONVENIO_PLANO_MAT