SELECT 
    cd_estabelecimento
    , cd_tab_preco_mat
    , cd_material
    , TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') AS dt_inicio_vigencia
    , to_char(vl_preco_venda) AS vl_preco_venda
    , cd_moeda
    , ie_brasindice
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
    , cd_unidade_medida
    , to_char(qt_conversao) AS qt_conversao
    , ie_situacao
    , nr_sequencia_nf
    , nr_item_nf
    , cd_cgc_fornecedor
    , TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') AS dt_atualizacao_nrec
    , ie_preco_venda
    , ie_inpart
    , ie_manual
    , nr_seq_motivo
    , TO_CHAR(dt_final_vigencia, 'YYYY-MM-DD hh24:mi:ss') AS dt_final_vigencia
    , ie_integracao 
FROM tasy.preco_material

