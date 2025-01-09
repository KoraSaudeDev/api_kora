SELECT
	REGEXP_REPLACE(cd_categoria,'[''"!/:@;]', '') as cd_categoria
	, REGEXP_REPLACE(cd_classif_setor,'[''"!/:@;]', '') as cd_classif_setor
	, REGEXP_REPLACE(cd_doenca,'[''"!/:@;]', '') as cd_doenca
	, REGEXP_REPLACE(cd_medico_executor,'[''"!/:@;]', '') as cd_medico_executor
	, REGEXP_REPLACE(cd_pessoa_fisica,'[''"!/:@;]', '') as cd_pessoa_fisica
	, REGEXP_REPLACE(cd_plano,'[''"!/:@;]', '') as cd_plano
	, REGEXP_REPLACE(cd_procedimento_loc,'[''"!/:@;]', '') as cd_procedimento_loc
	, REGEXP_REPLACE(ds_inconsist_pep,'[''"!/:@;]', '') as ds_inconsist_pep
	, REGEXP_REPLACE(ds_inconsist_prescr,'[''"!/:@;]', '') as ds_inconsist_prescr
	, REGEXP_REPLACE(ds_mascara_carteira,'[''"!/:@;]', '') as ds_mascara_carteira
	, REGEXP_REPLACE(ds_observacao,'[''"!/:@;]', '') as ds_observacao
	, REGEXP_REPLACE(ie_autor_kit,'[''"!/:@;]', '') as ie_autor_kit
	, REGEXP_REPLACE(ie_autor_particular,'[''"!/:@;]', '') as ie_autor_particular
	, REGEXP_REPLACE(ie_carater_cirurgia,'[''"!/:@;]', '') as ie_carater_cirurgia
	, REGEXP_REPLACE(ie_carater_inter_sus,'[''"!/:@;]', '') as ie_carater_inter_sus
	, REGEXP_REPLACE(ie_checkup,'[''"!/:@;]', '') as ie_checkup
	, REGEXP_REPLACE(ie_exige_just_medica,'[''"!/:@;]', '') as ie_exige_just_medica
	, REGEXP_REPLACE(ie_nova_autorizacao,'[''"!/:@;]', '') as ie_nova_autorizacao
	, REGEXP_REPLACE(ie_prioridade,'[''"!/:@;]', '') as ie_prioridade
	, REGEXP_REPLACE(ie_qt_total_autor,'[''"!/:@;]', '') as ie_qt_total_autor
	, REGEXP_REPLACE(ie_regra_valor,'[''"!/:@;]', '') as ie_regra_valor
	, REGEXP_REPLACE(ie_resp_autor,'[''"!/:@;]', '') as ie_resp_autor
	, REGEXP_REPLACE(ie_situacao,'[''"!/:@;]', '') as ie_situacao
	, REGEXP_REPLACE(ie_somente_item,'[''"!/:@;]', '') as ie_somente_item
	, REGEXP_REPLACE(ie_tiss_cobertura_especial,'[''"!/:@;]', '') as ie_tiss_cobertura_especial
	, REGEXP_REPLACE(ie_tiss_tipo_etapa_autor,'[''"!/:@;]', '') as ie_tiss_tipo_etapa_autor
	, REGEXP_REPLACE(ie_valida_bonus_conv,'[''"!/:@;]', '') as ie_valida_bonus_conv
	, REGEXP_REPLACE(ie_valor,'[''"!/:@;]', '') as ie_valor
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_fim_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_fim_vigencia
	, TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia
	, TO_CHAR(cd_area_procedimento) as cd_area_procedimento
	, TO_CHAR(cd_convenio) as cd_convenio
	, TO_CHAR(cd_edicao_amb) as cd_edicao_amb
	, TO_CHAR(cd_empresa_conv) as cd_empresa_conv
	, TO_CHAR(cd_especialidade_medic) as cd_especialidade_medic
	, TO_CHAR(cd_especialidade_proc) as cd_especialidade_proc
	, TO_CHAR(cd_estabelecimento) as cd_estabelecimento
	, TO_CHAR(cd_grupo_proc) as cd_grupo_proc
	, TO_CHAR(cd_perfil) as cd_perfil
	, TO_CHAR(cd_procedimento) as cd_procedimento
	, TO_CHAR(cd_setor_atendimento) as cd_setor_atendimento
	, TO_CHAR(cd_setor_atual) as cd_setor_atual
	, TO_CHAR(cd_setor_entrega_prescr) as cd_setor_entrega_prescr
	, TO_CHAR(cd_tipo_acomodacao) as cd_tipo_acomodacao
	, TO_CHAR(ie_clinica) as ie_clinica
	, TO_CHAR(ie_origem_proced) as ie_origem_proced
	, TO_CHAR(ie_regra) as ie_regra
	, TO_CHAR(ie_tipo_atendimento) as ie_tipo_atendimento
	, TO_CHAR(nr_seq_cbhpm_edicao) as nr_seq_cbhpm_edicao
	, TO_CHAR(nr_seq_classif) as nr_seq_classif
	, TO_CHAR(nr_seq_classif_atend) as nr_seq_classif_atend
	, TO_CHAR(nr_seq_classif_proc_int) as nr_seq_classif_proc_int
	, TO_CHAR(nr_seq_cobertura) as nr_seq_cobertura
	, TO_CHAR(nr_seq_estagio) as nr_seq_estagio
	, TO_CHAR(nr_seq_exame) as nr_seq_exame
	, TO_CHAR(nr_seq_forma_org) as nr_seq_forma_org
	, TO_CHAR(nr_seq_grupo) as nr_seq_grupo
	, TO_CHAR(nr_seq_proc_interno) as nr_seq_proc_interno
	, TO_CHAR(nr_seq_subgrupo) as nr_seq_subgrupo
	, TO_CHAR(nr_sequencia) as nr_sequencia
	, TO_CHAR(qt_bonus) as qt_bonus
	, TO_CHAR(qt_dias_autorizacao) as qt_dias_autorizacao
	, TO_CHAR(qt_idade_max) as qt_idade_max
	, TO_CHAR(qt_idade_min) as qt_idade_min
	, TO_CHAR(qt_maximo) as qt_maximo
	, TO_CHAR(qt_minimo) as qt_minimo
	, TO_CHAR(qt_ponto_max) as qt_ponto_max
	, TO_CHAR(qt_ponto_min) as qt_ponto_min
FROM
	TASY.REGRA_CONVENIO_PLANO