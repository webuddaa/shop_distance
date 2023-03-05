import json
import argparse

from src.future_k_lines import get_k_lines
from src.message_utils import send_wechat_msg
from src.process_data import cal_macd, cal_result


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
    parser.add_argument('--period', type=str, default=None)
    parser.add_argument('--period_list', type=json.loads, default=None)
    parser.add_argument('--path', type=str)
    parser.add_argument('--is_circle', type=str, default="true")
    args = parser.parse_args()

    all_symbol_list = get_symbol_list(args.path)

    if args.period and args.is_circle == "true":
        p = args.period
        while True:
            result_peak, result_bottom = fun(p, all_symbol_list)

            if len(result_peak) > 0 or len(result_bottom) > 0:
                content = f"级别: {p} || 做多: {result_bottom} || 做空: {result_peak}"
                send_wechat_msg(content)

    if args.period and args.is_circle == "false":
        p = args.period
        result_peak, result_bottom = fun(p, all_symbol_list)

        if len(result_peak) > 0 or len(result_bottom) > 0:
            content = f"级别: {p} || 做多: {result_bottom} || 做空: {result_peak}"
            send_wechat_msg(content)

    if args.period_list and args.is_circle == "true":
        while True:
            for p in args.period_list:
                result_peak, result_bottom = fun(p, all_symbol_list)

                if len(result_peak) > 0 or len(result_bottom) > 0:
                    content = f"级别: {p} || 做多: {result_bottom} || 做空: {result_peak}"
                    send_wechat_msg(content)

    if args.period_list and args.is_circle == "false":
        for p in args.period_list:
            result_peak, result_bottom = fun(p, all_symbol_list)

            if len(result_peak) > 0 or len(result_bottom) > 0:
                content = f"级别: {p} || 做多: {result_bottom} || 做空: {result_peak}"
                send_wechat_msg(content)
