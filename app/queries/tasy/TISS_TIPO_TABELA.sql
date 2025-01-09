SELECT 
	NR_SEQUENCIA
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
    , TO_CHAR(DT_ATUALIZACAO_NREC, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO_NREC
	, CD_TABELA_RELAT
	, CD_TABELA_XML
    , NULLIF(REGEXP_REPLACE(DS_TABELA,'[''"!/:@;]', ''),'') AS DS_TABELA 
	, IE_VERSAO_TISS 
FROM
    TASY.TISS_TIPO_TABELA