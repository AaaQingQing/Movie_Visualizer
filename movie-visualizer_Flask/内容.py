import math

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def get_rating():  # 读取ratings中的评分信息
    f = open('ratings.csv')
    ratings = f.readlines()
    f.close()
    r = []
    ratings.pop(0)
    for line in ratings:
        rate = line.strip().split(',')
        r.append([int(rate[0]), int(rate[1]), float(rate[2])])
    movies = []
    for x in r:
        if x[1] not in movies:
            movies.append(x[1])
    m = len(movies)
    user_movie = np.zeros([671, m])
    for item in r:
        y = movies.index(item[1])
        user_movie[item[0] - 1, y] = item[2]  # 生成一个以用户为行，评分为列的矩阵
    return r


# 用户字典：user_rate[用户id]=[(电影id,电影评分)...]
# 电影字典：movie_user[电影id]=[用户id1,用户id2...]
def get_user(r):
    user_rate = {}
    user_movie = {}
    for i in r:
        user_rank = [i[1], i[2]]
        if i[0] in user_rate:
            user_rate[i[0]].append(user_rank)
        else:
            user_rate[i[0]] = [user_rank]
        if i[0] in user_movie:
            user_movie[i[0]].append(i[1])
        else:
            user_movie[i[0]] = [i[1]]
    return user_rate, user_movie


def get_movie_info():
    data = pd.read_csv("movies.csv")
    moviesID = data['movieId']
    titles = data['title']
    tags_raw = data['genres']
    tags = []
    movie_ID = []
    for row in tags_raw:
        row = row.split('|')
        tags.append(row)
    movie_info = {}
    for i in range(len(moviesID)):
        item = [moviesID[i], titles[i], tags[i]]
        movie_info[i] = item
        movie_ID.append(int(moviesID[i]))
    return movie_info, movie_ID


def TF_IDF(movie_info):
    tags_list = []
    for i, item in movie_info.items():
        for tag in item[2]:
            if tag not in tags_list:
                tags_list.append(tag)
    movie_num = len(movie_info)
    tag_num = len(tags_list)
    tf_matrix = np.zeros([movie_num, tag_num])
    idf_matrix = np.zeros([movie_num, tag_num])
    tf_idf = np.zeros([movie_num, tag_num])
    a = 0
    for i, item in movie_info.items():
        for tag in item[2]:
            b = tags_list.index(tag)
            tf_matrix[a, b] = 1
            idf_matrix[a, b] = 1
        a = a + 1
    for j in range(movie_num):
        sum_of_row = sum(tf_matrix[j, :])
        for k in range(tag_num):
            if tf_matrix[j, k]:
                tf_matrix[j, k] = tf_matrix[j, k] / sum_of_row  # 计算TF（词频）矩阵。词频=词在文件中出现次数/文件中词总数
    for j in range(tag_num):
        sum_of_col = sum(idf_matrix[:, j])
        for k in range(movie_num):
            if idf_matrix[k, j]:  # 计算IDF（反文档频率）。IDF=log(文档总数/包含词的文档总数+1)
                idf_matrix[k, j] = math.log(movie_num / (sum_of_col + 1))  # 其中+1是为了防止分母为0
    for k in range(movie_num):
        for j in range(tag_num):
            tf_idf[k, j] = idf_matrix[k, j] * tf_matrix[k, j]  # 计算TF-IDF值，即TD*IDF
    return tf_idf


def recommendation(user_rate, user_id, movie_ID, cos_sim, user_movie):  # 求出每一部电影的预期评分并进行排序
    recommend_list = []
    recommend_dict = {}
    user_rated = user_rate[user_id]
    user_rated_num = len(user_rated)
    movie_num = len(movie_ID)
    for i in range(movie_num):
        if (movie_ID[i]) not in user_movie[user_id]:
            sum1 = 0
            sum2 = 0
            sum3 = 0
            for rated_movie in user_rated:
                row = movie_ID.index(rated_movie[0])
                if cos_sim[row, i] > 0:
                    if movie_ID[i] in user_rated:
                        continue
                    else:
                        sum1 += cos_sim[row, i] * rated_movie[1]
                        sum2 += cos_sim[row, i]
                        sum3 += rated_movie[1]
                else:
                    continue
            if sum2 == 0:
                pre_score = sum3 / user_rated_num  # 若分母为0，取已打分电影的平均值
            else:
                pre_score = sum1 / sum2  # 代入公式计算预期评分
            recommend_list.append([pre_score, i])
            recommend_dict[movie_ID[i]] = pre_score
    recommend_list.sort(reverse=True)
    return recommend_list, recommend_dict


def predict_score(user_rate, user_id, movie_ID, cos_sim, movieid):
    user_rated = user_rate[user_id]  # 预测评分与推荐类似，但只需计算指定电影即可，以免进行无用的计算
    user_rated_num = len(user_rated)
    column = movie_ID.index(movieid)
    sum1 = 0
    sum2 = 0
    sum3 = 0
    for rated_movie in user_rated:
        row = movie_ID.index(rated_movie[0])
        if cos_sim[row, column] > 0:
            if movie_ID[column] in user_rated:
                continue
            else:
                sum1 += cos_sim[row, column] * rated_movie[1]
                sum2 += cos_sim[row, column]
                sum3 += rated_movie[1]
        else:
            continue
    if sum2 == 0:
        pre_score = sum3 / user_rated_num
    else:
        pre_score = sum1 / sum2
    return pre_score



if __name__ == "__main__":
    r = get_rating()
    user_rate, user_movie = get_user(r)
    movie_info, movie_ID = get_movie_info()
    tf_idf = TF_IDF(movie_info)
    cos_sim = cosine_similarity(tf_idf)
    user_id = int(input('请输入被推荐者的ID(0表示运行测试集)：'))
    if user_id != 0:
        n = int(input('请输入推荐电影个数:'))
        recommend_list, recommend_dict = recommendation(user_rate, user_id, movie_ID, cos_sim, user_movie)
        print("{0:6}\t{1:6}\t{2:65}\t{3}".format('电影ID', '预期评分', '电影名', '电影标签'))
        for i in range(n):
            j = recommend_list[i][1]
            print('{0:6}\t{1:.6f}\t{2:65}\t{3}'.format(movie_info[j][0], recommend_list[i][0], movie_info[j][1],
                                                       movie_info[j][2]))
    else:
        test_data = pd.read_csv("test_set.csv")
        usersid = test_data['userId']
        moviesid = test_data['movieId']
        rating = test_data['rating']
        m = len(usersid)
        sse = 0
        print('{0:4}\t{1:6}\t{2:6}\t{3:6}'.format('用户ID', '电影ID', '预期评分', '实际评分'))
        for i in range(m):
            pre_score = predict_score(user_rate, usersid[i], movie_ID, cos_sim, moviesid[i])
            print('{0:4}\t{1:<6}\t{2:.6f}\t{3:.6f}'.format(usersid[i], moviesid[i], pre_score, rating[i]))
            sse += (pre_score - rating[i]) ** 2
        print("SSE=", sse)
