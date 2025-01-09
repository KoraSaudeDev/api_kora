SELECT nr_sequencia
    , cd_estabelecimento
    , cd_convenio
    , TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') AS dt_inicio_vigencia
    , ie_situacao
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
    , cd_categoria
    , cd_grupo_material
    , cd_subgrupo_material
    , cd_classe_material
    , cd_material
    , to_char(tx_ajuste) AS tx_ajuste
    , to_char(vl_negociado) AS vl_negociado
    , ie_preco_informado
    , ie_glosa
    , to_char(tx_brasindice_pfb) AS tx_brasindice_pfb
    , to_char(tx_brasindice_pmc) AS tx_brasindice_pmc
    , to_char(tx_afaturar) AS tx_afaturar
    , TO_CHAR(dt_final_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_final_vigencia
    , cd_tipo_acomodacao
    , ie_tipo_atendimento
    , cd_setor_atendimento
    , to_char(tx_simpro_pfb) AS tx_simpro_pfb
    , to_char(tx_simpro_pmc) AS tx_simpro_pmc
    , ie_origem_preco
    , ie_precedencia_preco
    , pr_glosa
    , to_char(qt_idade_min) AS qt_idade_min
    , to_char(qt_idade_max) AS qt_idade_max
    , ie_tipo_material
    , to_char(tx_pmc_neg) AS tx_pmc_neg
    , to_char(tx_pmc_pos) AS tx_pmc_pos
    , cd_cid
    , cd_tabela_preco
    , cd_motivo_exc_conta
    , ie_sexo
    , cd_plano
    , cd_proc_referencia
    , ie_origem_proced
    , ie_autor_particular
    , cd_convenio_glosa
    , cd_categoria_glosa
    , ie_kit_material
    , nr_seq_proc_interno
    , cd_kit_material
    , ds_observacao
    , ie_data_referencia_vig
    , ie_atend_retorno
    , to_char(tx_pfb_neg) AS tx_pfb_neg
    , to_char(tx_pfb_pos) AS tx_pfb_pos
    , ie_tipo_kit
    , nr_seq_familia
    , cd_tipo_baixa
    , ie_ignora_preco_venda
    , nr_seq_just_valor_inf
    , nr_seq_estrutura
    , nr_seq_origem
    , nr_seq_cobertura
    , ie_ignora_divisao_bras
    , to_char(tx_simpro_pos_pfb) AS tx_simpro_pos_pfb
    , to_char(tx_simpro_neg_pfb) AS tx_simpro_neg_pfb
    , to_char(tx_simpro_pos_pmc) AS tx_simpro_pos_pmc
    , to_char(tx_simpro_neg_pmc) AS tx_simpro_neg_pmc
    , to_char(qt_dias_inter_inicio) AS qt_dias_inter_inicio
    , to_char(qt_dias_inter_final) AS qt_dias_inter_final
    , nr_seq_regra_lanc
    , nr_seq_lib_dieta_conv
    , ie_clinica
    , to_char(qt_pos_inicial) AS qt_pos_inicial
    , to_char(qt_pos_final) AS qt_pos_final
    , ie_estrangeiro
    , ie_reconstituinte
    , nr_seq_classificacao
    , ie_existe_tabela 
FROM tasy.regra_ajuste_material