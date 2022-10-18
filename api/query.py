from sqlalchemy import text

from api.config import get_connection

engine = get_connection()


def query_tren_pengeluaran(tahun):
    result = engine.execute(
        text(f"""SELECT sbkk.TglBKK, sbkk.JmlBayar
            FROM rsudtasikmalaya.dbo.StrukBuktiKasKeluar sbkk
            WHERE datepart(year,[TglBKK]) = {tahun-1}
            OR datepart(year,[TglBKK]) = {tahun}
            ORDER BY sbkk.TglBKK ASC;"""))
    return result


def query_pengeluaran_instalasi(start_date, end_date):
    result = engine.execute(
        text(f"""SELECT sbkk.TglBKK, i.NamaInstalasi, sbkk.JmlBayar
           FROM rsudtasikmalaya.dbo.StrukBuktiKasKeluar sbkk
           INNER JOIN rsudtasikmalaya.dbo.Ruangan r
           ON sbkk.KdRuangan = r.KdRuangan
           INNER JOIN rsudtasikmalaya.dbo.Instalasi i
           ON r.KdInstalasi = i.KdInstalasi
           WHERE sbkk.TglBKK >= '{start_date}'
           AND sbkk.TglBKK < '{end_date}'
           ORDER BY sbkk.TglBKK ASC;"""))
    return result


def query_pengeluaran_rekanan(tahun):
    result = engine.execute(
        text(f"""SELECT spp.TglStruk, spp.IdPenjamin, p.NamaPenjamin, 
            spp.TotalBiaya as Pengajuan, JmlHutangPenjamin as Klaim
            FROM rsudtasikmalaya.dbo.StrukPelayananPasien spp
            INNER JOIN rsudtasikmalaya.dbo.Penjamin p
            ON spp.IdPenjamin = p.IdPenjamin
            WHERE spp.IdPenjamin != 2222222222
            AND datepart(year,[TglStruk]) = {tahun-1}
            OR datepart(year,[TglStruk]) = {tahun}
            ORDER BY spp.TglStruk ASC;"""))
    return result


def query_pengeluaran_cara_bayar(start_date, end_date):
    result = engine.execute(
        text(f"""SELECT sbkk.TglBKK, cb.CaraBayar, sbkk.JmlBayar
            FROM dbo.StrukBuktiKasKeluar sbkk
            INNER JOIN dbo.CaraBayar cb
            ON sbkk.KdCaraBayar = cb.KdCaraBayar
            WHERE sbkk.TglBKK >= '{start_date}'
            AND sbkk.TglBKK < '{end_date}'
            ORDER BY sbkk.TglBKK ASC;"""))
    return result