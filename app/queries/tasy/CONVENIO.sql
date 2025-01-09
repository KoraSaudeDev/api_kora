SELECT 
	CD_CONVENIO
	, NULLIF(REGEXP_REPLACE(DS_CONVENIO,'[''"!/:@;]', ''),'') AS DS_CONVENIO  
    , TO_CHAR(DT_INCLUSAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_INCLUSAO
	, IE_TIPO_CONVENIO
	, IE_SITUACAO
	, CD_CGC
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
    , TO_CHAR(DT_ATUALIZACAO_NREC, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO_NREC
	-- new
	, IE_ORIGEM_PRECO
	, IE_PRECEDENCIA_PRECO
FROM
    TASY.CONVENIO