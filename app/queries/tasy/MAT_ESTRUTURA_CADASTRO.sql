SELECT nr_sequencia
    , nr_seq_estrutura
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
    , TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao_nrec
    , cd_material 
FROM tasy.mat_estrutura_cadastro