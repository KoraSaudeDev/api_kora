SELECT 
    cd_con_pla
    ,cd_convenio
    ,cd_multi_empresa
    ,sn_ativo
    ,cd_regra
    ,cd_indice
    ,sn_permite_ambulatorio
    ,sn_permite_internacao
    ,sn_permite_hoca
    ,sn_permite_urgencia
    ,sn_permite_externo
    ,sn_obriga_senha
    ,sn_valida_nr_guia
    ,sn_obriga_guia_na_diaria
	,TO_CHAR(hr_vencimento, 'YYYY-MM-DD hh24:mi:ss') as hr_vencimento
    ,nr_tempo_tolerancia
	,TO_CHAR(hr_limite, 'YYYY-MM-DD hh24:mi:ss') as hr_limite
    ,cd_gru_fat
    ,cd_pro_fat
    ,qt_pro_fat
FROM empresa_con_pla ecp
