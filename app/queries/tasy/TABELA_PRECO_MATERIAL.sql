SELECT 
    cd_estabelecimento
    , cd_tab_preco_mat
    , NULLIF(REGEXP_REPLACE(ds_tab_preco_mat,'[''"!/:@;]', ''),'') AS ds_tab_preco_mat 
    , ie_situacao
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
    , ie_atualiza_nf
    , TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') AS dt_atualizacao_nrec
    , ie_ultima_compra
    , ie_hosp_pls
    , cd_operacao_nf
    , ie_ordem_compra 
FROM tasy.tabela_preco_material