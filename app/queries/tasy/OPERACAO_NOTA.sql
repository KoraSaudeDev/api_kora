SELECT 
	CD_OPERACAO_NF
    , NULLIF(REGEXP_REPLACE(DS_OPERACAO_NF,'[''"!/:@;]', ''),'') AS DS_OPERACAO_NF 
	, IE_TIPO_OPERACAO
	, IE_BAIXA_ESTOQUE
	, IE_OPERACAO_FISCAL
	, IE_SITUACAO
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
	, CD_OPERACAO_ESTOQUE
	, IE_CONTAS_PAGAR
	, CD_NATUREZA_OPERACAO
	, IE_EXIGE_ORDEM_COMPRA
    , TO_CHAR(DT_ATUALIZACAO_NREC, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO_NREC
	, IE_ULTIMA_COMPRA
	, IE_ATUALIZA_TAB_PRECO
FROM 
	TASY.OPERACAO_NOTA