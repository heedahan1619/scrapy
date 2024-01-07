import pandas as pd
import numpy as np

import json
from collections import OrderedDict
from collections import defaultdict


category_json = OrderedDict()

df = pd.read_csv("crawler_news/preprocess/category.csv")
df = pd.DataFrame(df)

df_index = df.iloc[1:65, :2]
df_col = df.iloc[1:65, 4:]
df_new = pd.concat([df_index, df_col], axis=1)


for i in range(len(df_new.index)):
    check = df_new.iloc[i,0]
    if check is np.nan:
        df_new.iloc[i,0] = big_cat
    else:
        big_cat = check
df_new.rename(columns={"핀인사이트(=네이버)":"category", "Unnamed: 1":"category_sub"}, inplace=True)
print(f"news columns : {list(df_new.columns[2:])}")

start_colidx, end_colidx = map(int, input("범위를 입력해주세요(띄어쓰기로 구분, 1부터 25까지) : ").split())   # 범위 숫자로 입력(1부터)
df_mine = df_new.loc[:, ["category", "category_sub"]]
df_mine = pd.concat([df_mine, df_new.iloc[:, start_colidx+1:end_colidx+2]], axis=1)


for x in range(2, len(df_mine.columns)):

    cat_match = defaultdict(dict)
    cat_sub = None

    for i in range(len(df_mine.index)):
        fin_cat = df_mine.iloc[i,0]
        fin_cat_sub = df_mine.iloc[i,1]
        if fin_cat_sub is np.nan:
            fin_cat_sub = ""

        if df_mine.iloc[i, x] is not np.nan:
            categories = df_mine.iloc[i, x].replace(" ", "")
            categories = categories.replace("/", "·")
            categories = categories.split("\n")

            for j in categories:   # 많아봐야 2~3번이라 그냥 삼중반복문 함...
                divide_category = j.split("-")
                cat = divide_category[0]
                if len(divide_category)>1:
                    cat_sub = divide_category[1].split(",")
                    cat_sub = [sub.replace(".", ", ") for sub in cat_sub]
                else:
                    cat_match[cat].update({"all" : (fin_cat, fin_cat_sub)})
                
                while cat_sub:
                    cat_match[cat].update({cat_sub.pop(0) : (fin_cat, fin_cat_sub)})

    news_name = df_mine.columns[x]
    category_json[news_name] = cat_match



with open("crawler_news/preprocess/news_category.json", "w", encoding="utf-8") as make_file:
    json.dump(category_json, make_file, ensure_ascii=False, indent="\t")

print("Created news_category.json")