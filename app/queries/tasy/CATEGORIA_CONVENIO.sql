SELECT
	nr_seq_regra_acomp
	, REGEXP_REPLACE(cd_categoria,'[''"!/:@;]', '') as cd_categoria
	, REGEXP_REPLACE(cd_integracao,'[''"!/:@;]', '') as cd_integracao
	, REGEXP_REPLACE(cd_plano_padrao,'[''"!/:@;]', '') as cd_plano_padrao
	, REGEXP_REPLACE(ds_categoria,'[''"!/:@;]', '') as ds_categoria
	, REGEXP_REPLACE(ds_reduzida,'[''"!/:@;]', '') as ds_reduzida
	, REGEXP_REPLACE(ds_senha_web,'[''"!/:@;]', '') as ds_senha_web
	, REGEXP_REPLACE(ie_empresa,'[''"!/:@;]', '') as ie_empresa
	, REGEXP_REPLACE(ie_idade_dieta,'[''"!/:@;]', '') as ie_idade_dieta
	, REGEXP_REPLACE(ie_ident_atend,'[''"!/:@;]', '') as ie_ident_atend
	, REGEXP_REPLACE(ie_lib_dieta,'[''"!/:@;]', '') as ie_lib_dieta
	, REGEXP_REPLACE(ie_permite_gerar_pacote,'[''"!/:@;]', '') as ie_permite_gerar_pacote
	, REGEXP_REPLACE(ie_preco_custo,'[''"!/:@;]', '') as ie_preco_custo
	, REGEXP_REPLACE(ie_situacao,'[''"!/:@;]', '') as ie_situacao
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, cd_convenio
	, cd_tipo_acomodacao
	, nr_acompanhante
	, nr_seq_apresentacao
	, qt_dieta_acomp
	, qt_idade_maiores
	, qt_idade_menores
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
FROM
	TASY.CATEGORIA_CONVENIO