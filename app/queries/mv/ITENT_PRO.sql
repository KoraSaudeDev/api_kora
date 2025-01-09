SELECT
	ip.cd_itent_pro as cd_itent_pro,
	ip.cd_ent_pro as cd_ent_pro,
	ip.cd_produto as cd_produto,
	ip.cd_uni_pro as cd_uni_pro,
	to_char(ip.qt_entrada) as qt_entrada,
	to_char(ip.vl_custo_real) as vl_custo_real,
	to_char(ip.vl_total) as vl_total,
	to_char(ip.vl_unitario) as vl_unitario
FROM
	DBAMV.ITENT_PRO ip
WHERE
	CD_ENT_PRO IN (
		SELECT
			CD_ENT_PRO
		FROM
			DBAMV.ENT_PRO ep
		WHERE
			DT_ENTRADA >= TO_DATE('2019-01-01', 'YYYY-MM-DD')
	)