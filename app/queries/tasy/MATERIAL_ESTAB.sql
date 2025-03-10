SELECT 
	NR_SEQUENCIA
	, CD_ESTABELECIMENTO
	, CD_MATERIAL
    , TO_CHAR(DT_ATUALIZACAO, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO
	, IE_MATERIAL_ESTOQUE
    , to_char(QT_ESTOQUE_MINIMO) AS QT_ESTOQUE_MINIMO
    , to_char(QT_CONSUMO_MENSAL) AS QT_CONSUMO_MENSAL
	, CD_MATERIAL_CONTA
	, CD_KIT_MATERIAL
    , TO_CHAR(DT_ATUALIZACAO_NREC, 'YYYY-MM-DD hh24:mi:ss') AS DT_ATUALIZACAO_NREC
	, NR_REGISTRO_ANVISA
    , TO_CHAR(DT_VALIDADE_REG_ANVISA, 'YYYY-MM-DD hh24:mi:ss') AS DT_VALIDADE_REG_ANVISA
	, IE_UNID_CONSUMO_PRESCR
	, CD_UNIDADE_VENDA
    , to_char(QT_CONV_ESTOQUE_VENDA) AS QT_CONV_ESTOQUE_VENDA
	, CD_UNIDADE_MEDIDA_COMPRA
	, CD_UNIDADE_MEDIDA_CONSUMO
	, CD_UNIDADE_MEDIDA_ESTOQUE
    , to_char(QT_CONV_COMPRA_ESTOQUE) AS QT_CONV_COMPRA_ESTOQUE
    , to_char(QT_CONV_ESTOQUE_CONSUMO) AS QT_CONV_ESTOQUE_CONSUMO
	, IE_TIPO_CONSIGNADO
	, IE_TIPO_IMPOSTO
	, IE_VIGENTE_ANVISA
	, IE_REG_ANVISA_ISENTO
    , NULLIF(REGEXP_REPLACE(DS_MOTIVO_ISENCAO_ANVISA,'[''"!/:@;]', ''),'') AS DS_MOTIVO_ISENCAO_ANVISA 
FROM 
	TASY.MATERIAL_ESTAB