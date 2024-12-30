SELECT
        Produto.Cd_Produto AS cd_produto,
        Produto.Ds_Produto AS ds_produto,
        SUM(Est_Pro.Qt_Estoque_Atual) / COALESCE(
            (SELECT
                uni_pro.vl_fator
            FROM
                dbamv.uni_pro
            WHERE
                uni_pro.cd_produto = Produto.Cd_Produto
                AND uni_pro.sn_ativo = 'S'
            FETCH FIRST 1 ROW ONLY
            ),
            1
        ) AS Qt_Estoque_Atual,
        (SELECT
            uni_pro.ds_unidade
        FROM
            dbamv.uni_pro
        WHERE
            uni_pro.cd_produto = Produto.Cd_Produto
            AND uni_pro.sn_ativo = 'S'
        FETCH FIRST 1 ROW ONLY
        ) AS Ds_Unidade
    FROM
        Dbamv.Est_Pro,
        Dbamv.Produto,
        Dbamv.Empresa_Produto,
        (
            SELECT DISTINCT
                i.cd_produto
            FROM
                dbamv.mvto_estoque,
                dbamv.itmvto_estoque i,
                dbamv.estoque e
            WHERE
                mvto_estoque.cd_mvto_estoque = i.cd_mvto_estoque
                AND mvto_estoque.cd_estoque = e.cd_estoque
                AND mvto_estoque.Dt_Mvto_Estoque BETWEEN TO_DATE(:P_DATA_INI, 'dd/mm/yyyy hh24:mi:ss')
                AND TO_DATE(:P_DATA_FIM, 'dd/mm/yyyy hh24:mi:ss')
        ) mvto
    WHERE
        Produto.Sn_Mestre = 'N'
        AND Empresa_Produto.Cd_Produto = Produto.Cd_Produto
        AND Est_Pro.Cd_Produto = Produto.Cd_Produto
        AND Produto.Cd_Produto = mvto.cd_produto
    GROUP BY
        Produto.Cd_Produto,
        Produto.Ds_Produto
    ORDER BY
        Produto.Cd_Produto,
        Produto.Ds_Produto