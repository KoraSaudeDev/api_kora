SELECT
	REGEXP_REPLACE(cd_categoria,'[''"!/:@;]', '') as cd_categoria
	, REGEXP_REPLACE(ie_dividir_indice_pfb,'[''"!/:@;]', '') as ie_dividir_indice_pfb
	, REGEXP_REPLACE(ie_dividir_indice_pmc,'[''"!/:@;]', '') as ie_dividir_indice_pmc
	, REGEXP_REPLACE(ie_primeira_versao,'[''"!/:@;]', '') as ie_primeira_versao
	, REGEXP_REPLACE(ie_situacao,'[''"!/:@;]', '') as ie_situacao
	, REGEXP_REPLACE(ie_tipo_material,'[''"!/:@;]', '') as ie_tipo_material
	, REGEXP_REPLACE(ie_tipo_preco,'[''"!/:@;]', '') as ie_tipo_preco
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, REGEXP_REPLACE(nm_usuario_nrec,'[''"!/:@;]', '') as nm_usuario_nrec
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao_nrec
	, TO_CHAR(dt_base_fixo, 'YYYY-MM-DD hh24:mi:ss') as dt_base_fixo
	, TO_CHAR(dt_final_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_final_vigencia
	, TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia
	, TO_CHAR(cd_classe_material) as cd_classe_material
	, TO_CHAR(cd_convenio) as cd_convenio
	, TO_CHAR(cd_estabelecimento) as cd_estabelecimento
	, TO_CHAR(cd_grupo_material) as cd_grupo_material
	, TO_CHAR(cd_subgrupo_material) as cd_subgrupo_material
	, TO_CHAR(ie_prioridade) as ie_prioridade
	, TO_CHAR(nr_sequencia) as nr_sequencia
	, TO_CHAR(qt_dia_fixo) as qt_dia_fixo
	, TO_CHAR(tx_pfb_neg) as tx_pfb_neg
	, TO_CHAR(tx_pfb_pos) as tx_pfb_pos
	, TO_CHAR(tx_pmc) as tx_pmc
	, TO_CHAR(tx_pmc_neg) as tx_pmc_neg
	, TO_CHAR(tx_pmc_pos) as tx_pmc_pos
	, TO_CHAR(tx_preco_fabrica) as tx_preco_fabrica
	, TO_CHAR(vl_maximo) as vl_maximo
	, TO_CHAR(vl_minimo) as vl_minimo
FROM
	TASY.CONVENIO_SIMPRO