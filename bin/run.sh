cd /data/Projects/shop_distance

nohup /data/anaconda3/bin/python -m src.ample_temp --period $1 --path /data/Projects/shop_distance > /data/Projects/shop_distance/bin/period_$1.log 2>&1 &