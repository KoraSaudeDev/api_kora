SELECT 
    nr_sequencia
    ,nr_seq_regra
    ,TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') AS dt_atualizacao
    ,TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') AS dt_atualizacao_nrec
    , to_char(vl_inicial) AS vl_inicial
    , to_char(vl_final) AS vl_final
    , to_char(tx_ajuste) AS tx_ajuste
    ,ie_origem_preco 
FROM tasy.regra_ajuste_indice_dif