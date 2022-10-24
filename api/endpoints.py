from collections import Counter
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from flask import Blueprint, jsonify, request

from api.config import MONTH_ID as month_id
from api.query import *

pengeluaran_bp = Blueprint('pengeluaran', __name__)


def get_default_date(tgl_awal, tgl_akhir):
    if tgl_awal == None:
        tgl_awal = datetime.strptime((datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d'), '%Y-%m-%d')
    else:
        tgl_awal = datetime.strptime(tgl_awal, '%Y-%m-%d')

    if tgl_akhir == None:
        tgl_akhir = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
    else:
        tgl_akhir = datetime.strptime(tgl_akhir, '%Y-%m-%d')
    return tgl_awal, tgl_akhir


def get_date_prev(tgl_awal, tgl_akhir):
    tgl_awal = tgl_awal - relativedelta(months=1)
    tgl_awal = tgl_awal.strftime('%Y-%m-%d')
    tgl_akhir = tgl_akhir - relativedelta(months=1)
    tgl_akhir = tgl_akhir.strftime('%Y-%m-%d')
    return tgl_awal, tgl_akhir


def count_values(data, param):
    cnt = Counter()
    for i in range(len(data)):
        cnt[data[i][param]] += float(data[i]['total'])
    return cnt


@pengeluaran_bp.route('/pengeluaran/tren_pengeluaran')
def tren_pengeluaran():
    # Date Initialization
    tgl_awal = request.args.get('tgl_awal')
    tahun = datetime.now().year if tgl_awal == None else int(tgl_awal[:4])

    # Get query result
    result = query_tren_pengeluaran(tahun)

    # Initialization Trend Data
    tren = []
    for i in range(1, 13):
        tren.append({
            "month": month_id[i],
            "tahun_ini": 0,
            "tahun_sebelumnya": 0,
            "tahun_selanjutnya": 0,
            "persentase_tren": None,
            "persentase_predict": None
        })

    # Extract data outcome
    for row in result:
        curr_m = month_id[row['TglBKK'].month]
        for i in range(len(tren)):
            if row['TglBKK'].year == tahun and tren[i]['month'] == curr_m:
                tren[i]['tahun_ini'] = round(
                    tren[i]['tahun_ini'] + float(row['JmlBayar']), 2)
            else:
                if tren[i]['month'] == curr_m:
                    tren[i]['tahun_sebelumnya'] = round(
                        tren[i]['tahun_sebelumnya'] + float(row['JmlBayar']), 2)

            tren[i]['tahun_sebelumnya'] = round(
                    tren[i]['tahun_sebelumnya'] + float(0), 2)

    # Define trend percentage
    for i in range(len(tren)):
        if tren[i]['tahun_ini'] == 0 or tren[i]['tahun_sebelumnya'] == 0:
            tren[i]['persentase_tren'] = None
        else:
            tren[i]['persentase_tren'] = round(((tren[i]['tahun_ini'] - tren[i]['tahun_sebelumnya'])
                                                / tren[i]['tahun_sebelumnya']) * 100, 2)
        if tren[i]['tahun_ini'] == 0 or tren[i]['tahun_selanjutnya'] == 0:
            tren[i]['persentase_predict'] = None
        else:
            tren[i]['persentase_predict'] = round(((tren[i]['tahun_ini'] - tren[i]['tahun_selanjutnya'])
                                                / tren[i]['tahun_selanjutnya']) * 100, 2)

    # Define return result as a json
    data = {
        "judul": "Tren Pengeluaran",
        "label": 'Pengeluaran',
        "tahun": tahun,
        "data": tren
    }
    return jsonify(data)


@pengeluaran_bp.route('/pengeluaran/pengeluaran_instalasi')
def pengeluaran_instalasi():
    # Date Initialization
    tgl_awal = request.args.get('tgl_awal')
    tgl_akhir = request.args.get('tgl_akhir')
    tgl_awal, tgl_akhir = get_default_date(tgl_awal, tgl_akhir)
    tgl_awal_prev, tgl_akhir_prev = get_date_prev(tgl_awal, tgl_akhir)

    # Get query result
    result = query_pengeluaran_instalasi(tgl_awal, tgl_akhir + timedelta(days=1))
    result_prev = query_pengeluaran_instalasi(tgl_awal_prev, datetime.strptime(tgl_akhir_prev, '%Y-%m-%d') + timedelta(days=1))

    # Extract data by date (dict)
    tmp = [{"tanggal": row['TglBKK'], "instalasi": row['NamaInstalasi'], "total": row['JmlBayar']} for row in result]
    tmp_prev = [{"tanggal": row['TglBKK'], "instalasi": row['NamaInstalasi'], "total": row['JmlBayar']} for row in result_prev]

    # Extract data as (dataframe)
    cnts = count_values(tmp, 'instalasi')
    cnts_prev = count_values(tmp_prev, 'instalasi')
    data = [{"name": x, "value": round(y, 2)} for x, y in cnts.items()]
    data_prev = [{"name": x, "value": round(y, 2)} for x, y in cnts_prev.items()]

    # Define trend percentage
    for i in range(len(cnts)):
        percentage = None
        for j in range(len(cnts_prev)):
            if data[i]["name"] == data_prev[j]["name"]:
                percentage = (data[i]["value"] - data_prev[j]["value"]) / data[i]["value"]
            try:
                data[i]["trend"] = round(percentage, 3)
            except:
                data[i]["trend"] = percentage
        data[i]["predict"] = None

    # Define return result as a json
    result = {
        "judul": 'Pengeluaran Instalasi',
        "label": 'Pengeluaran',
        "data": data,
        "tgl_filter": {"tgl_awal": tgl_awal, "tgl_akhir": tgl_akhir}
    }
    return jsonify(result)


@pengeluaran_bp.route('/pengeluaran/pengeluaran_rekanan')
def pengeluaran_rekanan():
    # Date Initialization
    tgl_awal = request.args.get('tgl_awal')
    tahun = datetime.now().year if tgl_awal == None else int(tgl_awal[:4])

    # Get query result
    result = query_pengeluaran_rekanan(tahun)

    # Initialization Trend Data
    tren = []
    for i in range(1, 13):
        tren.append({
            "month": month_id[i],
            "klaim": 0,
            "pengajuan": 0,
            "klaim_prev": 0,
            "pengajuan_prev": 0,
            "klaim_next": 0,
            "pengajuan_next": 0,
            "klaim_tren": None,
            "klaim_predict": None,
            # "pengajuan_tren": None,
            # "pengajuan_predict": None
        })

    # Extract data
    for row in result:
        curr_m = month_id[row['TglStruk'].month]
        for i in range(len(tren)):
            if row['TglStruk'].year == tahun and tren[i]['month'] == curr_m:
                tren[i]['pengajuan'] = round(
                    tren[i]['pengajuan'] + float(row['Pengajuan']), 2)
                tren[i]['klaim'] = round(
                    tren[i]['klaim'] + float(row['Klaim']), 2)
            else:
                if tren[i]['month'] == curr_m:
                    tren[i]['pengajuan_prev'] = round(
                        tren[i]['pengajuan_prev'] + float(row['Pengajuan']), 2)
                    tren[i]['klaim_prev'] = round(
                        tren[i]['klaim_prev'] + float(row['Klaim']), 2)

            tren[i]['pengajuan_next'] = round(
                tren[i]['pengajuan_next'] + float(0), 2)
            tren[i]['klaim_next'] = round(
                tren[i]['klaim_next'] + float(0), 2)

    # Define trend percentage
    for i in range(len(tren)):
        if tren[i]['klaim'] == 0 or tren[i]['klaim_prev'] == 0:
            tren[i]['klaim_tren'] = None
        else:
            tren[i]['klaim_tren'] = round(((tren[i]['klaim'] - tren[i]['klaim_prev'])
                                                / tren[i]['klaim_prev']) * 100, 2)
        if tren[i]['klaim'] == 0 or tren[i]['klaim_next'] == 0:
            tren[i]['klaim_predict'] = None
        else:
            tren[i]['klaim_predict'] = round(((tren[i]['klaim'] - tren[i]['klaim_next'])
                                                / tren[i]['klaim_next']) * 100, 2)    
    
    # Define return result as a json
    data = {
        "judul": "Pengeluaran Rekanan",
        "label": 'Pengeluaran',
        "tahun": tahun,
        "data": tren
    }
    return jsonify(data)


@pengeluaran_bp.route('/pengeluaran/pengeluaran_produk')
def pengeluaran_produk():
    return jsonify({'response': 'ini data pengeluaran produk'})


@pengeluaran_bp.route('/pengeluaran/pengeluaran_cara_bayar')
def pengeluaran_cara_bayar():
    # Date Initialization
    tgl_awal = request.args.get('tgl_awal')
    tgl_akhir = request.args.get('tgl_akhir')
    tgl_awal, tgl_akhir = get_default_date(tgl_awal, tgl_akhir)
    tgl_awal_prev, tgl_akhir_prev = get_date_prev(tgl_awal, tgl_akhir)

    # Get query result
    result = query_pengeluaran_cara_bayar(tgl_awal, tgl_akhir + timedelta(days=1))
    result_prev = query_pengeluaran_cara_bayar(tgl_awal_prev, datetime.strptime(tgl_akhir_prev, '%Y-%m-%d') + timedelta(days=1))

    # Extract data by date (dict)
    tmp = [{"tanggal": row['TglBKK'], "cara_bayar": row['CaraBayar'], "total": row['JmlBayar']} for row in result]
    tmp_prev = [{"tanggal": row['TglBKK'], "cara_bayar": row['CaraBayar'], "total": row['JmlBayar']} for row in result_prev]

    # Extract data as (dataframe)
    cnts = count_values(tmp, 'cara_bayar')
    cnts_prev = count_values(tmp_prev, 'cara_bayar')
    data = [{"name": x, "value": round(y, 2)} for x, y in cnts.items()]
    data_prev = [{"name": x, "value": round(y, 2)} for x, y in cnts_prev.items()]

    # Define trend percentage
    for i in range(len(cnts)):
        percentage = None
        for j in range(len(cnts_prev)):
            if data[i]["name"] == data_prev[j]["name"]:
                percentage = (data[i]["value"] - data_prev[j]["value"]) / data[i]["value"]
            try:
                data[i]["trend"] = round(percentage, 3)
            except:
                data[i]["trend"] = percentage
        data[i]["predict"] = None

    # Define return result as a json
    result = {
        "judul": 'Pengeluaran Cara Bayar',
        "label": 'Pengeluaran',
        "data": data,
        "tgl_filter": {"tgl_awal": tgl_awal, "tgl_akhir": tgl_akhir}
    }
    return jsonify(result)
