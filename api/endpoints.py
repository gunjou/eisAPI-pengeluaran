from collections import Counter
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import text

from api.config import MONTH_ID as month_id
from api.config import get_connection


pengeluaran_bp = Blueprint('pengeluaran', __name__)
engine = get_connection()


def get_default_date(tgl_awal, tgl_akhir):
    if tgl_awal == None:
        tgl_awal = datetime.today() - relativedelta(months=1)
        tgl_awal = datetime.strptime(tgl_awal.strftime('%Y-%m-%d'), '%Y-%m-%d')
    else:
        tgl_awal = datetime.strptime(tgl_awal, '%Y-%m-%d')

    if tgl_akhir == None:
        tgl_akhir = datetime.strptime(
            datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
    else:
        tgl_akhir = datetime.strptime(tgl_akhir, '%Y-%m-%d')
    return tgl_awal, tgl_akhir


@pengeluaran_bp.route('/tren_pengeluaran')
def tren_pengeluaran():
    tgl_awal = request.args.get('tgl_awal')
    tahun = datetime.now().year if tgl_awal == None else int(tgl_awal[:4])
    result = engine.execute(
        text(
            f"""SELECT sbkk.TglBKK, sbkk.JmlBayar
            FROM rsudtasikmalaya.dbo.StrukBuktiKasKeluar sbkk
            WHERE datepart(year,[TglBKK]) = {tahun-1}
            OR datepart(year,[TglBKK]) = {tahun}
            ORDER BY sbkk.TglBKK ASC;"""))

    tren = {}
    for i in range(1, 13):
        tren[month_id[i]] = {
            "tahun_ini": 0,
            "tahun_sebelumnya": 0,
            "tahun_selanjutnya": 0,
            "persentase_tren": None,
            "persentase_predict": None
        }

    for row in result:
        curr_m = month_id[row['TglBKK'].month]
        if row['TglBKK'].year == tahun:
            tren[curr_m]['tahun_ini'] = round(
                tren[curr_m]['tahun_ini'] + float(row['JmlBayar']), 2)
        else:
            tren[curr_m]['tahun_sebelumnya'] = round(
                tren[curr_m]['tahun_sebelumnya'] + float(row['JmlBayar']), 2)
        tren[curr_m]['tahun_selanjutnya'] = round(
            tren[curr_m]['tahun_selanjutnya'] + float(0), 2)

    for i in range(1, 13):
        if tren[month_id[i]]['tahun_ini'] == 0 or tren[month_id[i]]['tahun_sebelumnya'] == 0:
            tren[month_id[i]]['persentase_tren'] = None
        else:
            tren[month_id[i]]['persentase_tren'] = round(((tren[month_id[i]]['tahun_ini'] - tren[month_id[i]]['tahun_sebelumnya'])
                                                          / tren[month_id[i]]['tahun_sebelumnya']) * 100, 2)
        if tren[month_id[i]]['tahun_ini'] == 0 or tren[month_id[i]]['tahun_selanjutnya'] == 0:
            tren[month_id[i]]['persentase_predict'] = None
        else:
            tren[month_id[i]]['persentase_predict'] = round(((tren[month_id[i]]['tahun_ini'] - tren[month_id[i]]['tahun_selanjutnya'])
                                                             / tren[month_id[i]]['tahun_selanjutnya']) * 100, 2)
    data = {
        "judul": "Tren Pengeluaran",
        "label": 'Pengeluaran',
        "tahun": tahun,
        "tren": tren
    }
    return jsonify(data)


@pengeluaran_bp.route('/pengeluaran_instalasi')
def pengeluaran_instalasi():
    tgl_awal = request.args.get('tgl_awal')
    tgl_akhir = request.args.get('tgl_akhir')
    tgl_awal, tgl_akhir = get_default_date(tgl_awal, tgl_akhir)
    result = engine.execute(
        text(
            f"""SELECT sbkk.TglBKK, i.NamaInstalasi, sbkk.JmlBayar
           FROM rsudtasikmalaya.dbo.StrukBuktiKasKeluar sbkk
           INNER JOIN rsudtasikmalaya.dbo.Ruangan r
           ON sbkk.KdRuangan = r.KdRuangan
           INNER JOIN rsudtasikmalaya.dbo.Instalasi i
           ON r.KdInstalasi = i.KdInstalasi
           WHERE sbkk.TglBKK >= '{tgl_awal}'
           AND sbkk.TglBKK < '{tgl_akhir + timedelta(days=1)}'
           ORDER BY sbkk.TglBKK ASC;"""))
    data = []
    for row in result:
        data.append({
            "tanggal": row['TglBKK'],
            "instalasi": row['NamaInstalasi'],
            "total": row['JmlBayar'],
            "judul": 'Pengeluaran Instalasi',
            "label": 'Pengeluaran'
        })
    cnt = Counter()
    for i in range(len(data)):
        cnt[data[i]['instalasi'].lower().replace(' ', '_')] += float(data[i]['total'])

    result = {
        "judul": 'Pengeluaran Instalasi',
        "label": 'Pengeluaran',
        "instalasi": cnt,
        "tgl_filter": {"tgl_awal": tgl_awal, "tgl_akhir": tgl_akhir}
    }
    return jsonify(result)


@pengeluaran_bp.route('/pengeluaran_rekanan')
def pengeluaran_rekanan():
    tgl_awal = request.args.get('tgl_awal')
    tahun = datetime.now().year if tgl_awal == None else int(tgl_awal[:4])
    result = engine.execute(
        text(
            f"""SELECT spp.TglStruk, spp.IdPenjamin, p.NamaPenjamin, 
            spp.TotalBiaya as Pengajuan, JmlHutangPenjamin as Klaim
            FROM rsudtasikmalaya.dbo.StrukPelayananPasien spp
            INNER JOIN rsudtasikmalaya.dbo.Penjamin p
            ON spp.IdPenjamin = p.IdPenjamin
            WHERE spp.IdPenjamin != 2222222222
            AND datepart(year,[TglStruk]) = {tahun-1}
            OR datepart(year,[TglStruk]) = {tahun}
            ORDER BY spp.TglStruk ASC;"""))

    tren = {}
    for i in range(1, 13):
        tren[month_id[i]] = {
            "pengajuan": 0,
            "klaim": 0,
        }

    for row in result:
        curr_m = month_id[row['TglStruk'].month]
        tren[curr_m]['pengajuan'] = round(tren[curr_m]['pengajuan'] + float(row['Pengajuan']), 2)
        tren[curr_m]['klaim'] = round(tren[curr_m]['klaim'] + float(row['Klaim']), 2)
        
    data = {
        "judul": "Pengeluaran Rekanan",
        "label": 'Pengeluaran',
        "tahun": tahun,
        "asuransi": tren
    }
    return jsonify(data)


@pengeluaran_bp.route('/pengeluaran_produk')
def pengeluaran_produk():
    return jsonify({'response': 'ini data pengeluaran produk'})


@pengeluaran_bp.route('/pengeluaran_cara_bayar')
def pengeluaran_cara_bayar():
    tgl_awal = request.args.get('tgl_awal')
    tgl_akhir = request.args.get('tgl_akhir')
    tgl_awal, tgl_akhir = get_default_date(tgl_awal, tgl_akhir)
    result = engine.execute(
        text(
            f"""SELECT sbkk.TglBKK, cb.CaraBayar, sbkk.JmlBayar
            FROM dbo.StrukBuktiKasKeluar sbkk
            INNER JOIN dbo.CaraBayar cb
            ON sbkk.KdCaraBayar = cb.KdCaraBayar
            WHERE sbkk.TglBKK >= '{tgl_awal}'
            AND sbkk.TglBKK < '{tgl_akhir + timedelta(days=1)}'
            ORDER BY sbkk.TglBKK ASC;"""))
    data = []
    for row in result:
        data.append({
            "tanggal": row['TglBKK'],
            "cara_bayar": row['CaraBayar'],
            "total": row['JmlBayar'],
            "judul": 'Pendapatan Cara Bayar',
            "label": 'Pendapatan'
        })
    cnt = Counter()
    for i in range(len(data)):
        cnt[data[i]['cara_bayar'].lower().replace(
            ' ', '_')] += float(data[i]['total'])

    result = {
        "judul": 'Pengeluaran Cara Bayar',
        "label": 'Pengeluaran',
        "cara_bayar": cnt,
        "tgl_filter": {"tgl_awal": tgl_awal, "tgl_akhir": tgl_akhir}
    }
    return jsonify(result)
