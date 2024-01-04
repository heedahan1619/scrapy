media_category_dict = {}


# matching_dict = {}

# category_list = []
# category_sub_list = []
# media_category_list = []
# media_category_sub_list = []

# 주어진 데이터프레임을 순회하면서 딕셔너리에 값 추가
for idx, row in df.iterrows():
    # print(idx,"\n", row)
    
    """기존 언론사 카테고리 추출"""

    # 기존 언론사 순회
    for origin_media in list(df.columns)[:4]:

        origin_row = row[f"{origin_media}"]
        origin_name = origin_media.split(" ")[0] # 기존 언론사 이름 추출
        
        # 기존 언론사 리스트 및 딕셔너리 동적 생성 
        media_list_name = f"{origin_name}_list"

        if "핀인사이트" in origin_media: # 핀인사이트
            if media_list_name not in media_category_dict:
                media_category_dict[media_list_name] = {"category":[], "category_sub":[]}
            if "sub" not in origin_media: # category
                media_category_dict[media_list_name]["category"].append(origin_row)
            else: # category_sub
                media_category_dict[media_list_name]["category_sub"].append(origin_row)
        else: # 네이트
            if media_list_name not in media_category_dict:
                media_category_dict[media_list_name] = {"media_category":[], "media_category_sub":[]}
            if "sub" not in origin_media: # media_category
                # media_category = origin_row
                media_category_dict[media_list_name]["media_category"].append(origin_row)
            else: # media_category_sub
                if origin_row == "-":
                    origin_row = ""                   
                # media_category_sub = origin_row
                media_category_dict[media_list_name]["media_category_sub"].append(origin_row)
    
    """신규 언론사 카테고리 추출"""

    # 신규 언론사 순회
    for new_media in list(df.columns)[4:]:
        
        # 신규 언론사의 카테고리 추출
        new_row = row[f"{new_media}"]
         
        # 신규 언론사 리스트 및 딕셔너리 동적 생성 
        media_list_name = f"{new_media}_list"
        if media_list_name not in media_category_dict:
            media_category_dict[media_list_name] = {"media_category":[], "media_category_sub":[]}
        else:    
            split_enter = new_row.split("\n") # 줄바꿈으로 분리

            for i in range(len(split_enter)):
                
                split_dash = split_enter[i].split("-")
                
                if "-" not in split_enter[i]:
                    media_category = split_enter[i]
                    media_category_sub = media_category
                else:
                    media_category = split_dash[0]        
                
                    if "," not in split_dash[1]:
                        media_category_sub = split_dash[1]
                    else:
                        split_comma = split_dash[1].split(",")
                        
                        if split_dash[1][-1] == ",":
                            split_dash[1] = split_dash[1][:-1]
                        else:
                            for j in range(len(split_comma)):
                                media_category_sub = split_comma[j]
                                
                media_category_dict[media_list_name]["media_category"].append(media_category)
                media_category_dict[media_list_name]["media_category_sub"].append(media_category_sub)  
                    
# 딕셔너리에서 필요한 항목 추출하기
for media_list, categories in media_category_dict.items():
    media = media_list.split("_")[0]
    print(f"언론사: {media}")  
    
    try:
        print(categories["category"])
        print(categories["category_sub"])
    except:
        print(categories["media_category"])
        print(categories["media_category_sub"])
        
for media_list, categories in media_category_dict.items():
    if media_list == "핀인사이트_list":
        print(media_list, len(categories["category"]), len(categories["category_sub"]))
    else:
        print(media_list, len(categories["media_category"]), len(categories["media_category_sub"]))