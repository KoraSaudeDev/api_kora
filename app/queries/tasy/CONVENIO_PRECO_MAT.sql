SELECT 
	cd_estabelecimento
    , cd_convenio
    , cd_categoria
    , TO_CHAR(dt_liberacao_tabela, 'YYYY-MM-DD hh24:mi:ss') AS dt_liberacao_tabela
    , cd_tab_preco_mat
    , TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') AS dt_atualizacao
    , tx_ajuste_tabela_mat
    , ie_situacao
    , nr_prioridade
    , TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') AS dt_inicio_vigencia
    , TO_CHAR(dt_final_vigencia, 'YYYY-MM-DD hh24:mi:ss') AS dt_final_vigencia
    , ie_tab_adicional
    , cd_tab_mat_atualizacao
    , ie_integracao_opme
    , cd_grupo_material
    , cd_subgrupo_material
    , cd_classe_material 
FROM tasy.convenio_preco_mat