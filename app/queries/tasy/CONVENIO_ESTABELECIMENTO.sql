SELECT nr_sequencia
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
    , cd_convenio
    , cd_estabelecimento
    , nr_seq_regra_funcao
    , nr_seq_conta
    , cd_conta_pre_fatur
    , TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao_nrec
    , ie_exige_data_ult_pagto
    , ie_exige_guia
    , ie_exige_orc_atend
    , ie_glosa_atendimento
    , ie_preco_medio_material
    , ie_agenda_consulta
    , ie_rep_cod_usuario
    , ie_exige_carteira_atend
    , ie_exige_validade_atend
    , ie_exige_plano
    , ie_separa_conta
    , ie_guia_unica_conta
    , ie_valor_contabil
    , ie_titulo_receber
    , ie_conversao_mat
    , ie_doc_convenio
    , ie_doc_retorno
    , to_char(qt_conta_protocolo) AS qt_conta_protocolo
    , to_char(qt_dia_fim_conta) AS qt_dia_fim_conta
    , ie_exige_senha_atend
    , ie_partic_cirurgia
    , ie_exige_origem
    , cd_interno
    , cd_regional
    , ie_protocolo_conta
    , ie_gerar_nf_titulo
    , ie_cancelar_conta
    , ie_manter_zerado_edicao
    , nr_dec_unitario
    , ie_arredondamento
    , ie_exige_guia_princ
    , nr_seq_conta_banco
    , ie_exige_doc_conv_titulo
    , nr_seq_envio_prot
    , ie_origem_preco
    , ie_precedencia_preco
    , ie_partic_resp_cred
    , ie_exige_fim_vigencia
    , ie_doc_autorizacao
    , ie_fechar_atend_adiant
    , ie_conta_fim_mes
    , ie_repasse_proc
    , ie_repasse_mat
    , ie_atualiza_func_medico
    , ie_cgc_cih
    , ie_valor_filme_tab_preco
    , ie_regra_prior_edicao
    , ie_medico_cooperado
    , ie_doc_conv_part_func
    , ie_consiste_guia_atend
    , ie_exige_compl_usuario
    , nr_seq_trans_fin_conv_ret
    , ie_obter_preco_mat_autor
    , ie_lib_repasse
    , ie_gerar_nf
    , ie_retem_iss
    , ie_autorizacao_eup
    , ie_exige_tempo_doenca
    , ie_pf_unica_nf_prot
    , ie_exige_gabarito
    , ie_lancto_auto_dt_alta
    , ie_motivo_glosa_conv
    , ie_repasse_gratuidade
    , ie_chamada_titulo
    , ie_substituir_guia
    , ie_titulo_sem_nf
    , ie_guia_transf_conta
    , to_char(qt_dia_conta_ret) AS qt_dia_conta_ret
    , ie_calcular_nf
    , ie_grava_guia_conta
    , ie_autor_generico
    , ie_exige_email
    , ie_exige_tipo_faturamento
    , ie_exige_cpf_paciente
    , ds_mascara_guia_proc
    , ie_exige_nr_conv
    , ie_consiste_pac_protocolo
    , ie_cons_duplic_cod_usu
    , ie_tit_ret_senha
    , ie_cons_dia_int_vig
    , ie_obter_fornec_mat_autor
    , ie_gera_nome_nf_convenio
    , ie_forma_geracao_nf
    , ie_forma_rateio_sadt
    , ie_indice_ajuste_filme
    , ie_obriga_titulo_partic
    , ie_glosa_adic_ret
    , ie_atualiza_serie_nf_saida
    , nr_dias_venc
    , ie_obriga_titulo_prot
    , ie_exige_passaporte_paciente
    , ie_tipo_glosa_ret
    , ie_obrigar_item_glosa
    , ie_preco_medio_bras
    , ie_forma_autor_quimioterapia
    , nr_seq_trans_tit_prot
    , ie_obriga_obs_desc_prot
    , ie_converte_ml_fr
    , ie_permite_cod_convenio_duplic
    , ie_trunc_vl_material
    , ie_consistir_tit
    , ie_exige_cpf_titulo
    , ie_fecha_conta_int
    , nr_seq_tf_cr_grc
    , nr_seq_tf_cp_grc
    , ie_gerar_desconto
    , ie_proc_tuss_autor
    , ie_partic_ret
    , ie_arred_multiplicado
    , ie_converte_itens_audit
    , ie_conta_fim_dia
    , ie_tit_prot_pf
    , cd_ans
    , ie_fixar_vig_brasindice
    , ie_conta_atual
    , ie_separa_partic_adic_hor
    , ie_vl_conta_autor
    , ie_ajustar_periodo_conta
    , ie_atual_qt_solic_autor
    , ie_lote_reap
    , ie_exige_cobertura
    , ie_altera_pj_tit
    , ie_regra_cart_usuario
    , ie_dt_prev_autor_quimio
    , ie_dt_vigencia_autor_quimio
    , to_char(qt_horas_inicio_ciclo) AS qt_horas_inicio_ciclo
    , TO_CHAR(dt_inicio_vig_tuss, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vig_tuss
    , ie_valor_original_glosa
    , ie_considera_regra_data_preco
    , ie_contab_lote_consig
    , ie_exige_cpf_pagador
    , ie_verifica_proc_glosa
    , ie_valor_filme_apos_adic_hor
    , ie_pre_faturamento
    , ds_proc_retorno
    , ie_divide_vl_med_conv_glosa
    , hr_conta_fim_dia
    , ie_autor_mat_conta
    , nr_dias_gastos_rn
    , cd_proc_long_perm
    , ie_orig_proc_long_perm
    , nr_dias_venc_atend
    , nr_dias_alerta
    , ie_exige_desconto_conta
    , ie_imprime_data_rodape
    , ie_periodo_inicial_seg
    , ie_trat_conta_rn
    , ie_consid_proc_bilat_autor
    , ie_data_vig_cbhpm
    , ie_regra_moeda_ajuste
    , ds_mensagem_desfecho
    , ie_consiste_benef_ops
    , ie_conta_transitoria
    , ie_imprime_qtde
    , ie_lib_repasse_sem_tit
    , ie_arred_so_glosa_perc
    , ie_grava_guia_taxa
    , to_char(qt_dia_venc_tit_grg) AS qt_dia_venc_tit_grg
    , TO_CHAR(dt_fim_contrato, 'YYYY-MM-DD hh24:mi:ss') as dt_fim_contrato
    , ie_copia_senha_guia
    , ie_glosa_aceita_grg
    , ie_conv_categ_glosa
    , cd_estab_pls
    , ie_registro_pep
    , ie_exige_conv_glosa
    , ie_exige_usuario_glosa
    , ie_exige_compl_glosa
    , ie_exige_validade_glosa
    , to_char(qt_exame_prescr) AS qt_exame_prescr
    , ie_consid_conv_glosa_eup
    , ie_consiste_conta_prot
    , ie_tiss_tipo_saida
    , ie_funcao_medico
    , ie_conta_prot_ref
    , ie_glosa_mat_aut_neg
    , ie_dt_conta_tit_prot
    , ie_obriga_diagnostico
    , ie_nova_autor_item_fim_vig
    , ie_dividir_indice_pmc
    , ie_dividir_indice_pfb
    , ie_tit_liquido
    , nr_seq_trans_tit_conta
    , cd_tipo_receb_neg_tit
    , ie_titulo_empresa_resp
    , ie_ret_outros_conv
    , ie_ipi_brasindice
    , cd_localizador_paciente
    , ds_caminho_exec
    , cd_cnpj_conv_estab
    , ie_titulo_paciente_prot
    , ie_gerar_ciha
    , ie_inc_conta_def_prot
    , ie_bloqueia_proc_sem_autor
    , ie_aux_maior_aux_cir
    , to_char(qt_dias_internacao) AS qt_dias_internacao
    , ie_exige_letra_carteira
    , ie_copia_senha_guia_princ
    , ie_obriga_nf_prot
    , ie_gerar_autor_quimioterapia
    , ie_consiste_sql_nf
    , ie_fechar_analise_saldo_rest
    , ie_atualiza_autor_senha
    , ie_valor_pago_glosa_guia
    , ie_regra_horas_onc_ciclo
    , ie_utiliza_conv_bo
    , ie_recalcular_conta
    , ie_exige_doc_conv
    , ie_permite_internar_eup
    , ie_calc_porte_estab
    , ie_codigo_convenio
    , to_char(qt_dias_reapre) AS qt_dias_reapre
    , to_char(qt_dias_autorizacao) AS qt_dias_autorizacao
    , to_char(qt_dias_autor_proc) AS qt_dias_autor_proc
    , ie_consiste_cns_conta
    , ie_ch_anestesista
    , ie_valor_pago_ret
    , ie_exige_lib_bras
    , ie_aplicar_tx_co_cbhpm
    , ie_valor_inf_reversao
    , ie_data_autor_prorrog
    , ie_prioridade_brasindice
    , ie_autor_mat_exec
    , ie_preco_mat_esp
    , ie_plano_consulta_preco
    , ie_lib_repasse_prot_tit
    , ie_forma_proc_princ
    , ie_exige_dt_venc_prot
    , ie_permite_vinc_orc
    , ie_gerar_nf_desdob
    , ie_autor_mat_esp_cirurgia
    , ie_qt_mat_autor
    , ie_exige_empresa_cons
    , ie_obriga_nf_tit_rec    
    , ie_calc_vl_aux_conv
    , ie_conv_medida_autor_quimio
    , ie_trib_titulo_retorno
    , ie_tomador_nf_desdob
    , ie_consis_inicio_conta_prot
    , ie_ignora_partic
    , ie_autor_prescr_saldo
    , ie_biometria_atend
    , ie_autor_desdob_conta
    , ie_consiste_regra_ipasgo
    , ie_consiste_seq_conta
    , ie_origem_fat_direto
    , ie_taxa_tempo_unidade
    , to_char(qt_dia_desdob_conta) AS qt_dia_desdob_conta
    , ie_valor_pago_cobrado_ret
    , ie_considera_dt_entrada
    , ie_considera_dt_entrada_anam
    , ie_fixar_vig_simpro
    , ie_permite_desd_planserv
    , ie_protocolo_individual
    , ie_atualiza_just_anl_ant
    , ie_exibe_titular_conv
    , ie_bloq_lancto_guia_anl_grg
    , ie_permite_integracao
    , ie_valor_coseguro
    , nr_seq_evento_integracao
    , ie_vinc_adiant_prot_pj
    , cd_regra_hon_som_filme_ipe
    , ie_prioridade_simpro
    , ie_conversao_conv_item
    , ie_prioridade_pacote_job
    , ie_prostheses_price
    , ie_split_by_partial_payment
    , ie_validacao_tiss_freepass
    , ie_generate_dam_ir
    , ie_gen_resub_by_default
    , ie_arred_vl_bras_ant
    , ie_tipo_titulo_rec
    , ie_lib_repasse_tit_conv
    , ie_desdob_pagto_recurso
    , ie_utiliza_wint
    , cd_proc_long_perm_loc
    , ie_copiar_etapa_desdob
    , TO_CHAR(dt_dia_entrega, 'YYYY-MM-DD hh24:mi:ss') AS dt_dia_entrega
    , TO_CHAR(dt_entrega_prot, 'YYYY-MM-DD hh24:mi:ss') AS dt_entrega_prot
    , to_char(qt_dias_tol_entrega) AS qt_dias_tol_entrega
    , ie_remun_por_diagnostico
    , ie_regra_ordem_pacote 
FROM tasy.convenio_estabelecimento