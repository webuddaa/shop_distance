import pandas as pd
import requests
import json
from loguru import logger
import argparse

from src.future_k_lines import get_k_lines


def cal_macd(data: pd.DataFrame, short_length=12, long_length=26, mid_length=9) -> pd.DataFrame:
    exp1 = data["Close"].ewm(span=short_length, adjust=False).mean()
    exp2 = data["Close"].ewm(span=long_length, adjust=False).mean()

    data["Diff"] = exp1 - exp2  # 白线
    data["Dea"] = data["Diff"].ewm(span=mid_length, adjust=False).mean()  # 黄线
    data["Macd"] = (data["Diff"] - data["Dea"]) * 2  # 红绿柱

    return data


def process_dataset(temp_df):
    """剔除指标钝化的数据"""
    temp_df["target"] = temp_df["Macd"].apply(lambda x: 1 if x >= 0 else -1)
    temp_df["target2"] = temp_df["target"].shift(1)  # 向下移动1个单位
    temp_df["macd_abs"] = temp_df["Macd"].apply(abs)
    temp_df["my_date"] = temp_df.apply(lambda row: row["Date"] if row["target"] + row["target2"] == 0 else None, axis=1)
    temp_df = temp_df.fillna(method="ffill")  # 用缺失值前面的一个值代替缺失值
    temp_df = temp_df.dropna()

    temp_df2 = temp_df.groupby("my_date", as_index=False).agg(macd_cnt=("Macd", "count"))
    date_list = list(temp_df2.iloc[:-1][temp_df2["macd_cnt"] == 1]["my_date"])
    if len(date_list) == 0:
        return temp_df[["Date", "Open", "High", "Low", "Close", "Volume", "Diff", "Dea", "Macd"]]
    res_df = temp_df[~temp_df["Date"].isin(date_list)]
    return res_df[["Date", "Open", "High", "Low", "Close", "Volume", "Diff", "Dea", "Macd"]]


def cal_extreme_point(macd_sum, price_highest, later_price_highest, price_lowest, later_price_lowest):
    if macd_sum > 0:
        return max(price_highest, later_price_highest)
    else:
        return min(price_lowest, later_price_lowest)


def merge_macd(temp_df):
    temp_df["target"] = temp_df["Macd"].apply(lambda x: 1 if x >= 0 else -1)
    temp_df["target2"] = temp_df["target"].shift(1)  # 向下移动1个单位
    temp_df["macd_abs"] = temp_df["Macd"].apply(abs)
    temp_df["my_date"] = temp_df.apply(lambda row: row["Date"] if row["target"] + row["target2"] == 0 else None, axis=1)
    temp_df = temp_df.fillna(method="ffill")  # 用缺失值前面的一个值代替缺失值
    temp_df = temp_df.dropna()

    temp_df2 = temp_df.groupby("my_date", as_index=False).agg(
        macd_sum=("Macd", "sum"),
        macd_cnt=("Macd", "count"),
        macd_abs_sum=("macd_abs", "sum"),
        macd_abs_max=("macd_abs", "max"),
        macd_abs_min=("macd_abs", "min"),
        diff_max=("Diff", "max"),
        diff_min=("Diff", "min"),
        price_highest=("High", "max"),
        price_lowest=("Low", "min")
    ).reset_index(drop=True)

    temp_df2["later_price_lowest"] = temp_df2["price_lowest"].shift(-1)
    temp_df2["later_price_highest"] = temp_df2["price_highest"].shift(-1)
    temp_df3 = temp_df2.fillna({"later_price_lowest": 9999999, "later_price_highest": 0})
    temp_df3["extreme_point"] = temp_df3.apply(
        lambda row: cal_extreme_point(row["macd_sum"], row["price_highest"], row["later_price_highest"],
                                      row["price_lowest"], row["later_price_lowest"]), axis=1)
    temp_df4 = temp_df3.drop(["price_highest", "price_lowest", "later_price_lowest", "later_price_highest"], axis=1)
    return temp_df4


def bottom_divergence(temp_df, now_price) -> bool:
    """底背驰"""
    prev_low_price = float(temp_df.iloc[-3]["extreme_point"])
    prev_high_price = float(temp_df.iloc[-2]["extreme_point"])

    prev_high_diff = float(temp_df.iloc[-2]["diff_max"])
    prev_low_diff = float(temp_df.iloc[-3]["diff_min"])
    now_low_diff = float(temp_df.iloc[-1]["diff_min"])

    ratio_1 = (prev_high_diff - prev_low_diff) / abs(prev_low_diff)
    ratio_2 = (prev_high_diff - now_low_diff) / (prev_high_diff - prev_low_diff)

    target_0 = temp_df.iloc[-1]["macd_sum"] < 0
    target_1 = temp_df.iloc[-1]["macd_abs_sum"] * 2 < temp_df.iloc[-3]["macd_abs_sum"]
    target_2 = ratio_2 < 0.8
    target_3 = 0.8 < ratio_1 < 1.2
    target_4 = (prev_high_price - now_price) / (prev_high_price - prev_low_price) > 0.9
    final_target = target_0 and target_1 and target_2 and target_3 and target_4

    target_5 = temp_df.iloc[-1]["macd_abs_sum"] * 2 < temp_df.iloc[-3]["macd_abs_sum"] < temp_df.iloc[-5]["macd_abs_sum"]
    target_6 = 0 > temp_df.iloc[-1]["diff_min"] > temp_df.iloc[-3]["diff_min"] > temp_df.iloc[-5]["diff_min"]
    final_target2 = target_0 and target_5 and target_6
    
    return final_target or final_target2


def peak_divergence(temp_df, now_price) -> bool:
    """
    顶背驰
    """
    prev_low_price = float(temp_df.iloc[-2]["extreme_point"])
    prev_high_price = float(temp_df.iloc[-3]["extreme_point"])

    prev_low_diff = float(temp_df.iloc[-2]["diff_min"])
    prev_high_diff = float(temp_df.iloc[-3]["diff_max"])
    now_high_diff = float(temp_df.iloc[-1]["diff_max"])

    ratio_1 = (prev_high_diff - prev_low_diff) / abs(prev_high_diff)
    ratio_2 = (now_high_diff - prev_low_diff) / (prev_high_diff - prev_low_diff)

    target_0 = temp_df.iloc[-1]["macd_sum"] > 0
    target_1 = temp_df.iloc[-1]["macd_abs_sum"] * 2 < temp_df.iloc[-3]["macd_abs_sum"]
    target_2 = ratio_2 < 0.8
    target_3 = 0.8 < ratio_1 < 1.2
    target_4 = (now_price - prev_low_price) / (prev_high_price - prev_low_price) > 0.9

    final_target = target_0 and target_1 and target_2 and target_3 and target_4
    
    target_5 = temp_df.iloc[-1]["macd_abs_sum"] * 2 < temp_df.iloc[-3]["macd_abs_sum"] < temp_df.iloc[-5]["macd_abs_sum"]
    target_6 = 0 < temp_df.iloc[-1]["diff_max"] < temp_df.iloc[-3]["diff_max"] < temp_df.iloc[-5]["diff_max"]
    final_target2 = target_0 and target_5 and target_6
    
    return final_target or final_target2


def cal_result(temp_df) -> str:
    """
    ["Date", "Open", "High", "Low", "Close", "Volume", "Diff", "Dea", "Macd"]
    """
    now_price = float(temp_df.iloc[-1]["Close"])
    df1 = process_dataset(temp_df)
    df2 = merge_macd(df1)

    if bottom_divergence(df2, now_price):
        return "bottom"
    elif peak_divergence(df2, now_price):
        return "peak"
    else:
        return "no"


def send_wechat_msg(content_text):
    """
    发送消息到企业微信群中
    """
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8165d8d4-591f-4862-be01-3f4281d2da39"
    headers = {"Content-Type": "application/json;charset=utf-8"}

    msg = {
        "msgtype": "text",
        "text": {"content": content_text, "mentioned_list": []}
    }
    try:
        requests.post(url, data=json.dumps(msg), headers=headers)
    except Exception as e:
        logger.info(f"send wechat fail, error info: {e}")


def get_symbol_list(path):
    with open(f"{path}/data/tmp.txt", "r") as f:
        temp_str = f.read()
    return json.loads(temp_str)


def fun(period: str, all_symbols: list):
    result_peak = []
    result_bottom = []

    for symbol in all_symbols:
        temp_df = get_k_lines(symbol, period)
        if temp_df.shape[0] < 200:
            continue

        temp_df2 = cal_macd(temp_df)
        temp_type = cal_result(temp_df2)
        if temp_type == "no":
            continue
        elif temp_type == "bottom":
            result_bottom.append(symbol)
        else:
            result_peak.append(symbol)
    return result_peak, result_bottom


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', type=str)
    parser.add_argument('--path', type=str)
    args = parser.parse_args()

    all_symbol_list = get_symbol_list(args.path)

    p = args.period
    while True:
        result_peak, result_bottom = fun(p, all_symbol_list)

        if len(result_peak) > 0 or len(result_bottom) > 0:
            content = f"级别: {p} || 做多: {result_bottom} || 做空: {result_peak}"
            send_wechat_msg(content)

