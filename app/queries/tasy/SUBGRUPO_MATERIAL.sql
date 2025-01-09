SELECT 
	CD_SUBGRUPO_MATERIAL
    , NULLIF(REGEXP_REPLACE(DS_SUBGRUPO_MATERIAL,'[''"!/:@;]', ''),'') AS DS_SUBGRUPO_MATERIAL 
	, CD_GRUPO_MATERIAL
	, IE_SITUACAO
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
FROM 
	TASY.SUBGRUPO_MATERIAL