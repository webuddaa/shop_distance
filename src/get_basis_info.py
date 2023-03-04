import json
import requests
import pandas as pd
import re
from loguru import logger
import argparse
from datetime import datetime

from src.future_k_lines import get_k_lines
from src.message_utils import send_wechat_msg


def convert_symbol(temp_symbol: str):
    if not isinstance(temp_symbol, str):
        return
    temp_symbol2 = temp_symbol.upper()
    a1 = ''.join(re.findall(r'[A-Za-z]', temp_symbol2))
    a2 = temp_symbol2.split(a1)[1]
    return f"{a1}2{a2}" if len(a2) == 3 else f"{a1}{a2}"


def extract_symbol(x):
    if "(" in x:
        return x.split("(")[1].split(")")[0]
    return


def fun(x):
    if "万分之" in x:
        tmp = x.split('/万分之')[0]
        return "0" if tmp == "0" else f"万分之[{tmp}]"
    else:
        return x


def get_futures_basis_info(path):
    """获取当天可以交易的品种"""
    url = "https://www.9qihuo.com/qihuoshouxufei"
    r = requests.get(url)
    temp_df = pd.read_html(r.text)[0]

    temp_df2 = temp_df.iloc[:, [0, 1, 3, 5, 6, 7, 8]]
    temp_df2["temp_symbol"] = temp_df2[0].apply(extract_symbol)
    temp_df2["new_symbol"] = temp_df2["temp_symbol"].apply(convert_symbol)
    temp_df3 = temp_df2.dropna(subset=["new_symbol"])
    temp_df3.columns = ["-", "现价", "交易所保证金", "每手保证金", "手续费-开仓", "手续费-平昨", "手续费-平今", "temp_symbol", "合约代码"]
    temp_df3["手续费-开仓"] = temp_df3["手续费-开仓"].apply(fun)
    temp_df3["手续费-平昨"] = temp_df3["手续费-平昨"].apply(fun)
    temp_df3["手续费-平今"] = temp_df3["手续费-平今"].apply(fun)
    temp_df3["交易所保证金"] = temp_df3["交易所保证金"].apply(lambda x: float(x.split("%")[0]))
    temp_df3["每手保证金"] = temp_df3["每手保证金"].apply(lambda x: float(x.split("元")[0]))
    temp_df3["合约品种"] = temp_df3["合约代码"].apply(lambda x: ''.join(re.findall(r'[A-Za-z]', x)))
    temp_df3["现价"] = temp_df3["现价"].apply(float)
    temp_df4 = temp_df3[["合约品种", "合约代码", "交易所保证金", "手续费-开仓", "手续费-平昨", "手续费-平今", "现价", "每手保证金"]].reset_index(drop=True)

    # 可以夜盘交易的品种
    NIGHT_FUTURE_SYMBOLS = ["BU", "FU", "HC", "RB", "C", "CS", "EB", "EG", "L", "PP", "V", "CF", "CY", "FG", "MA", "PF", "SA", "SR"]
    temp_df5 = temp_df4[(temp_df4["合约品种"].isin(NIGHT_FUTURE_SYMBOLS)) & (temp_df4["每手保证金"] < 9000)]

    dt = datetime.now()
    if dt.day <= 15:
        # 只剔除当前月份
        temp_list = [f"{dt.month:02d}"]
    else:
        # 需要剔除当前月份和下个月
        temp_list = [f"{dt.month:02d}", f"{dt.month + 1:02d}"]

    temp_symbol_list = list(temp_df5["合约代码"].unique())

    result = []
    for symbol in temp_symbol_list:
        for m in temp_list:
            if symbol.endswith(m):
                result.append(symbol)

    final_symbol_list = list(set(temp_symbol_list) - set(result))

    final_symbol_list2 = []
    for symbol in final_symbol_list:
        temp_df = get_k_lines(symbol, "day")
        if temp_df.shape[0] < 200:
            continue

        val = temp_df.iloc[-5:]["Volume"].mean()
        if val > 10000:
            final_symbol_list2.append(symbol)

    final_symbol_list3 = sorted(final_symbol_list2)
    with open(f"{path}/data/tmp.txt", "w") as f:
        f.write(json.dumps(final_symbol_list3))

    send_wechat_msg(f"当天可以交易的合约有{len(final_symbol_list3)}个")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str)
    args = parser.parse_args()
    try:
        get_futures_basis_info(args.path)
    except Exception as e:
        logger.exception(e)

